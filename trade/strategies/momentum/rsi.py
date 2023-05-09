from numpy import recarray, append

from trade.strategies.abstract import Hyperparameter, TradingStrategy, OHLCbounds
from trade.indicators import RSI, get_stable_min_bars

# Stream indicators. Only returns last value
# from talib.stream import RSI as _RSI


# class TriggerBandMechanism():

#     def __init__(self, bands: list[tuple], signals: tuple[int]) -> None:
#         self.n_bands = len(bands)
#         self.bands = bands
#         self.signals = signals
#         self.was_on_band = [False for _ in range(self.n_bands)]

#     def __call__(self, value: float) -> bool:
#         for i in range(self.n_bands):
#             if is_on_band(value, self.bands[i]):
#                 if not self.was_on_band[i]:
#                     self.was_on_band[i] = True
#             elif self.was_on_band[i]:
#                 self.was_on_band[i] = False
#                 return self.signals[i]
#         return -1  # Neutral signal until value is out of any band


def is_on_band(value: float, band: tuple[float]):
    return band[0] <= value <= band[1]


class RsiStrategy(TradingStrategy):
    config_window = Hyperparameter("window", "numeric", (2, 1000))
    config_buy_band = Hyperparameter("buy_band", "interval", (0, 100))
    config_sell_band = Hyperparameter("sell_band", "interval", (0, 100))
    config_source = Hyperparameter("source", "categoric", OHLCbounds)
    config_lookback = Hyperparameter("lookback", "numeric", (-1, 0))
    config_mode = Hyperparameter(
        "mode", "categoric", ("inband", "outband", "onband"))

    def __init__(
        self,
        window: int,
        buy_band: tuple[float],
        sell_band: tuple[float],
        source: str = "close",
        lookback: int = 0,
        mode: str = "outband",
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window._check_bounds(window, init=True)
        self.config_buy_band._check_bounds(buy_band, init=True)
        self.config_sell_band._check_bounds(sell_band, init=True)
        self.config_source._check_bounds(source, init=True)
        self.config_lookback._check_bounds(lookback, init=True)
        self.config_mode._check_bounds(mode, init=True)

        # fill user values
        self._window = window
        self._buy_band = buy_band
        self._sell_band = sell_band
        self._lookback = lookback
        self._source = source
        self._mode = mode

        # calcualte an estimate of bars needed to get a good rsi approximation
        self.min_bars = get_stable_min_bars("RSI", window) + lookback

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
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self.config_mode._check_bounds(mode)
        self._mode = mode

    def fit(self, train_data: recarray, train_labels: recarray = None):
        if not self.compound_mode:
            super().fit(train_data, train_labels)
        # Select optimal batch
        self._batch = self.train_data[self._source][-self.min_bars:]

    def update_data(self, new_data: recarray) -> None:
        if not self.compound_mode:
            super().update_data(new_data)
        # Select optimal batch
        self._batch = self.train_data[self._source][-self.min_bars:]

    def generate_entry_signal(self, candle: recarray) -> int:
        # Calculate RSI for current candle
        batch = append(self._batch, candle.close)
        rsis = RSI(batch, self._window)
        rsi = rsis[-1+self._lookback]

        if self._mode == "outband":
            prev_rsi = rsis[-2+self._lookback]
            print(f"{prev_rsi=:.2f} {rsi=:.2f}")
            if is_on_band(prev_rsi, self._buy_band) and not is_on_band(rsi, self._buy_band):
                return 0  # buy
            elif is_on_band(prev_rsi, self._sell_band) and not is_on_band(rsi, self._sell_band):
                return 1  # sell
            else:
                return -1  # neutral

        elif self._mode == "inband":
            prev_rsi = rsis[-2+self._lookback]
            # print(f"{prev_rsi=:.2f} {rsi=:.2f}")
            if not is_on_band(prev_rsi, self._buy_band) and is_on_band(rsi, self._buy_band):
                return 0  # buy
            elif not is_on_band(prev_rsi, self._sell_band) and is_on_band(rsi, self._sell_band):
                return 1  # sell
            else:
                return -1  # neutral

        elif self._mode == "onband":
            # Return signal only if last rsi touches sell/buy bands
            if is_on_band(rsi, self._buy_band):
                return 0  # buy
            elif is_on_band(rsi, self._sell_band):
                return 1  # sell
            else:
                return -1  # neutral
