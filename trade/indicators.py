
import numpy as np
from typing import Union
from pandas import Series

from sklearn.preprocessing import minmax_scale

from talib.abstract import Function
from talib import EMA, SMA, CCI, ADX, RSI
from talib import get_functions, set_unstable_period

__unstable_indicators__ = [
    'HT_DCPERIOD',
    'HT_DCPHASE',
    'HT_PHASOR',
    'HT_SINE',
    'HT_TRENDMODE',
    'ADX',
    'ADXR',
    'CMO',
    'DX',
    'MFI',
    'MINUS_DI',
    'MINUS_DM',
    'PLUS_DI',
    'PLUS_DM',
    'RSI',
    'STOCHRSI',
    'EMA',
    'HT_TRENDLINE',
    'KAMA',
    'MAMA',
    'T3',
    'ATR',
    'NATR',
    "WT",
    "RQK",
    "RBFK",
]

__linear_indicators__ = [
    'MAX',
    'MIN',
    'MINMAX',
    'BBANDS',
    'DEMA',
    'EMA',
    'HT_TRENDLINE',
    'KAMA',
    'MA',
    'MAMA',
    'MAVP',
    'MIDPOINT',
    'MIDPRICE',
    'SAR',
    'SAREXT',
    'SMA',
    'T3',
    'TEMA',
    'TRIMA',
    'WMA',
    'AVGPRICE',
    'MEDPRICE',
    'TYPPRICE',
    'WCLPRICE',
    'LINEARREG',
    'LINEARREG_INTERCEPT',
    'TSF',
    "HL2",
    "HLC3",
    "OHLC4",
]

__new_indicators__ = [
    "HL2",
    "HLC3",
    "OHLC4",
    "WT",
    "RQK",
    "RBFK"
]


def get_all_indicators():
    talib_indicators = get_functions()
    talib_indicators.extend(__new_indicators__)
    return talib_indicators


def get_talib_linear_indicators():
    linear_indicators = []
    for ind_name in get_all_indicators():
        flags = Function(ind_name).function_flags
        if flags is not None and 'Output scale same as input' in flags:
            linear_indicators.append(ind_name)
    return linear_indicators


def get_talib_unstable_indicators():
    unstable_indicators = []
    for ind_name in get_all_indicators():
        flags = Function(ind_name).function_flags
        if flags is not None and 'Function has an unstable period' in flags:
            unstable_indicators.append(ind_name)
    return unstable_indicators


def test_indicator(indicator: str, wrange=(2, 100), n_tests=2000, max_bars=2000):
    def run_test(window: int, error_tolerance: float = 0.0001):
        # fake if highly volatile price data
        close = np.random.rand(max_bars) * 50
        high = close + np.random.rand(max_bars) * 5
        low = close - np.random.rand(max_bars) * 5
        real_val = Function(indicator)(high, window)[-1]
        for i in range(2 * window + 12, max_bars):
            stream_val = Function(indicator)(high[-i:], window)[-1]
            # or convert to str and chop at desired accuracy
            if abs(real_val - stream_val) < error_tolerance:
                return i
        return None

    avg_stable_windows = []
    for w in range(*wrange):
        print(w)
        tests = Series([run_test(w) for i in range(n_tests)])
        avg_stable_windows.append(tests.median())
    return Series(avg_stable_windows, index=range(*wrange))


def calculate_formula(a):
    mini = 1e10
    v = None
    f = None
    # print(avg_stable_windows)
    # avg_stable_windows.plot()
    x = a.index.values
    for e in np.arange(1, 4, 0.001):
        y = a.values ** e
        fit = np.polyfit(x, y, 1)
        r = ((fit[0] * x + fit[1])**(1/e) -
             a.values).astype(int)
    #     print(e, r)
        error = abs(np.mean(np.abs(r)))
        # print(error)
        if 0 <= error < mini and (np.all(np.abs(r[:1]) < 1)):
            print(e, abs(np.mean(np.abs(r))))
            mini = error
            v = e
            f = fit
    print(v, f, mini)
    print(((f[0] * x + f[1])**(1/v) - a.values).astype(int))
    return f, v


def get_lorentzian_distance(x1: np.ndarray, x2: np.ndarray) -> float:
    return np.sum(np.log(1 + np.abs(x1 - x2)))


def normalize(
    data: Union[Series, np.recarray],
    xrange: tuple[float, float] = (0, 1),
    method: str = "minmax_scale"
) -> Union[Series, np.recarray]:
    if method == "range_scale":
        return (data - xrange[0]) / (xrange[1] - xrange[0])
    elif method == "minmax_scale":
        return minmax_scale(data, xrange, copy=False)


