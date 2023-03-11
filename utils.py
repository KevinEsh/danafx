
import numpy as np
from pandas import Series
from ta.trend import EMAIndicator, SMAIndicator


def get_lorentzian_distance(x1: np.ndarray, x2: np.ndarray) -> float:
    return np.sum(np.log(1 + np.abs(x1 - x2)))


def WaveTrendIndicator(hlc3: Series, window: int = 10, avg_window: int = 21) -> Series:
    # study(title="WaveTrend [LazyBear]", shorttitle="WT_LB")

    # n1 = input(10, "Channel Length")
    # n2 = input(21, "Average Length")
    # obLevel1 = input(60, "Over Bought Level 1")
    # obLevel2 = input(53, "Over Bought Level 2")
    # osLevel1 = input(-60, "Over Sold Level 1")
    # osLevel2 = input(-53, "Over Sold Level 2")

    ema = EMAIndicator(hlc3, window)
    avg_ema = EMAIndicator(abs(hlc3 - ema), avg_window)
    ci = (hlc3 - ema) / (0.015 * avg_ema)
    tci = ema(ci, avg_window)
    wt1 = tci
    return SMAIndicator(tci, 4)


def HL2(high: Series, low: Series) -> Series:
    return (high + low) / 2


def HLC3(high: Series, low: Series, close: Series) -> Series:
    return (high + low + close) / 3


def OHLC4(open: Series, high: Series, low: Series, close: Series) -> Series:
    return (open + high + low + close) / 4


def ema_trend(close: Series, ema: Series) -> Series:
    return close > ema


def sma_trend(close: Series, sma: Series) -> Series:
    return close > sma


def get_signal_labels(source: Series, window: int = -4) -> Series:
    shifted = source.shift(window)  # move the window to the future
    shifted[window:] = source[window:]  # fill nan values with their present
    uptrend = (shifted > source).astype(float)  # 1 if current price is lower than future
    downtrend = (shifted < source).astype(float)  # -1 if current price is greater than future
    return uptrend - downtrend
