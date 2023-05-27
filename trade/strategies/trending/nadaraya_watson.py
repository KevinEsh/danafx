from numpy import ndarray
from datatools.custom import addpop, get_recarray
from datatools.technical import crossingover, crossingunder

from trade.metadata import CandleLike, EntrySignal
from trade.indicators import RBFK, RQK, get_stable_min_bars
from trade.strategies.abstract import Hyperparameter, TradingStrategy


class DualNadarayaKernelStrategy(TradingStrategy):
    config_window_rqk = Hyperparameter("window_rqk", "numeric", (3, 1000))
    config_window_rbfk = Hyperparameter("window_rbfk", "numeric", (3, 1000))
    config_alpha_rq = Hyperparameter("alpha_rq", "numeric", (0, 1e6))
    config_n_bars = Hyperparameter("n_bars", "numeric", (2, 5000))
    config_lag = Hyperparameter("lag", "numeric", (0, 2))
    config_neutral_band = Hyperparameter(
        "neutral_band", "interval", (-1000, 1000))

    def __init__(
        self,
        window_rqk: int = 8,
        window_rbfk: int = 8,
        alpha_rq: float = 1,
        n_bars: int = 25,
        lag: int = 0,
        neutral_band: tuple = (0, 0),
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window_rqk._check_bounds(window_rqk, init=True)
        self.config_window_rbfk._check_bounds(window_rbfk, init=True)
        self.config_alpha_rq._check_bounds(alpha_rq, init=True)
        self.config_n_bars._check_bounds(n_bars, init=True)
        self.config_lag._check_bounds(lag, init=True)
        self.config_neutral_band._check_bounds(neutral_band, init=True)

        self._window_rqk = window_rqk
        self._window_rbfk = window_rbfk
        self._alpha_rq = alpha_rq
        self._n_bars = n_bars
        self._lag = lag
        self._neutral_band = neutral_band

        # self._rqk_bars = get_stable_min_bars("RQK")
        # self._rbfk_bars = get_stable_min_bars("RBFK")
        # self.min_bars = max(self._rqk_bars, self._rbfk_bars) + lag

        self._rqk_bars = n_bars
        self._rbfk_bars = n_bars
        self.min_bars = n_bars + lag

    @property
    def window_rqk(self):
        return self._window_rqk

    @window_rqk.setter
    def window_rqk(self, window_rqk):
        self.config_window_rqk._check_bounds(window_rqk)
        self._window_rqk = window_rqk

    @property
    def window_rbfk(self):
        return self._window_rbfk

    @window_rbfk.setter
    def window_rbfk(self, window_rbfk):
        self.config_window_rbfk._check_bounds(window_rbfk)
        self._window_rbfk = window_rbfk

    @property
    def alpha_rq(self):
        return self._alpha_rq

    @alpha_rq.setter
    def alpha_rq(self, alpha_rq):
        self.config_alpha_rq._check_bounds(alpha_rq)
        self._alpha_rq = alpha_rq

    @property
    def n_bars(self):
        return self._n_bars

    @n_bars.setter
    def n_bars(self, n_bars):
        self.config_n_bars._check_bounds(n_bars)
        self._n_bars = n_bars

    @property
    def lag(self):
        return self._lag

    @lag.setter
    def lag(self, lag):
        self.config_lag._check_bounds(lag)
        self._lag = lag

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
        if not self.compound_mode:
            super().fit(train_data, train_labels)

        # Precalculate RQK & RBFK. This will save computational time
        self._rqk_queue = RQK(train_data.close, self._window_rqk, self._alpha_rq,
                              self._rqk_bars, dropna=True)
        self._rbfk_queue = RBFK(train_data.close, (self._window_rbfk - self._lag),
                                self._rbfk_bars, dropna=True)

        # print(self._rqk_queue)
        # print(self._rbfk_queue)

        # Save minimal batch to compute indicator with current candle
        self._batch_rqk = self.train_data[-self._rqk_bars:]
        self._batch_rbfk = self.train_data[-self._rbfk_bars:]

        # signals = self.batch_signals()
        # print(signals)

    def update_data(self, new_candles: CandleLike) -> None:
        if not self.is_new_data(new_candles):
            return

        if not self.compound_mode:
            super().update_data(new_candles)

        # Update minimal batch
        self._batch_rqk = self.train_data[-self._rqk_bars:]
        self._batch_rbfk = self.train_data[-self._rbfk_bars:]

        # Then calculate new indicator values
        new_rqk = RQK(self._batch_rqk.close, self._window_rqk, self._alpha_rq,
                      self._rqk_bars, dropna=True)
        new_rbfk = RBFK(self._batch_rbfk.close, (self._window_rbfk - self._lag),
                        self._rbfk_bars, dropna=True)

        # Finally add them to the queue
        self._rqk_queue = addpop(self._rqk_queue, new_rqk)
        self._rbfk_queue = addpop(self._rbfk_queue, new_rbfk)
        # print(self._rqk_queue)
        # print(self._rbfk_queue)

    def generate_entry_signal(self, candle: CandleLike) -> int:
        # If lag = 0 that means we need to calculate indicators with current candle
        if self._lag == 0:
            batch_rqk = addpop(self._batch_rqk.close, candle.close)  # TODO: achis? esto borra datos del batch?
            batch_rbfk = addpop(self._batch_rbfk.close, candle.close)

            # Calculate indicator for current candle
            rqk = RQK(batch_rqk, self._window_rqk, self._alpha_rq,
                      self._rqk_bars)[-1]
            rbfk = RBFK(batch_rbfk, (self._window_rbfk - self._lag),
                        self._rqk_bars)[-1]

            line_rqk = [self._rqk_queue[-1], rqk]
            line_rbfk = [self._rbfk_queue[-1], rbfk]
        # else use cache stored values to make signal
        else:
            line_rqk = self._rqk_queue[-2-self._lag:]
            line_rbfk = self._rbfk_queue[-2-self._lag:]

        # print(
        #     f"[{line_rqk[0]=:.5f}, {line_rqk[1]=:.5f}][{line_rbfk[0]=:.5f}, {line_rbfk[1]=:.5f}]")

        # Detect tendency and return signal
        if crossingover(line_rbfk, line_rqk, self._neutral_band[1])[-1]:
            return EntrySignal.BUY
        elif crossingunder(line_rbfk, line_rqk, self._neutral_band[0])[-1]:
            return EntrySignal.SELL
        else:
            return EntrySignal.NEUTRAL

    def batch_signals(self):
        # Precalculate RQK & RBFK. This will save computational time
        rqks = RQK(self.train_data.close, self._window_rqk, self._alpha_rq,
                   self._rqk_bars)
        rbfks = RBFK(self.train_data.close, (self._window_rbfk - self._lag),
                     self._rbfk_bars)

        buy_signals = crossingover(rqks, rbfks, self.neutral_band[1])
        sell_signals = crossingunder(rqks, rbfks, self.neutral_band[0])

        return get_recarray([buy_signals, sell_signals], names=["buy", "sell"])
