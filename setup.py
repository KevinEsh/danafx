from trade.indicators2 import get_signal_labels, HLC3


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
    from trade.strategies.gaussian_regressor import GaussianStockRegressor
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

    data = df_rates[["high", "low", "close"]
                    ].shift(-1, fill_value=1.0).values.reshape(-1, 3)
    target = df_rates["close"]

    train_data = data[:-90, 1:]
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
