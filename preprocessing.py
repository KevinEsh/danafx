from pandas import DataFrame, Series
from numpy import ndarray, linspace, newaxis
from sklearn.datasets import make_regression
from utils import HL2, HLC3, RSISmoothIndicator, CCISmoothIndicator, WaveTrendIndicator, \
    ADXSmoothIndicator, get_signal_labels


def preprocess_stock_data(
    stock_data: DataFrame,
    add_indicators: dict[str, str],
    rescaled: bool = True,
    fillna: bool = False,
) -> ndarray:
    stock_data["index"] = range(0, len(stock_data))
    stock_data["hlc3"] = HLC3(stock_data.high, stock_data.low, stock_data.close)
    stock_data["rsi14"] = RSISmoothIndicator(stock_data.close, fillna=False)
    stock_data["rsi9"] = RSISmoothIndicator(stock_data.close, 9, fillna=False)
    stock_data["cci"] = CCISmoothIndicator(stock_data.high, stock_data.low, stock_data.close, fillna=False)
    stock_data["wt"] = WaveTrendIndicator(stock_data.hlc3, fillna=False)
    stock_data["adx"] = ADXSmoothIndicator(stock_data.high, stock_data.low, stock_data.close, fillna=False)
    # stock_data["ground_signal"] = get_signal_labels(stock_data["close"], -4)

    # stock_data.dropna(axis=0, inplace=True)
    data = stock_data[add_indicators].values.reshape(-1, len(add_indicators))
    # target = stock_data["ground_signal"].values

    return data  # , target


def get_dummy_data():
    # Generate some random data
    X, y = make_regression(n_samples=70, n_features=1, noise=10, random_state=0)
    # Predict the target variable at some new inputs
    X_new = linspace(-2, 2, 100)[:, newaxis]
    return X, y, X_new


def get_dummy_classification_data():

    X = DataFrame({'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                   'feature2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
                   'feature3': [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]})

    y = Series([0, 0, 0, 0, -1, -1, -1, -1, 1, 1, 1])

    # make some predictions on new data
    X_new = DataFrame({'feature1': [6, 7, 8, 1],
                       'feature2': [12, 14, 16, 3],
                       'feature3': [15, 17, 19, 100]})

    return X, y, X_new
