
# TODO: mejorar estas estrategias en backtesting phase
from talib import SMA, EMA


def ema_trend(close: Series, ema: Series) -> Series:
    return close > ema


def sma_trend(close: Series, sma: Series) -> Series:
    return close > sma


def get_signal_labels(source: Series, window: int = -4) -> Series:
    shifted = source.shift(window)  # move the window to the future
    shifted[window:] = source[window:]  # fill nan values with their present
    # 1 if current price is lower than future
    uptrend = (shifted > source).astype(float)
    # -1 if current price is greater than future
    downtrend = (shifted < source).astype(float)
    return uptrend - downtrend
