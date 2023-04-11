from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ExpSineSquared, RationalQuadratic
from sklearn.gaussian_process import GaussianProcessRegressor
import numpy as np
import matplotlib.pyplot as plt
import time


class GaussianStockRegressor:
    def __init__(self) -> None:
        # TODO: poner de parametros los modificadores del kernel
        # expsinsqrt = ExpSineSquared(1.0, 15.0, periodicity_bounds=(1e-3, 1e4))
        # noice = WhiteKernel(1e-2, noise_level_bounds=(1e-7, 1e-4))
        self.rq_kernel = 5.97**2 * RationalQuadratic(
            alpha=5.98e+05,
            length_scale=16.9,
            length_scale_bounds=(8, 24),
            alpha_bounds=(1e3, 1e6),
        )

        self.rbf_kernel = 107.0**2 * RBF(
            length_scale=303,
            length_scale_bounds=(1e-5, 1.0e8)
        )

        # kernel = 1.0 * expsinsqrt * rbf + noice

        self.gaussian_process = GaussianProcessRegressor(
            kernel=self.rq_kernel,
            alpha=0.001**2,
            # random_state=0,
            n_restarts_optimizer=8,
        )

    def fit(self, train_data, train_target) -> None:
        self.train_data = train_data
        self.train_target = train_target
        self.gaussian_process.fit(self.train_data, self.train_target)

    def predict(self, data, return_std: str = True) -> np.ndarray:
        mean_pred, std_pred = self.gaussian_process.predict(data, return_std)
        return mean_pred, std_pred

    def get_optimized_kernel(self):
        return self.gaussian_process.kernel_

    def save_model(self, path: str = "gp_model.pkl"):
        with open(path, 'wb') as model_file:
            pickle.dump(self.gaussian_process, model_file)


if __name__ == "__main__":
    import pickle
    import matplotlib.pyplot as plt
    from preprocessing.preprocessing import preprocess_stock_data
    from setup import get_settings
    from trade.broker import BrokerSession
    # from matplotlib.pyplot import plot, savefig

    # Import project settings
    strategy_settings = get_settings("settings\demo\lorentzian_classifier.json")
    login_settings = get_settings("settings/demo/login.json")
    # trading_settings = get_settings("settings/demo/trading.json")
    mt5_login_settings = login_settings["mt5_login"]

    session = BrokerSession()
    session.start_session(mt5_login_settings)
    session.initialize_symbols(["EURUSD"])

    df = session.query_historic_data("EURUSD", "M30", 6500)  #
    source_columns = strategy_settings["source_data"].keys()

    # X, y = preprocess_stock_data(df, source_columns, True, False)
    # data = arange(0, 500, 1)[:, newaxis]
    add_indicators = ["close"]  # ["hlc3", "rsi14", "rsi9", "cci", "wt", "adx"]
    target = df.close.values
    data = preprocess_stock_data(df, add_indicators)
    # print(data)

    train_data = data[0:6500]
    train_target = target[0:6500]

    rq_kernel = RationalQuadratic(8, 1)
    w = np.tril(rq_kernel(np.arange(6500).reshape(-1, 1)))
    sum_w = w.sum(axis=1, keepdims=True)
    pred_rq = (w @ train_data) / sum_w

    rbf_kernel = RBF(16)
    w = np.tril(rbf_kernel(np.arange(6500).reshape(-1, 1)))
    sum_w = w.sum(axis=1, keepdims=True)
    pred_rbf = (w @ train_data) / sum_w

    # test_data = data[100:]
    # test_target = target[100:]

    # Test unoptimized kernel

    # Fit the GP to the data
    # gp = GaussianStockRegressor()
    # gp.fit(train_data, train_target)
    # print(gp.get_optimized_kernel())
    # y_pred, std = gp.predict(test_data, return_std=True)

    # Visualize the results
    plt.plot(range(0, data.shape[0])[6000:], data[6000:], color='black', label='Data', alpha=0.4)
    plt.plot(range(0, data.shape[0])[6000:], pred_rbf[6000:], color='blue', label='Pred', alpha=0.4)
    plt.plot(range(0, data.shape[0])[6000:], pred_rq[6000:], color='red', label='Pred', alpha=0.4)
    # # plt.plot(data[100:, 0], y_pred, color='blue', label='Prediction RQ')
    # # plt.plot(test_data, y_pred2, color='red', label='Prediction RBF')
    # # plt.fill_between(test_data[:, 0].ravel(), y_pred - std, y_pred + std, alpha=0.1, color='blue')
    # # plt.fill_between(test_data.ravel(), y_pred2 - std2, y_pred2 + std2, alpha=0.1, color='red')
    plt.legend()
    plt.savefig("test_x.jpeg")

    # rng = np.random.RandomState(0)
    # data = np.linspace(0, 0, num=1_000).reshape(-1, 1)
    # target = np.sin(data).ravel()

    # training_sample_indices = rng.choice(np.arange(0, 400), size=6500, replace=False)
    # training_data = data[training_sample_indices]
    # training_noisy_target = target[training_sample_indices] + 0.5 * rng.randn(
    #     len(training_sample_indices)
    # )

    # print(training_data)
    # print(training_noisy_target)

    # gauss_predictor = GaussianStockPredictor()
    # gauss_predictor.fit(training_data, training_noisy_target)
    # mean_predictions_gpr, std_predictions_gpr = gauss_predictor.predict(data)

    # plt.plot(data, target, label="True signal", linewidth=2, linestyle="dashed")
    # plt.scatter(
    #     training_data,
    #     training_noisy_target,
    #     color="black",
    #     label="Noisy measurements",
    #     alpha=0.2
    # )
    # # Plot the predictions of the kernel ridge
    # # plt.plot(
    # #     data,
    # #     predictions_kr,
    # #     label="Kernel ridge",
    # #     linewidth=2,
    # #     linestyle="dashdot",
    # # )
    # # Plot the predictions of the gaussian process regressor
    # plt.plot(
    #     data,
    #     mean_predictions_gpr,
    #     label="Gaussian process regressor",
    #     linewidth=0.1,
    #     linestyle="dotted",
    # )
    # plt.fill_between(
    #     data.ravel(),
    #     mean_predictions_gpr - std_predictions_gpr,
    #     mean_predictions_gpr + std_predictions_gpr,
    #     color="tab:green",
    #     alpha=0.1,
    # )
    # plt.legend(loc="lower right")
    # plt.xlabel("data")
    # plt.ylabel("target")
    # _ = plt.title("Comparison between kernel ridge and gaussian process regressor")

    # plt.savefig("gr.jpeg")
