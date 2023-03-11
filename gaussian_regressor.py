from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ExpSineSquared
from sklearn.gaussian_process import GaussianProcessRegressor
import numpy as np
import matplotlib.pyplot as plt
import time


class GaussianStockPredictor:
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
    rng = np.random.RandomState(0)
    data = np.linspace(0, 50, num=1_000).reshape(-1, 1)
    target = np.sin(data).ravel()

    training_sample_indices = rng.choice(np.arange(0, 400), size=200, replace=False)
    training_data = data[training_sample_indices]
    training_noisy_target = target[training_sample_indices] + 0.5 * rng.randn(
        len(training_sample_indices)
    )

    print(training_data)
    print(training_noisy_target)

    gauss_predictor = GaussianStockPredictor()
    gauss_predictor.fit(training_data, training_noisy_target)
    mean_predictions_gpr, std_predictions_gpr = gauss_predictor.predict(data)

    plt.plot(data, target, label="True signal", linewidth=2, linestyle="dashed")
    plt.scatter(
        training_data,
        training_noisy_target,
        color="black",
        label="Noisy measurements",
        alpha=0.2
    )
    # Plot the predictions of the kernel ridge
    # plt.plot(
    #     data,
    #     predictions_kr,
    #     label="Kernel ridge",
    #     linewidth=2,
    #     linestyle="dashdot",
    # )
    # Plot the predictions of the gaussian process regressor
    plt.plot(
        data,
        mean_predictions_gpr,
        label="Gaussian process regressor",
        linewidth=0.1,
        linestyle="dotted",
    )
    plt.fill_between(
        data.ravel(),
        mean_predictions_gpr - std_predictions_gpr,
        mean_predictions_gpr + std_predictions_gpr,
        color="tab:green",
        alpha=0.1,
    )
    plt.legend(loc="lower right")
    plt.xlabel("data")
    plt.ylabel("target")
    _ = plt.title("Comparison between kernel ridge and gaussian process regressor")

    plt.savefig("gr.jpeg")
