
import numpy as np
from pandas import Series
from basic import get_all_indicators
from talib.abstract import Function


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
