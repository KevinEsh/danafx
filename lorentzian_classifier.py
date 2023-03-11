from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import numpy as np
from enum import Enum
from typing import Any


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

    def __init__(
        self,
        n_neighbors: int = 4,
        lookback_window: int = 2000,
        neighbors_leap: int = 4,
        n_jobs: int = 1
    ) -> None:
        # define the number of neighbors to use
        self._n_neighbors = n_neighbors
        self._lookback_window = lookback_window
        self._neighbors_leap = neighbors_leap
        self._n_jobs = n_jobs

        # create the KNN classifier using the Lorentzian distance metric
        self.knn_classifier = KNeighborsClassifier(
            n_neighbors=self._n_neighbors,
            n_jobs=self._n_jobs,
            metric=self._modif_lorentzian_distance,
            weights=self._distance_weights
            # metric_params={"lookback_window": 2000},
        )

    def fit(self, train_data: Any, train_target: Any) -> None:
        # fit the model
        self._train_data = train_data
        self._train_target = train_target
        self.knn_classifier.fit(self._train_data, self._train_target)

    def predict(self, data: Any) -> Any:
        return self.knn_classifier.predict(data)

    def _modif_lorentzian_distance(self, x1: np.ndarray, x2: np.ndarray) -> float:
        i1, i2 = x1[0], x2[0]  # get the chronological index of both points
        is_not_in_window = (i1 < i2) and (i1 <= i2 + self._lookback_window)
        # TODO: cambiar esta cosa por 4 velas atras de i2 (experimentar)
        skip_neighbor = not (i1 - i2) % self._neighbors_leap
        if skip_neighbor or is_not_in_window:
            return np.inf
        return np.sum(np.log(1 + np.abs(x1[1:] - x2[1:])))

    def _distance_weights(self, distances: np.ndarray) -> np.ndarray:
        # convert inf distance to 0, they will be disregarded
        is_inf = np.isinf(distances)
        distances[is_inf] = 0
        # normalize weigths using their distance. Further points will have less impact
        return distances / np.sum(distances, axis=1, keepdims=True)


X = pd.DataFrame({'feature1': [1, 2, 3, 4, 5],
                  'feature2': [2, 4, 6, 8, 10],
                 'feature3': [5, 7, 9, 11, 13]})

y = pd.Series([0, 0, 0, -1, -1])


# make some predictions on new data
X_new = pd.DataFrame({'feature1': [6, 7, 8, 1],
                      'feature2': [12, 14, 16, 3],
                     'feature3': [15, 17, 19, 100]})


print(y_pred)
