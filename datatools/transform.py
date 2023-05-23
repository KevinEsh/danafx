from talib import EMA, SMA
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler, MinMaxScaler, FunctionTransformer
from sklearn.base import BaseEstimator, TransformerMixin


def range_scale(X, feature_range: tuple[int, int] = (0, 100)):
    return (X - feature_range[0]) / (feature_range[1] - feature_range[0])


def smooth(X, window: int, method: str = "SMA"):
    if window < 1:
        raise ValueError(f"{window=} should be greater than 0")
    if window == 1:
        return X
    elif method == "SMA":
        return SMA(X, window)
    elif method == "EMA":
        # TODO: min_bars = get_stable_min_bars("EMA", window_smooth)
        # EMA.set
        return EMA(X, window)


def get_smoother(
    method: str,
    **kwargs: int,
):
    if method == "EMA":
        return FunctionTransformer(EMA, kw_args=kwargs)
    elif method == "SMA":
        return FunctionTransformer(SMA, kw_args=kwargs)
    elif method == "savitz":
        return FunctionTransformer(savgol_filter, kw_args=kwargs)


def get_scaler(
    method: str,
    **kwargs
):
    if method == "range_scale":
        return FunctionTransformer(range_scale, kw_args=kwargs)
    elif method == "minmax_scale":
        return MinMaxScaler(**kwargs)
    elif method == "standard_scale":
        return StandardScaler(**kwargs)


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
