from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ExpSineSquared, RationalQuadratic
from sklearn.gaussian_process import GaussianProcessRegressor, GaussianProcessClassifier
import numpy as np
import matplotlib.pyplot as plt
import time


class GaussianStockRegressor:
    def __init__(self) -> None:
        # TODO: poner de parametros los modificadores del kernel
        expsinsqrt = ExpSineSquared(1.0, 15.0, periodicity_bounds=(1e-3, 1e4))
        rbf = RBF(length_scale=14, length_scale_bounds="fixed")
        noice = WhiteKernel(1e-2, noise_level_bounds=(1e-7, 1e-4))

        kernel = 1.0 * expsinsqrt * rbf + noice
        self.gaussian_process = GaussianProcessRegressor(kernel=kernel)

    def fit(self, train_data, train_target) -> None:
        self.train_data = train_data
        self.train_target = train_target
        self.gaussian_process.fit(self.train_data, self.train_target)

    def predict(self, data, return_std: str = True) -> np.ndarray:
        start_time = time.time()
        mean_pred, std_pred = self.gaussian_process.predict(data, return_std)
        print(f"Time for KernelRidge predict: {time.time() - start_time:.3f} seconds")
        return mean_pred, std_pred


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from preprocessing import preprocess_stock_data
    from setup import get_settings
    from ktrader import TraderBot
    from numpy import newaxis, arange
    # from matplotlib.pyplot import plot, savefig

    strategy_settings = get_settings("settings\demo\lorentzian_classifier.json")

    # Import project settings
    login_settings = get_settings("settings/demo/login.json")
    # trading_settings = get_settings("settings/demo/trading.json")
    mt5_login_settings = login_settings["mt5_login"]

    trader = TraderBot()
    trader.start_session(mt5_login_settings)
    trader.initialize_symbols(["EURUSD"])

    df = trader.query_historic_data("EURUSD", "H1", 2000)
    source_columns = strategy_settings["source_data"].keys()

    # X, y = preprocess_stock_data(df, source_columns, True, False)
    # data = arange(0, 500, 1)[:, newaxis]
    add_indicators = ["index", "hlc3", "rsi14", "rsi9", "cci", "wt", "adx"]
    target = df.close.values
    data = preprocess_stock_data(df, add_indicators)

    train_data = data[50:1500, :]
    train_target = target[50:1500]

    test_data = data[1300:, :]
    test_target = target[1300:]

    # Initialize the Gaussian Process Regressor with the Rational Quadratic Kernel
    noice = WhiteKernel(1e-4, noise_level_bounds=(1e-6, 1e-3))
    esq_kernel = ExpSineSquared(1.0, 15.0, periodicity_bounds=(1e-3, 1e4))
    rq_kernel = 1.0 * RationalQuadratic(alpha=5.5, length_scale=8.0) + noice
    rbf_kernel = 1.0e-1 * RBF(length_scale=1,  length_scale_bounds=(1e-5, 1.0))
    gp = GaussianProcessRegressor(kernel=rq_kernel)  # , random_state=0)
    # gp_rbf = GaussianProcessRegressor(kernel=rbf_kernel * esq_kernel, random_state=0)

    # Fit the GP to the data
    gp.fit(train_data, train_target)
    # gp_rbf.fit(train_data, train_target)

    # y_pred2, std2 = gp_rbf.predict(test_data, return_std=True)
    y_pred, std = gp.predict(test_data, return_std=True)

    # Visualize the results
    # plt.scatter(data[:, 0], target, color='black', label='Data', alpha=0.4)
    plt.plot(data[:, 0], target, color='black', label='Data', alpha=0.4)
    plt.plot(test_data[:, 0], y_pred, color='blue', label='Prediction RQ')
    # plt.plot(test_data, y_pred2, color='red', label='Prediction RBF')
    # plt.fill_between(test_data[:, 0].ravel(), y_pred - std, y_pred + std, alpha=0.1, color='blue')
    # plt.fill_between(test_data.ravel(), y_pred2 - std2, y_pred2 + std2, alpha=0.1, color='red')
    plt.legend()
    plt.savefig("test1.jpeg")

    # rng = np.random.RandomState(0)
    # data = np.linspace(0, 50, num=1_000).reshape(-1, 1)
    # target = np.sin(data).ravel()

    # training_sample_indices = rng.choice(np.arange(0, 400), size=200, replace=False)
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
