from numpy import recarray, append, sqrt
from sklearn.neighbors import KNeighborsClassifier

from trade.strategies.abstract import Hyperparameter, TradingStrategy, OHLCbounds
from trade.indicators import RSI, ADX, CCI, WT, get_stable_min_bars #TODO: mover estos indicadores a una funcion que solo te los calcule (pipeline) y te los agregue a tu train_data

IndicatorBounds = ["RSI", "ADX", "CCI", "WT"]

class LorentzianClassifierStrategy(TradingStrategy):
    """This model specializes specifically in predicting the direction of price
    action over the course of the next 4 bars. To avoid complications with the
    ML model, this value is hardcoded to 4 bars but support for other training
    lengths may be added in the future.
    """
    config_sources = Hyperparameter("sources", "structured", IndicatorBounds) #TODO: structured
    config_window = Hyperparameter("window", "numeric", (2, 6000))
    config_n_neighbors = Hyperparameter("n_neighbors", "numeric", (0, 100))
    config_neighbors_leap = Hyperparameter("neighbors_leap", "interval", (0, 100))
    config_n_jobs = Hyperparameter("n_jobs", "numeric", (1, 5))

    def __init__(
        self,
        sources: list,
        window: int = 2000,
        n_neighbors: int = 4,
        neighbors_leap: int = 4,
        n_jobs: int = 1
    ) -> None:
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_sources._check_bounds(sources, init=True)
        self.config_window._check_bounds(window, init=True)
        self.config_n_neighbors._check_bounds(n_neighbors, init=True)
        self.config_neighbors_leap._check_bounds(neighbors_leap, init=True)
        self.config_n_jobs._check_bounds(n_jobs, init=True)

        # define the number of neighbors to use
        self._sources = sources
        self._window = window
        self._n_neighbors = n_neighbors
        self._neighbors_leap = neighbors_leap
        self._n_jobs = n_jobs

        self.min_bars = window

        # create the KNN classifier using the Lorentzian distance metric
        self.knn_classifier = KNeighborsClassifier(
            n_neighbors=self._n_neighbors,
            n_jobs=self._n_jobs,
            metric=self._modif_lorentzian_distance,
            weights=self._distance_weights,
            # metric_params={"lookback_window": 2000},
        )

    def fit(self, train_data: recarray, train_target: recarray):
        # fit the model

        for name, specs in self._sources:
            values = pipeline(train_data, specs)
            values = copy_fromat(values, train_data, name)
            append(train_data, )
        self._train_data = train_data
        self._train_target = train_target
        
        self.knn_classifier.fit(self._train_data, self._train_target)

    def generate_entry_signal(self, candle: recarray) -> int:
        return self.knn_classifier.predict(data) # TODO

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
                if largest_distance:
                    pass  # TODO

    def update_data(self, new_data: Any) -> None:
        # TODO: modificar esta funcion para poder actualizar los datos de entrenamiento cada cierto tiempo/iteraciones
        raise NotImplemented

    def _lorentzian_distance(self, x1: np.ndarray, x2s: np.ndarray) -> np.ndarray:
        return np.sum(np.log(1 + np.abs(x2s[:, 1:] - x1[1:])), axis=1)

    def _modif_lorentzian_distance(self, x1: np.ndarray, x2: np.ndarray) -> float:
        i1, i2 = x1[0], x2[0]  # get the chronological index of both points
        is_not_in_window = (i1 <= i2) or (i1 > i2 + self._lookback_window)
        # TODO: cambiar esta cosa por 4 velas atras de i2 (experimentar)
        # (i1 - i2) % self._neighbors_leap
        skip_neighbor = i1 % self._neighbors_leap
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
        # TODO: tener este parametro para modificaciones
        elongated_distances = distances**3
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
    from trade.brokers.mt5broker import TraderBot
    # from matplotlib.pyplot import plot, savefig

    strategy_settings = get_settings(
        "settings\demo\lorentzian_classifier.json")

    # Import project settings
    login_settings = get_settings("settings/demo/login.json")
    # trading_settings = get_settings("settings/demo/trading.json")
    mt5_login_settings = login_settings["mt5_login"]

    trader = TraderBot()
    trader.start_session(mt5_login_settings)
    trader.initialize_symbols(["EURUSD"])

    df = trader.query_historic_data("EURUSD", "H4", 5000)
    source_columns = strategy_settings["source_data"].keys()

    data, target = None, None  # TODO
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
