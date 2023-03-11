from json import load
from os.path import exists
from ktrader import TraderBot
import mplfinance as fplt
from gaussian_regressor import GaussianStockPredictor
from utils import get_signal_labels, HLC3
from numpy import nan

# Function to import settings from settings.json


def get_settings(filepath: str) -> dict[str, str]:
    # Test the filepath to sure it exists
    if not exists(filepath):
        raise ImportError(f"{filepath} path does not exist")

    # Open the file and get the information from file
    with open(filepath, "r") as file:
        project_settings = load(file)

    return project_settings


# def signal_correction(data: list[float], signals: list[int]) -> pd.Series:
#     uptrend, downtrend, nulltrend = [], [], []
#     for i in range(1, len(signals)):
#         if signals[i] == 1:
#             uptrend.append(data[i])
#             downtrend.append(nan)
#             nulltrend.append(nan)
#         if signals[i] == 0:
#             uptrend.append(data[i])
#             downtrend.append(nan)
#             nulltrend.append(nan)
#         if signals[i] == -1:
#             uptrend.append(data[i])
#             downtrend.append(nan)
#             nulltrend.append(nan)


def plot_candlestick_chart(df_rates, symbol: str, timestamp: str) -> None:
    # change columns names to make df compatible with mplfinance
    mpl_comp_names = {
        'time': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'tick_volume': 'Volume'
    }
    saving_config = {
        "fname": f'{symbol}_{timestamp}.jpeg',
        # "dpi": None,
        # "pad_inches": 0.01,
        # "transparent": True
    }

    uptrend = df_rates.regression * df_rates.signal.apply(lambda s: nan if s != 1 else 1)
    downtrend = df_rates.regression * df_rates.signal.apply(lambda s: nan if s != -1 else 1)

    trendmarkers = [
        fplt.make_addplot(
            uptrend,
            color="green",
            linestyle='dotted',
            # type='scatter',
            width=2,
            alpha=0.8,
            marker=".",
            # markersize=20,
        ),
        fplt.make_addplot(
            downtrend,
            color="red",
            linestyle='dotted',
            # type='scatter',
            width=2,
            alpha=0.8,
            marker=".",
            # markersize=20,
        ),
    ]

    fplt.plot(
        df_rates.rename(columns=mpl_comp_names),
        type="ohlc",  # 'hollow_and_filled',  # 'candle',
        style='yahoo',  # 'charles',
        ylabel='Price ($GBP)',
        title=symbol,
        volume=True,
        tight_layout=True,
        figscale=1.25,
        figratio=(5, 2),
        # mav=(5, 20),
        savefig=saving_config,
        addplot=trendmarkers,
        fill_between=[
            {
                "y1": df_rates['down'].values,
                "y2": df_rates['up'].values,
                # "where": df_rates["signal"] == 1,
                "color": "gray",
                "alpha": 0.07,
                # "interpolate": True,
                # "step": 'pre',
                "antialiased": True
            },
        ]
    )


# def plot_gauss_regression():
#     plt.fill_between(
#         data.ravel(),
#         mean_predictions_gpr - std_predictions_gpr,
#         mean_predictions_gpr + std_predictions_gpr,
#         color="tab:green",
#         alpha=0.1,
#     )


# Main function
if __name__ == '__main__':
    # Import project settings
    login_settings = get_settings("settings/demo/login.json")
    trading_settings = get_settings("settings/demo/trading.json")

    mt5_login_settings = login_settings["mt5_login"]

    trader = TraderBot()

    # Start MT5
    trader.start_session(mt5_login_settings)
    trader.initialize_symbols(["EURUSD"])
    df_rates = trader.query_historic_data("EURUSD", "H4", 100)
    df_rates["hlc3"] = HLC3(df_rates.high, df_rates.low, df_rates.close)
    df_rates["signal"] = get_signal_labels(df_rates["hlc3"], -4)

    data = df_rates[["high", "low", "close"]].shift(-1, fill_value=1.0).values.reshape(-1, 3)
    target = df_rates["close"]

    train_data = data[:-90, :]
    train_target = target[:-90]

    gauss_predictor = GaussianStockPredictor()
    gauss_predictor.fit(train_data, train_target)
    mean, std = gauss_predictor.predict(data)
    df_rates["regression"] = mean
    df_rates["up"] = mean + std
    df_rates["down"] = mean - std

    # for i in range(190, 199):
    #     mean, std = gauss_predictor.predict(data[i].reshape(-1, 3))
    #     df_rates.iloc[i]["regression"] = mean[0]
    #     df_rates.iloc[i]["up"] = mean[0] + std[0]
    #     df_rates.iloc[i]["down"] = mean[0] - std[0]
    #     df_rates.iloc[i+1]["close"] = mean
    #     df_rates.iloc[i+1]["high"] = mean + std
    #     df_rates.iloc[i+1]["low"] = mean - std
    # print(df_rates)
    plot_candlestick_chart(df_rates, "EURUSD", "2023-03-06")
    # print(df_rates)
    # trader.place_order("BUY_LIMIT", "EURUSD", 0.01, 1.04420, 1.04420 * 0.9, 1.04420 * 1.1)
