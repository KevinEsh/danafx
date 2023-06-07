import numpy as np
from talib import MAX, MIN, EMA, SMA

from trade.metadata import CandleLike
from datatools.custom import get_recarray, rolling_apply, drop_na


def OC2(
    open: CandleLike,
    close: CandleLike,
    asrecarray: bool = False
) -> CandleLike:
    """
    Calculates the HL2 (high plus low divided by 2) for the given high and low candle-like data.

    Args:
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        asrecarray (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: The calculated HL2 values.
    """
    oc2 = (open + close) / 2.

    if asrecarray:
        oc2 = get_recarray([oc2], names="oc2", formats="<f8")
    return oc2

def HL2(
    high: CandleLike,
    low: CandleLike,
    asrecarray: bool = False
) -> CandleLike:
    """
    Calculates the HL2 (high plus low divided by 2) for the given high and low candle-like data.

    Args:
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        asrecarray (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: The calculated HL2 values.
    """
    hl2 = (high + low) / 2.

    if asrecarray:
        hl2 = get_recarray([hl2], names="hl2", formats="<f8")
    return hl2


def HLC3(
    high: CandleLike,
    low: CandleLike,
    close: CandleLike,
    asrecarray: bool = False,
) -> CandleLike:
    """
    Calculates the HLC3 (high plus low plus close divided by 3) for the given high, low and close candle-like data.

    Args:
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        close (CandleLike): The close values of the candles.
        asrecarray (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: The calculated HL2 values.
    """
    hlc3 = (high + low + close) / 3.

    if asrecarray:
        hlc3 = get_recarray([hlc3], names="hlc3", formats="<f8")
    return hlc3


def OHLC4(
    open: CandleLike,
    high: CandleLike,
    low: CandleLike,
    close: CandleLike,
    asrecarray: bool = False,
) -> CandleLike:
    """
    Calculates the HLC3 (open plus high plus low plus close divided by 4) for the
    given open, high, low and close candle-like data.

    Args:
        open (CandleLike): The open values of the candles.
        high (CandleLike): The high values of the candles.
        low (CandleLike): The low values of the candles.
        close (CandleLike): The close values of the candles.
        asrecarray (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: The calculated HL2 values.
    """
    ohlc4 = (open + high + low + close) / 4.
    if asrecarray:
        ohlc4 = get_recarray([ohlc4], names="ohlc4", formats="<f8")
    return ohlc4

def HEIKINASHI(
    open: CandleLike,
    high: CandleLike,
    low: CandleLike,
    close: CandleLike,
    asrecarray: bool = False,
) -> CandleLike:
    """
    Computes the Heikin Ashi representation of a given set of open, high, low, and close prices.
    
    Args:
        open (np.array): Array of open prices.
        high (np.array): Array of high prices.
        low (np.array): Array of low prices.
        close (np.array): Array of close prices.
        asrecarray (bool): If True, returns the result as a NumPy record array (recarray).
                           If False, returns the result as a standard NumPy array.

    Returns:
        np.array or np.recarray: The Heikin Ashi representation of the input prices. The structure
                                 of the output (i.e., whether it's a standard array or recarray) 
                                 is determined by the `asrecarray` argument.
    """
    # Compute the Heikin Ashi close price
    ha_close = OHLC4(open, high, low, close)

    # Initialize a new array for the Heikin Ashi open prices
    ha_open = np.zeros_like(open)

    # Set the first Heikin Ashi open price to be the same as the original first open price
    ha_open[0] = open[0]

    # Loop through the rest of the array to calculate each Heikin Ashi open price
    for i in range(1, len(open)):
        ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2
    
    if asrecarray:
        # Convert the Heikin Ashi open and close prices, as well as the original high and low prices,
        # into a NumPy record array
        ha = get_recarray(
            [ha_open, high, low, ha_close], 
            names=["open", "high", "low", "close"], 
            formats=["<f8","<f8","<f8","<f8"])
    else:
        # Use column_stack to reshape the data to (n, 4)
        ha = np.column_stack((ha_open, high, low, ha_close))

    return ha

