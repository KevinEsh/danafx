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
    from sklearn.datasets import make_regression
    import matplotlib.pyplot as plt

    # Generate some random data
    X, y = make_regression(n_samples=70, n_features=1, noise=10, random_state=0)

    # Initialize the Gaussian Process Regressor with the Rational Quadratic Kernel
    esq_kernel = ExpSineSquared(1.0, 15.0, periodicity_bounds=(1e-3, 1e4))
    rq_kernel = 1.0 * RationalQuadratic(alpha=8., length_scale=8.0)
    rbf_kernel = 1.0e-1 * RBF(length_scale=1,  length_scale_bounds=(1e-5, 1.0)) 
    gp = GaussianProcessRegressor(kernel=rq_kernel, random_state=0)
    gp_rbf = GaussianProcessRegressor(kernel=rbf_kernel * esq_kernel, random_state=0)

    # Fit the GP to the data
    gp.fit(X, y)
    gp_rbf.fit(X, y)

    # Predict the target variable at some new inputs
    X_new = np.linspace(-2, 2, 100)[:, np.newaxis]
    y_pred2, std2 = gp_rbf.predict(X_new, return_std=True)
    y_pred, std = gp.predict(X_new, return_std=True)

    # Visualize the results
    plt.scatter(X, y, color='black', label='Data', alpha=0.4)
    plt.plot(X_new, y_pred, color='blue', label='Prediction RQ')
    plt.plot(X_new, y_pred2, color='red', label='Prediction RBF')
    plt.fill_between(X_new.ravel(), y_pred - std, y_pred + std, alpha=0.1, color='blue')
    plt.fill_between(X_new.ravel(), y_pred2 - std2, y_pred2 + std2, alpha=0.1, color='red')
    plt.legend()
    plt.show()

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

    plt.savefig("gr.jpeg")
