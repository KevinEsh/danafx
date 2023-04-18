from trade.strategies.abstract import Hyperparameter, TradingStrategy, OHLCbounds
from numpy import recarray, append

from talib import RSI

# Stream indicators. Only returns last value
# from talib.stream import RSI as _RSI


class TriggerBandMechanism():

    def __init__(self, bands: list[tuple], signals: tuple[int]) -> None:
        self.n_bands = len(bands)
        self.bands = bands
        self.signals = signals
        self.was_on_band = [False for _ in range(self.n_bands)]

    def __call__(self, value: float) -> bool:
        for i in range(self.n_bands):
            if is_on_band(value, self.bands[i]):
                if not self.was_on_band[i]:
                    self.was_on_band[i] = True
            elif self.was_on_band[i]:
                self.was_on_band[i] = False
                return self.signals[i]
        return -1  # Neutral signal until value is out of any band


def is_on_band(value: float, band: tuple[float]):
    return band[0] <= value <= band[1]


class RsiStrategy(TradingStrategy):
    config_window = Hyperparameter("window", "numeric", (2, 1000))
    config_buy_band = Hyperparameter("buy_band", "interval", (0, 100))
    config_sell_band = Hyperparameter("sell_band", "interval", (0, 100))
    config_source = Hyperparameter("source", "categoric", OHLCbounds)
    config_lookback = Hyperparameter("lookback", "numeric", (-1, 0))
    config_hold_mode = Hyperparameter("source", "boolean")

    def __init__(
        self,
        window: int,
        buy_band: tuple[float],
        sell_band: tuple[float],
        source: str = "close",
        lookback: int = 0,
        hold_mode: bool = False,
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window._check_bounds(window, init=True)
        self.config_buy_band._check_bounds(buy_band, init=True)
        self.config_sell_band._check_bounds(sell_band, init=True)
        self.config_source._check_bounds(source, init=True)
        self.config_lookback._check_bounds(lookback, init=True)
        self.config_hold_mode._check_bounds(hold_mode, init=True)

        # fill user values
        self._window = window
        self._buy_band = buy_band
        self._sell_band = sell_band
        self._lookback = lookback
        self._source = source
        self._hold_mode = hold_mode

        # calcualte an estimate of bars needed to get a good rsi approximation
        self.min_bars = int(7.4 * window)  # based on experiments
        # self._band_trigger = TriggerBandMechanism([buy_band, sell_band], (0, 1))

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, window):
        self.config_window._check_bounds(window)
        self._window = window

    @property
    def buy_band(self):
        return self._buy_band

    @buy_band.setter
    def buy_band(self, buy_band):
        self.config_buy_band._check_bounds(buy_band)
        self._buy_band = buy_band

    @property
    def sell_band(self):
        return self._sell_band

    @sell_band.setter
    def sell_band(self, sell_band):
        self.config_sell_band._check_bounds(sell_band)
        self._sell_band = sell_band

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        self.config_source._check_bounds(source)
        self._source = source

    @property
    def hold_mode(self):
        return self._hold_mode

    @hold_mode.setter
    def hold_mode(self, hold_mode):
        self.config_hold_mode._check_bounds(hold_mode)
        self._hold_mode = hold_mode

    def fit(self, train_data: recarray):
        super().fit(train_data)
        self._last_bars = self.train_data[self._source][-self.min_bars:]

    def update_data(self, new_data: recarray) -> None:
        super().update_data(new_data)
        self._last_bars = self.train_data[self._source][-self.min_bars:]

    def generate_entry_signal(self, datum: recarray) -> int:
        # Calculate RSI for current candle
        batch = append(self._last_bars, datum.close)
        rsis = RSI(batch, self._window)
        print(f"{rsis[-2]=:.2f} {rsis[-1]=:.2f}")
        print(self._last_bars.size)

        if self._hold_mode:
            prev_rsi, rsi = rsis[-2+self._lookback:self._lookback]
            if is_on_band(prev_rsi, self._buy_band) and not is_on_band(rsi, self._buy_band):
                return 0
            elif is_on_band(prev_rsi, self._sell_band) and not is_on_band(rsi, self._sell_band):
                return 1
            else:
                return -1
            # if self._was_on_buy_band and not is_on_band(rsi, self._buy_band):
            #     self._was_on_buy_band = False
            #     return 0  # buy
            # elif self._on_sell_band and not is_on_band(rsi, self._sell_band):
            #     self._on_sell_band = False
            #     return 1  # sell
            # elif is_on_band(rsi, self._buy_band):
            #     self._was_on_buy_band = True
            #     return -1  # not buy until rsi is out of buy_band
            # elif is_on_band(rsi, self._sell_band):
            #     self._was_on_sell_band = True
            #     return -1  # not buy until rsi is out of sell_band
            # else:
            #     return -1  # neutral
        else:
            # Return signal only if last rsi touches sell/buy bands
            rsi = rsis[-1+self._lookback]
            if is_on_band(rsi, self._buy_band):
                return 0  # buy
            elif is_on_band(rsi, self._sell_band):
                return 1  # sell
            else:
                return -1  # neutral
