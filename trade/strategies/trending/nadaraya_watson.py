from numpy import ndarray
from trade.metadata import CandleLike
from trade.indicators.custom import RBFK, RQK
from trade.strategies.abstract import Hyperparameter, TradingStrategy


class DualNadarayaKernelStrategy(TradingStrategy):
    config_window_rq = Hyperparameter("window_rq", "numeric", (2, 1000))
    config_window_rbf = Hyperparameter("window_rbf", "numeric", (2, 1000))
    config_alpha_rq = Hyperparameter("alpha_rq", "numeric", (2, 1000))
    config_neutral_band = Hyperparameter(
        "neutral_band", "interval", (-1000, 1000))

    def __init__(
        self,
        window_rq: int,
        window_rbf: int,
        alpha_rq: float,
        neutral_band: tuple = (0, 0),
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window_rq._check_bounds(window_rq, init=True)
        self.config_window_rbf._check_bounds(window_rbf, init=True)
        self.config_alpha_rq._check_bounds(alpha_rq, init=True)
        self.config_neutral_band._check_bounds(neutral_band, init=True)

        self._window_rq = window_rq
        self._window_rbf = window_rbf
        self.alpha_rq = alpha_rq
        self._neutral_band = neutral_band

    @property
    def window_rq(self):
        return self._window_rq

    @window_rq.setter
    def window_rq(self, window_rq):
        self.config_window_rq._check_bounds(window_rq)
        self._window_rq = window_rq

    @property
    def window_rbf(self):
        return self._window_rbf

    @window_rbf.setter
    def window_rbf(self, window_rbf):
        self.config_window_rbf._check_bounds(window_rbf)
        self._window_rbf = window_rbf

    @property
    def alpha_rq(self):
        return self._alpha_rq

    @alpha_rq.setter
    def alpha_rq(self, alpha_rq):
        self.config_alpha_rq._check_bounds(alpha_rq)
        self._alpha_rq = alpha_rq

    @property
    def neutral_band(self):
        return self._neutral_band

    @neutral_band.setter
    def neutral_band(self, neutral_band):
        self.config_neutral_band._check_bounds(neutral_band)
        self._neutral_band = neutral_band

    def fit(
        self,
        train_data: CandleLike,
        train_labels: ndarray = None
    ) -> None:
        super().fit(train_data, train_labels)

        # Precalculate MAVs. This will save a lot of computational time
        self._rbfk_values = RBFK(train_data.close, self._window_rbf)
        self._rqk_values = RQK(
            train_data.close, self._window_rq, self.alpha_rq)
        self._batch = train_data[-self.min_bars:]
        return

    def update_data(self, new_data: CandleLike) -> None:
        if not self.is_new_data(new_data):
            return

        # calculate window from old data to delete
        size = new_data.size
        s1 = 1 - self.window_rq
        s2 = s1 + size
        l1 = 1 - self.window_rbf
        l2 = l1 + size

        # if some new data has came up, just remove oldest contribution and add new one
        new_mav = new_data.close.sum()
        self._cached_mav_short += new_mav - self.train_data.close[s1:s2].sum()
        self._cached_mav_long += new_mav - self.train_data.close[l1:l2].sum()

        # Then replace oldest data
        # TODO Aqui va a haber un pedo cuando se actualicen con strategias compuestas
        return super().update_data(new_data)

    def generate_entry_signal(self, datum: CandleLike) -> int:
        # Calculate short and long moving averages
        mav_short = (self._cached_mav_short + datum.close) / self.window_rq
        mav_long = (self._cached_mav_long + datum.close) / self.window_rbf

        print(f"{mav_short=:.6f} {mav_long=:.6f}")

        # Detect tendency and return signal
        if mav_short > mav_long + self._neutral_band[1]:
            return 0  # buy
        elif mav_short < mav_long + self._neutral_band[0]:
            return 1  # sell
        else:
            return -1  # neutral
