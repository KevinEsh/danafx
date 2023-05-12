from sklearn.preprocessing import minmax_scale
from talib import EMA, SMA

from trade.metadata import CandleLike

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.signal import savgol_filter
import numpy as np
from trade.strategies.abstract import Hyperparameter
# Define a custom transformer to apply a Savitzky-Golay filter to the data
class RangeScaler(BaseEstimator, TransformerMixin):
    config_feature_range = Hyperparameter("feature_range", "interval", (-1000, 1000))
    # config_window = Hyperparameter("window", "numeric", (1, 100))

    def __init__(self, feature_range: tuple[int, int] = (0, 100), copy: bool = False):
        self.config_feature_range._check_bounds(feature_range, init=True)

        self.feature_range = feature_range
        self.copy = copy
        
    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return (X - self.feature_range[0]) / (self.feature_range[1] - self.feature_range[0])
        # return savgol_filter(X, self.window_length, self.polyorder, axis=0)

class Smoother(BaseEstimator, TransformerMixin):
    config_window = Hyperparameter("window", "numeric", (1, 100))
    config_method = Hyperparameter("method", "categoric", ["EMA", "SMA"])

    def __init__(self, window: int, method: str = "EMA", copy: bool = False):
        # Check if hyperparameters met the criteria
        self.config_window._check_bounds(window, init=True)
        self.config_method._check_bounds(method, init=True)

        self.window = window
        self.method = method
        self.copy = copy
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        if self.window == 1:
            return X
        elif self.method == "SMA":
            return SMA(X, self.window)
        elif self.method == "EMA":
            # TODO: min_bars = get_stable_min_bars("EMA", window_smooth)
            # EMA.set
            return EMA(X, self.window)

# Define a custom transformer to apply a Savitzky-Golay filter to the data
class SavitzkyGolayFilter(BaseEstimator, TransformerMixin):
    def __init__(self, window=5, polyorder=2):
        self.window = window
        self.polyorder = polyorder
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        return savgol_filter(X, self.window, self.polyorder, axis=0)


def normalize(
    data: CandleLike,
    xrange: tuple[float, float] = (0, 1),
    method: str = "minmax_scale"
) -> CandleLike:
    if method == "range_scale":
        return (data - xrange[0]) / (xrange[1] - xrange[0])
    elif method == "minmax_scale":
        return minmax_scale(data, xrange, copy=False)


def smooth(
    data: CandleLike,
    window_smooth: int = 2,
    method: str = "EMA",
) -> CandleLike:
    if window_smooth < 1:
        raise ValueError(f"{window_smooth=} should be greater than 0")
    elif window_smooth == 1:
        return data
    elif method == "SMA":
        return SMA(data, window_smooth)
    elif method == "EMA":
        # TODO: min_bars = get_stable_min_bars("EMA", window_smooth)
        # EMA.set
        return EMA(data, window_smooth)
