from pandas import DataFrame, Series
from sklearn.datasets import make_regression
from numpy import ndarray, linspace, newaxis


def get_dummy_data():
    # Generate some random data
    X, y = make_regression(n_samples=70, n_features=1,
                           noise=10, random_state=0)
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
