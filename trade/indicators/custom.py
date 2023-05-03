import numpy as np
from talib import MAX, MIN, EMA, SMA

from trade.metadata import CandleLike
from preputils.clean import copy_format, asrecarray


def HL2(
    high: CandleLike,
    low: CandleLike,
    keep_format: bool = False
) -> CandleLike:
    """
    Calculates the HL2 (high plus low divided by 2) for the given high and low candle-like data.

    Args:
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        keep_format (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: The calculated HL2 values.
    """
    hl2 = (high + low) / 2.
    if keep_format:
        hl2 = copy_format(hl2, high, name="hl2")
    return hl2


def HLC3(
    high: CandleLike,
    low: CandleLike,
    close: CandleLike,
    keep_format: bool = False,
) -> CandleLike:
    """
    Calculates the HLC3 (high plus low plus close divided by 3) for the given high, low and close candle-like data.

    Args:
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        close (CandleLike): The close values of the candles.
        keep_format (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: The calculated HL2 values.
    """
    hlc3 = (high + low + close) / 3.
    if keep_format:
        hlc3 = copy_format(hlc3, high, name="hlc3")
    return hlc3


def OHLC4(
    open: CandleLike,
    high: CandleLike,
    low: CandleLike,
    close: CandleLike,
) -> CandleLike:
    """
    Calculates the HLC3 (open plus high plus low plus close divided by 4) for the
    given open, high, low and close candle-like data.

    Args:
        open (CandleLike): The open values of the candles.
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        close (CandleLike): The close values of the candles.
        keep_format (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: The calculated HL2 values.
    """
    ohlc4 = (open + high + low + close) / 4.
    return ohlc4


def PIVOTHIGH(
    high: CandleLike,
    left: int,
    right: int,
    as_recarray: bool = False
) -> np.ndarray:
    """
    Calculates the pivot highs in an array of high values using the left and right periods.

    Args:
        high (CandleLike): Array of high values.
        left (int): Number of periods to look back for pivot high.
        right (int): Number of periods to look forward for pivot high.

    Returns:
        np.ndarray: Array of pivot high values with NaN values for non-pivot highs.
    """
    pivots = np.roll(MAX(high, left + 1 + right), -right)
    pivots[pivots != high] = np.NaN
    if as_recarray:
        pivots = asrecarray(pivots, names=[f"pivothigh{left}_{right}"])
    return pivots

def PIVOTLOW(low: np.ndarray, left: int, right: int) -> np.ndarray:
    """
    Calculates the pivot lows in an array of low values using the left and right periods.

    Args:
        low (np.ndarray): Array of low values.
        left (int): Number of periods to look back for pivot low.
        right (int): Number of periods to look forward for pivot low.

    Returns:
        np.ndarray: Array of pivot low values with NaN values for non-pivot lows.
    """
    pivots = np.roll(MIN(low, left + 1 + right), -right)
    pivots[pivots != low] = np.NaN
    return pivots


def DONCHAIN(
    ohlc: CandleLike,
    window: int = 20,
    keep_format: bool = False,
) -> tuple[CandleLike, CandleLike]:
    """
    Calculates the Donchian Channel for the given candle-like data.

    Args:
        ohlc (CandleLike): The candle-like data to calculate the Donchian Channel from.
        window (int, optional): The lookback window size to use when calculating the Donchian Channel. Defaults to 20.
        keep_format (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        tuple[CandleLike, CandleLike]: A tuple of two CandleLike, representing the upper and lower bounds of the Donchian Channel, respectively.
    """
    upper = MAX(ohlc, window)
    lower = MIN(ohlc, window)
    if keep_format:
        upper = copy_format(upper, ohlc, f"donchain_up_{window}")
        lower = copy_format(lower, ohlc, f"donchain_low_{window}")
    # donchain = np.rec.fromarrays(
    #     [upper, lower],
    #     names=["donchain_upper", "donchain_lower"],
    #     formats=["<f8", "<f8"]
    # )
    return upper, lower


def WT(
    high: CandleLike,
    low: CandleLike,
    close: CandleLike,
    window: int = 10,
    window_smooth: int = 11,
    keep_format: bool = False,
) -> CandleLike:
    """
    Calculates the WaveTrend Classic indicator for the given candle-like data.
    The WaveTrend Classic indicator is a momentum oscillator that combines a moving average (MA)
    with a cycle wave (CW) to identify overbought and oversold conditions.
    The MA is typically an exponential moving average (EMA), while the CW is a sine wave
    that oscillates between zero and one.

    Args:
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        close (CandleLike): The close values of the candles.
        window (int, optional): lookback window used in EMA indicator. Defaults to 10.
        window_smooth (int, optional): lookback window to smooth the indicator. Defaults to 11.

    Returns:
        CandleLike: The WaveTrend Classic indicator as a candle-like data object.
    """
    hlc3 = HLC3(high, low, close)
    ema = EMA(hlc3, window)
    delta_ema = EMA(np.abs(hlc3 - ema), window)
    ci = (hlc3 - ema) / (0.015 * delta_ema)
    tci = EMA(ci, window_smooth)
    wt = SMA(tci, 4)

    if keep_format:
        wt = copy_format(wt, high, f"wt_{window}")
    return wt


def RQK(
    close: CandleLike,
    window: float = 8,
    alpha: float = 1,
    keep_format: bool = False,
) -> CandleLike:
    """
    Computes the rolling Rational Quadratic Kernel (RQK) for a given time series of closing prices.

    Args:
        close (CandleLike): The closing prices of the time series.
        window (float, optional): The rolling window size used to compute the kernel. Defaults to 8.
        alpha (float, optional): A parameter that controls the decay rate of the weights. Defaults to 1.
        keep_format (bool, optional): Whether to return the output in the same format as the input. Defaults to False.

    Returns:
        CandleLike: The rolling Rational Quadratic Kernel of the closing prices.
    """
    size = close.size
    weights = (1. + 0.5 * np.arange(size) ** 2. /
               (alpha * (window ** 2.))) ** (-alpha)
    cum_weights = weights.cumsum()
    c = close.values[::-1]
    rq = np.empty(size)

    for i in range(size):
        j = size - i
        rq[j - 1] = (c[i:] @ weights[:j]) / cum_weights[j-1]
    if keep_format:
        rq = copy_format(rq, close, f"rqk_{window}")
    return rq


def RBFK(
    close: CandleLike,
    window: float = 16,
    keep_format: bool = False,
) -> CandleLike:
    """
    Computes the Radial Basis Function kernel on a time series of close prices.

    Args:
        close (CandleLike): The closing prices of the time series.
        window (float, optional): The lookback window parameter of the kernel. Defaults to 16.
        keep_format (bool, optional): If True, returns the output with the same format as the input. Defaults to False.

    Returns:
        CandleLike: The RBF kernel values of the time series.
    """
    n = close.size
    weights = np.exp(-0.5 * np.arange(n) ** 2 / (window ** 2))
    cum_weights = weights.cumsum()
    c = close.values[::-1]
    rbfk = np.empty(n)

    for i in range(n):
        j = n - i
        rbfk[j-1] = (c[i:] @ weights[:j]) / cum_weights[j-1]

    if keep_format:
        rbfk = copy_format(rbfk, close, f"rbfk_{window}")

    return rbfk
