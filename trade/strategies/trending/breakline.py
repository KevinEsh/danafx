from numpy import recarray, append, nanargmax, arange, isnan, all as npall

from trade.metadata import CandleLike
from trade.strategies.abstract import Hyperparameter, TradingStrategy
from trade.indicators import ATR_, SMA_, STDDEV_, VAR_
from trade.indicators import PIVOTHIGH, PIVOTLOW

# Stream indicators. Only returns last value


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

def is_crossingover(candle: CandleLike, value: float) -> bool:
    return candle.open < value < candle.close 

def get_last_nonnan_index(data: recarray) -> float:
    if npall(isnan(data)):
        return None
    return data.shape[0] - nanargmax(data)

def calculate_slope(
    data: CandleLike,
    bar_index: int, 
    window: int,
    alpha:float,
    method: str
) -> float:
    s = data.shape[0]
    slice_data = data[s - bar_index - window: s - bar_index + 1]

    h = slice_data.high
    l = slice_data.low
    c = slice_data.close

    if method == "atr":
        return ATR_(h, l, c, window) / (window * alpha)
    elif method == "stdev":
        return STDDEV_(c, window) / (window * alpha)
    elif method == "linreg":
        bar_indexes = arange(window)
        return 2 * alpha * abs( (SMA_(c[-window:] * bar_indexes, window) - SMA_(c[-window:], window) * SMA_(bar_indexes, window)) / VAR_(bar_indexes, window) )


class TrendlineBreakStrategy(TradingStrategy):
    config_window = Hyperparameter("window", "numeric", (1, 1000))
    config_alpha = Hyperparameter("alpha", "numeric", (1e-5, 1e5))
    config_offset = Hyperparameter("offset", "numeric", (-2, 0))
    # config_source = Hyperparameter("source", "categoric", OHLCbounds)
    config_method = Hyperparameter("method", "categoric", ("atr", "stdev", "linreg"))

    def __init__(
        self,
        window: int,
        alpha: float,
        offset: int = 0,
        # source: str = "close",
        method: str = "stdev",
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window._check_bounds(window, init=True)
        self.config_alpha._check_bounds(alpha, init=True)
        self.config_offset._check_bounds(offset, init=True)
        self.config_method._check_bounds(method, init=True)

        # fill user values
        self._window = window
        self._alpha = alpha
        self._offset = offset
        self._method = method

        # Estimate of bars needed to get a good approximation for pivots
        self.min_bars = 2 * window + 1

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, window):
        self.config_window._check_bounds(window)
        self._window = window

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self.config_alpha._check_bounds(alpha)
        self._alpha = alpha

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        self.config_offset._check_bounds(offset)
        self._offset = offset

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, method):
        self.config_method._check_bounds(method)
        self._method = method

    def fit(self, train_data: recarray, train_labels: recarray = None):
        if not self.compound_mode:
            super().fit(train_data, train_labels)

        # Get all high & low pivots from the whole timeseries
        high_pivots = PIVOTHIGH(self.train_data.high, self._window, self._window)
        low_pivots = PIVOTLOW(self.train_data.low, self._window, self._window)

        # Just take into account the last pivots. Those will make the prediction
        self._hp_index = get_last_nonnan_index(high_pivots)
        self._lp_index = get_last_nonnan_index(low_pivots)

        self._hp_value = high_pivots[-self._hp_index] if self._hp_index != None else None
        self._lp_value = low_pivots[-self._lp_index] if self._lp_index != None else None

        # Calculate slope accourding to method selected by user
        self._hp_slope = calculate_slope(self.train_data, self._hp_index,
                                         self._window, self._alpha, self._method)
        self._lp_slope = calculate_slope(self.train_data, self._lp_index,
                                         self._window, self._alpha, self._method)

    def update_data(self, new_data: recarray) -> None:
        if not self.compound_mode:
            super().update_data(new_data)
        # Select minimal batch for predictions
        self._batch = self.train_data[-self.min_bars:]
        
        # Get all high & low pivots from the whole timeseries
        high_pivots = PIVOTHIGH(self._batch.high, self._window, self._window)
        low_pivots = PIVOTLOW(self._batch.low, self._window, self._window)

        # Just take into account the last pivots. Those will make the prediction
        new_hp_index = get_last_nonnan_index(high_pivots)
        new_lp_index = get_last_nonnan_index(low_pivots)

        # if there is not a new high pivot, just increment x-axis projection
        if new_hp_index is None:
            self._hp_index += 1
        else:
            print(new_lp_index, self._window)
            self._hp_index = new_hp_index
            self._hp_value = high_pivots[-self._hp_index]
            self._hp_slope = calculate_slope(self._batch, self._hp_index,
                                    self._window, self._alpha, self._method)

        # if there is not a new low pivot, just increment x-axis projection
        if new_lp_index is None:
            self._lp_index += 1
        else:
            print(new_lp_index, self._window)
            self._lp_index = new_lp_index
            self._lp_value = high_pivots[-self._lp_index]
            self._hp_slope = calculate_slope(self._batch, self._hp_index,
                                    self._window, self._alpha, self._method)

    def generate_entry_signal(self, candle: recarray) -> int:
        candles = append(self._batch, candle)

        # calculate line projection to current candle
        buy_line = self._hp_value - self._hp_index * self._hp_slope
        sell_line = self._last_lp + self._lp_index * self._lp_slope

        if is_crossingover(candles, buy_line):
            return 0 # buy
        elif is_crossingover(candles, sell_line):
            return 1 # sell
        return -1 # netral
