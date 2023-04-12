
import numpy as np
from pandas import Series
from ta.trend import EMAIndicator, SMAIndicator, ADXIndicator, CCIIndicator
from ta.momentum import RSIIndicator
from sklearn.preprocessing import minmax_scale


def get_lorentzian_distance(x1: np.ndarray, x2: np.ndarray) -> float:
    return np.sum(np.log(1 + np.abs(x1 - x2)))


def WaveTrendIndicator(
        hlc3: Series,
        window_ema: int = 10,
        window_smooth: int = 11,
        rescaled: bool = True,
        fillna: bool = False,
) -> Series:
    """Returns the normalized WaveTrend Classic series ideal for use in ML algorithms.

    Args:
        hlc3 (Series): Average of High, Low, Close
        window_ema (int, optional): lookback window used in EMA indicator. Defaults to 10.
        window_smooth (int, optional): lookback window to smooth the indicator. Defaults to 21.
        rescaled (bool, optional): rescale data to [0,1] range. Defaults to True.
        fillna (bool, optional): fill empty values. Defaults to True.

    Returns:
        Series: WT Indicator series
    """
    ema = EMAIndicator(hlc3, window_ema, fillna).ema_indicator()
    diff_ema = EMAIndicator(np.abs(hlc3 - ema), window_ema, fillna).ema_indicator()
    ci = (hlc3 - ema) / (0.015 * diff_ema)
    tci = EMAIndicator(ci, window_smooth, fillna).ema_indicator()
    wt = SMAIndicator(tci, 4, fillna).sma_indicator()
    if rescaled:  # rescale it to [0,1] range
        return minmax_scale(wt, copy=False)
    return wt


def RSISmoothIndicator(
        close: Series,
        window_rsi: int = 14,
        window_smooth: int = 1,
        rescaled: bool = True,
        fillna: bool = False
) -> Series:
    """Return the normilized smoothed RSI series

    Args:
        close (Series): Close stock price series
        window_rsi (int, optional): Lookback window used in RSI. Defaults to 14.
        window_smooth (int, optional): lookback window to smooth the indicator. Defaults to 1.
        rescaled (bool, optional): _description_. Defaults to True.
        fillna (bool, optional): _description_. Defaults to False.

    Returns:
        Series: _description_
    """
    rsi = RSIIndicator(close, window_rsi, fillna).rsi()
    # smooth with EMA
    rsismooth = EMAIndicator(rsi, window_smooth, fillna).ema_indicator()
    if rescaled:  # rescaled it to [0,1] range
        return rsismooth / 100.
    return rsismooth


def CCISmoothIndicator(
        high: Series,
        low: Series,
        close: Series,
        window_cci: int = 20,
        window_smooth: int = 1,
        rescaled: bool = True,
        fillna: bool = False
) -> Series:
    cci = CCIIndicator(high, low, close, window_cci, 0.015, fillna).cci()
    # smooth with EMA
    ccismooth = EMAIndicator(cci, window_smooth, fillna).ema_indicator()
    if rescaled:  # rescale it to [0,1] range
        return minmax_scale(ccismooth, copy=False)
    return ccismooth


def ADXSmoothIndicator(
        high: Series,
        low: Series,
        close: Series,
        window_adx: int = 20,
        rescaled: bool = True,
        fillna: bool = False
) -> Series:
    adx = ADXIndicator(high, low, close, window_adx, fillna).adx()
    if rescaled:
        return adx / 100.
    return adx


def RQKernelIndicator(
        close: Series,
        window: float = 8,
        alpha: float = 1,
) -> Series:
    size = close.size
    weights = (1. + 0.5 * np.arange(size) ** 2 /
               (alpha * (window ** 2.))) ** (-alpha)
    cum_weights = weights.cumsum()
    c = close.values[::-1]
    rq = np.empty(size)

    for i in range(size):
        j = size - i
        rq[j - 1] = (c[i:] @ weights[:j]) / cum_weights[j-1]

    return rq


def RBFKernelIndicator(
        close: Series,
        window: float = 16
) -> Series:
    size = close.size
    weights = np.exp(-0.5 * np.arange(size) ** 2 / (window ** 2))
    cum_weights = weights.cumsum()
    c = close.values[::-1]
    rq = np.empty(size)

    for i in range(size):
        j = size - i
        rq[j-1] = (c[i:] @ weights[:j]) / cum_weights[j-1]

    return rq


def HL2(high: Series, low: Series) -> Series:
    return (high + low) / 2.


def HLC3(high: Series, low: Series, close: Series) -> Series:
    return (high + low + close) / 3.


def OHLC4(open: Series, high: Series, low: Series, close: Series) -> Series:
    return (open + high + low + close) / 4.


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


if __name__ == "__main__":
    from trade.broker import BrokerSession
    from matplotlib.pyplot import plot, savefig
    from setup import get_settings

    # Import project settings
    login_settings = get_settings("settings/demo/login.json")
    # trading_settings = get_settings("settings/demo/trading.json")
    mt5_login_settings = login_settings["mt5_login"]

    trader = BrokerSession()
    trader.start_session(mt5_login_settings)
    trader.initialize_symbols(["EURUSD"])
    df = trader.query_historic_data("EURUSD", "M30", 2000)
    # df["hlc3"] = HLC3(df.high, df.low, df.close)
    # df["rsi"] = RSISmoothIndicator(df.close, fillna=False)
    # df["cci"] = CCISmoothIndicator(df.high, df.low, df.close, fillna=False)
    # df["wt"] = WaveTrendIndicator(df.hlc3, fillna=False)
    # df["adx"] = ADXSmoothIndicator(df.high, df.low, df.close, fillna=False)

    df["rq"] = RQKernelIndicator(df.close)
    df["rbf"] = RBFKernelIndicator(df.close)

    print(df[["close", "rbf", "rq"]])

    # plot(df[["rsi", "cci", "wt", "adx"]])
    plot(df[["close", "rbf", "rq"]].tail(100))
    savefig("test3.jpeg")
