from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator, CCIIndicator
from enum import Enum


class TradeSignal(Enum):
    BUY = 1
    NEUTRAL = 0
    SELL = -1


class LorentzianClassifier:
    """This model specializes specifically in predicting the direction of price
    action over the course of the next 4 bars. To avoid complications with the
    ML model, this value is hardcoded to 4 bars but support for other training
    lengths may be added in the future.
    """
    pass


def get_modif_lorentzian_distance(x1: np.ndarray, x2: np.ndarray, lookback_window: float = 2000) -> float:
    i1, i2 = x1[0], x2[0]  # get the chronological index of both points
    is_not_in_window = (i1 < i2) and (i1 <= i2 + lookback_window)
    is_not_module = not (i2 - lookback_window) % 4  # TODO: cambiar esta cosa por 4 velas atras de i2 (experimentar)
    if is_not_module or is_not_in_window:
        return np.inf
    return np.sum(np.log(1 + np.abs(x1[1:] - x2[1:])))


def normalized_weights(distances: np.ndarray) -> np.ndarray:
    # convert inf distance to 0, they don't have any importance
    is_inf = np.isinf(distances)
    distances[is_inf] = 0
    # normalize weigths using their distance. Further points will have greater importance
    return distances / np.sum(distances, axis=1, keepdims=True)


X = pd.DataFrame({'feature1': [1, 2, 3, 4, 5],
                  'feature2': [2, 4, 6, 8, 10],
                 'feature3': [5, 7, 9, 11, 13]})

y = pd.Series([0, 0, 0, -1, -1])

RSIIndicator(X["feature1"])


# define the number of neighbors to use
n_neighbors = 2

# create the KNN classifier using the Lorentzian distance metric
knn = KNeighborsClassifier(
    n_neighbors=n_neighbors,
    n_jobs=2,
    metric_params={"lookback_window": 2},
    metric=get_modif_lorentzian_distance,
    weights=normalized_weights
)

# fit the model
knn.fit(X, y)

# make some predictions on new data
X_new = pd.DataFrame({'feature1': [6, 7, 8, 1],
                      'feature2': [12, 14, 16, 3],
                     'feature3': [15, 17, 19, 100]})

y_pred = knn.predict(X_new)

print(y_pred)