def smooth(
    data: Union[Series, np.recarray],
    window_smooth: int = 2,
    method: str = "EMA",
) -> Union[Series, np.recarray]:
    if window_smooth < 1:
        raise ValueError(f"{window_smooth=} should be greater than 0")
    elif window_smooth == 1:
        return data
    elif method == "SMA":
        return SMA(data, window_smooth)
    elif method == "EMA":
        min_bars = get_stable_min_bars("EMA", window_smooth)
        # EMA.set
        return EMA(data, window_smooth)


def get_min_bars(indicator: str, window: int) -> int:
    """Calculate the minimal amount of bars to get at least one value from that indicator

    Args:
        indicator (str): Indicator name. Call `get_all_indicators` to see complete list
        window (int): Number of bar were the function is applied sequentialy

    Returns:
        int: minimum amount of bar that the indicator needs
    """
    if indicator not in get_all_indicators():
        ValueError(f"{indicator=} does not exist")

    # Indicator is stable. Window is enough for calculate precise values
    if indicator not in __unstable_indicators__:
        if indicator == "WT":
            return 2 * window + 12
        return window
    else:
        return 1


def get_stable_min_bars(indicator: str, window: int) -> int:
    if indicator not in get_all_indicators():
        ValueError(f"{indicator=} does not exist")

    # Indicator is stable. Window is enough for calculate precise values
    if indicator not in __unstable_indicators__:
        return window
    # Calculate the min amount of bars to get a good aproximation i.e. <1e-4 error
    elif indicator == "RSI":
        return int((100. * window - 120.) ** (1./1.479))
    elif indicator == "EMA":
        return int((11.24 * window + 7.26) ** (1./1.2))
    elif indicator == "ADX":
        return int((138.2 * window - 155.55) ** (1./1.53))
    elif indicator == "WT":
        if 2 <= window <= 14:
            return int(2.36 * window + 61.51)
        else:
            return int((12.85 * window + 19.95) ** (1/1.173))
    else:
        NotImplementedError(
            f"{indicator=} has no formula to get stable values")


def HL2(high: Series, low: Series) -> Series:
    return (high + low) / 2.


def HLC3(high: Series, low: Series, close: Series) -> Series:
    return (high + low + close) / 3.


def OHLC4(open: Series, high: Series, low: Series, close: Series) -> Series:
    return (open + high + low + close) / 4.


def WT(
    high: Union[Series, np.recarray],
    low: Union[Series, np.recarray],
    close: Union[Series, np.recarray],
    window: int = 10,
    window_smooth: int = 11,
) -> Series:
    """Returns the WaveTrend Classic indicator ideal for use in ML algorithms.

    Args:
        hlc3 (Series): Average of High, Low, Close
        window (int, optional): lookback window used in EMA indicator. Defaults to 10.
        window_smooth (int, optional): lookback window to smooth the indicator. Defaults to 21.
        rescaled (bool, optional): rescale data to [0,1] range. Defaults to True.
        fillna (bool, optional): fill empty values. Defaults to True.

    Returns:
        Series: WT Indicator series
    """
    hlc3 = HLC3(high, low, close)
    ema = EMA(hlc3, window)
    delta_ema = EMA(np.abs(hlc3 - ema), window)
    ci = (hlc3 - ema) / (0.015 * delta_ema)
    tci = EMA(ci, window_smooth)
    wt = SMA(tci, 4)
    return wt


def RQK(
    close: Series,
    window: float = 8,
    alpha: float = 1,
) -> Series:
    size = close.size
    weights = (1. + 0.5 * np.arange(size) ** 2. /
               (alpha * (window ** 2.))) ** (-alpha)
    cum_weights = weights.cumsum()
    c = close.values[::-1]
    rq = np.empty(size)

    for i in range(size):
        j = size - i
        rq[j - 1] = (c[i:] @ weights[:j]) / cum_weights[j-1]

    return rq


def RBFK(
        close: Series,
        window: float = 16
) -> Series:
    n = close.size
    weights = np.exp(-0.5 * np.arange(n) ** 2 / (window ** 2))
    cum_weights = weights.cumsum()
    c = close.values[::-1]
    rq = np.empty(n)

    for i in range(n):
        j = n - i
        rq[j-1] = (c[i:] @ weights[:j]) / cum_weights[j-1]

    return rq


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

    df["rqk"] = RQK(df.close)
    df["rbfk"] = RBFK(df.close)

    print(df[["close", "rbf", "rq"]])

    # plot(df[["rsi", "cci", "wt", "adx"]])
    plot(df[["close", "rbf", "rq"]].tail(100))
    savefig("test3.jpeg")