def PIVOTHIGH(
    high: CandleLike,
    left: int,
    right: int,
    asrecarray: bool = False
) -> CandleLike:
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

    if asrecarray:
        pivots = get_recarray(
            [pivots],
            names=f"pivothigh{left}{right}",
            formats="<f8")
    return pivots


def PIVOTLOW(
    low: np.ndarray,
    left: int,
    right: int,
    asrecarray: bool = False,
) -> np.ndarray:
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

    if asrecarray:
        pivots = get_recarray(
            [pivots],
            names=f"pivotlow{left}{right}",
            formats="<f8")
    return pivots


def DONCHAIN(
    ohlc: CandleLike,
    window: int = 20,
    asrecarray: bool = False,
) -> CandleLike:
    """
    Calculates the Donchian Channel for the given candle-like data.

    Args:
        ohlc (CandleLike): The candle-like data to calculate the Donchian Channel from.
        window (int, optional): The lookback window size to use when calculating the Donchian Channel. Defaults to 20.
        asrecarray (bool): If True, the output will have the same format as the input (i.e. same type and attributes).

    Returns:
        CandleLike: array of the upper and lower bounds of the Donchian Channel, respectively.
    """
    upper = MAX(ohlc, window)
    lower = MIN(ohlc, window)

    if asrecarray:
        donchain = get_recarray(
            [upper, lower],
            names=[f"donup{window}", f"donlow{window}"],
            formats=["<f8", "<f8"])
    else:
        donchain = np.array([upper, lower])
    return donchain


def WT(
    high: CandleLike,
    low: CandleLike,
    close: CandleLike,
    window: int = 10,
    window_smooth: int = 11,
    asrecarray: bool = False,
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

    if asrecarray:
        wt = get_recarray([wt], names=f"wt{window}", formats="<f8")
    return wt


def RQK(
    close: CandleLike,
    window: float = 8,
    alpha: float = 1,
    n_bars: int = None,
    n_jobs: int = 1,
    asrecarray: bool = False,
    dropna: bool = False,
) -> CandleLike:
    """
    Computes the rolling Rational Quadratic Kernel (RQK) for a given time series of closing prices.

    Args:
        close (CandleLike): The closing prices of the time series.
        window (float, optional): The rolling window size used to compute the kernel. Defaults to 8.
        alpha (float, optional): A parameter that controls the decay rate of the weights. Defaults to 1.
        asrecarray (bool, optional): Whether to return the output in the same format as the input. Defaults to False.

    Returns:
        CandleLike: The rolling Rational Quadratic Kernel of the closing prices.
    """
    if not n_bars:
        n_bars = close.shape[0]

    bars = (np.arange(n_bars) ** 2.)[::-1]
    weights = (1. + 0.5 * bars / (alpha * window ** 2.)) ** (-alpha)

    rq = rolling_apply(lambda y: (y @ weights), n_bars, close, n_jobs=n_jobs)
    rq /= weights.sum()

    if dropna:
        rq = drop_na(rq)

    if asrecarray:
        rq = get_recarray(rq, names=f"rqk{window}", formats="<f8")

    return rq


def RBFK(
    close: CandleLike,
    window: float = 16,
    n_bars: int = None,
    n_jobs: int = 1,
    asrecarray: bool = False,
    dropna: bool = False,
) -> CandleLike:
    """
    Computes the Radial Basis Function kernel on a time series of close prices.

    Args:
        close (CandleLike): The closing prices of the time series.
        window (float, optional): The lookback window parameter of the kernel. Defaults to 16.
        asrecarray (bool, optional): If True, returns the output with the same format as the input. Defaults to False.

    Returns:
        CandleLike: The RBF kernel values of the time series.
    """
    if not n_bars:
        n_bars = close.shape[0]

    bars = (np.arange(n_bars) ** 2.)[::-1]
    weights = np.exp(-0.5 * bars / (window ** 2))

    rbfk = rolling_apply(lambda y: (y @ weights), n_bars, close, n_jobs=n_jobs)
    rbfk /= weights.sum()

    if dropna:
        rbfk = drop_na(rbfk)

    if asrecarray:
        rbfk = get_recarray(rbfk, names=f"rbfk{window}", formats="<f8")

    return rbfk
