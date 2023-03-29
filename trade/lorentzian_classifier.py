from sklearn.neighbors import KNeighborsClassifier
import numpy as np
from enum import Enum
from typing import Any


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
            weights=self._distance_weights,
            # metric_params={"lookback_window": 2000},
        )

    def fit(self, train_data: Any, train_target: Any) -> None:
        # fit the model
        self._train_data = train_data
        self._train_target = train_target
        # self.knn_classifier.fit(self._train_data, self._train_target)

    def predict(self, data: Any) -> Any:
        return self.knn_classifier.predict(data)

    def predict2(self, data: Any) -> Any:
        predictions = np.full(data.shape[0], 0)
        for x1 in data:
            i1 = x1[0]  # chronologycal index
            is_past = self._train_data[:, 0] < i1
            only_leap = ~((self._train_data[:, 0] - i1) % self._neighbors_leap)
            x2s = self._train_data[is_past & only_leap]
            distances = self._lorentzian_distance(x1, x2s)
            neighbor_count = 0
            largest_distance = -1
            for i, d in enumerate(distances):
                if largest_distance

    def update(self, new_data: Any) -> None:
        # TODO: modificar esta funcion para poder actualizar los datos de entrenamiento cada cierto tiempo/iteraciones
        raise NotImplemented

    def _lorentzian_distance(self, x1: np.ndarray, x2s: np.ndarray) -> np.ndarray:
        return np.sum(np.log(1 + np.abs(x2s[:, 1:] - x1[1:])), axis=1)

    def _modif_lorentzian_distance(self, x1: np.ndarray, x2: np.ndarray) -> float:
        i1, i2 = x1[0], x2[0]  # get the chronological index of both points
        is_not_in_window = (i1 <= i2) or (i1 > i2 + self._lookback_window)
        # TODO: cambiar esta cosa por 4 velas atras de i2 (experimentar)
        skip_neighbor = i1 % self._neighbors_leap  # (i1 - i2) % self._neighbors_leap
        if skip_neighbor or is_not_in_window:
            # print(i1, i2, np.inf)
            return np.inf
        # print(i1, i2, np.sum(np.log(1 + np.abs(x1[1:] - x2[1:]))))
        return np.sum(np.log(1. + np.abs(x1[1:] - x2[1:])))

    def _distance_weights(self, distances: np.ndarray) -> np.ndarray:
        # convert inf distance to 0, they will be disregarded
        is_inf = np.isinf(distances)
        distances[is_inf] = 0

        # normalize weigths using their distance. Further points will have less impact
        elongated_distances = distances**3  # TODO: tener este parametro para modificaciones
        sum_weighted = np.sum(elongated_distances, axis=1, keepdims=True)
        new_weights = np.divide(
            elongated_distances,
            sum_weighted,
            out=np.zeros_like(distances),
            where=(sum_weighted != 0)
        )
        return new_weights


if __name__ == "__main__":
    # import pandas as pd
    from setup import get_settings
    from broker import TraderBot
    # from matplotlib.pyplot import plot, savefig

    strategy_settings = get_settings("settings\demo\lorentzian_classifier.json")

    # Import project settings
    login_settings = get_settings("settings/demo/login.json")
    # trading_settings = get_settings("settings/demo/trading.json")
    mt5_login_settings = login_settings["mt5_login"]

    trader = TraderBot()
    trader.start_session(mt5_login_settings)
    trader.initialize_symbols(["EURUSD"])

    df = trader.query_historic_data("EURUSD", "H4", 5000)
    source_columns = strategy_settings["source_data"].keys()

    data, target =
    train_data = data  # [:-90, :]
    train_target = target  # [:-90]

    test_data = data[-204:-4]
    test_target = target[-204:-4]

    loren_classifier = LorentzianClassifier(
        **strategy_settings["init"]
    )

    loren_classifier.fit(train_data, train_target)
    pred_target = loren_classifier.predict(test_data)

    print(test_target)
    print(pred_target)
    print((test_target == pred_target).sum() / 200)
