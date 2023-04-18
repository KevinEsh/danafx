from trade.strategies.abstract import Hyperparameter, TradingStrategy
from numpy import recarray


class DualMavStrategy(TradingStrategy):
    config_short_window = Hyperparameter("short_window", "numeric", (2, 1000))
    config_long_window = Hyperparameter("long_window", "numeric", (2, 1000))
    config_neutral_band = Hyperparameter("neutral_band", "interval", (-1000, 1000))

    def __init__(
        self,
        short_window: int,
        long_window: int,
        neutral_band: tuple = (0, 0),
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_short_window._check_bounds(short_window, init=True)
        self.config_long_window._check_bounds(long_window, init=True)
        self.config_neutral_band._check_bounds(neutral_band, init=True)

        self._short_window = short_window
        self._long_window = long_window
        self._neutral_band = neutral_band

    @property
    def short_window(self):
        return self._short_window

    @short_window.setter
    def short_window(self, short_window):
        self.config_short_window._check_bounds(short_window)
        self._short_window = short_window

    @property
    def long_window(self):
        return self._long_window

    @long_window.setter
    def long_window(self, long_window):
        self.config_long_window._check_bounds(long_window)
        self._long_window = long_window

    @property
    def neutral_band(self):
        return self._neutral_band

    @neutral_band.setter
    def neutral_band(self, neutral_band):
        self.config_neutral_band._check_bounds(neutral_band)
        self._neutral_band = neutral_band

    def fit(self, train_data: recarray) -> None:
        # Precalculate MAVs. This will save a lot of computational time
        super().fit(train_data)
        self._cached_mav_short = self.train_data.close[(1 - self.short_window):].sum()
        self._cached_mav_long = self.train_data.close[(1 - self.long_window):].sum()
        return

    def update_data(self, new_data: recarray) -> None:
        if not self.is_new_data(new_data):
            return

        # calculate window from old data to delete
        size = new_data.size
        s1 = 1 - self.short_window
        s2 = s1 + size
        l1 = 1 - self.long_window
        l2 = l1 + size

        # if some new data has came up, just remove oldest contribution and add new one
        new_mav = new_data.close.sum()
        self._cached_mav_short += new_mav - self.train_data.close[s1:s2].sum()
        self._cached_mav_long += new_mav - self.train_data.close[l1:l2].sum()

        # Then replace oldest data
        return super().update_data(new_data)  # TODO Aqui va a haber un pedo cuando se actualicen con strategias compuestas

    def generate_entry_signal(self, datum: recarray) -> int:
        # Calculate short and long moving averages
        mav_short = (self._cached_mav_short + datum.close) / self.short_window
        mav_long = (self._cached_mav_long + datum.close) / self.long_window

        print(f"{mav_short=:.6f} {mav_long=:.6f}")

        # Detect tendency and return signal
        if mav_short > mav_long + self._neutral_band[1]:
            return 0  # buy
        elif mav_short < mav_long + self._neutral_band[0]:
            return 1  # sell
        else:
            return -1  # neutral
