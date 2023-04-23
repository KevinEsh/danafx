from sklearn.preprocessing import minmax_scale
from talib import EMA, SMA

from trade.indicators2.metadata import CandleLike


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
