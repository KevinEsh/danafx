

# def get_lorentzian_distance(x1: ndarray, x2: ndarray) -> float:
#     return np.sum(np.log(1 + np.abs(x1 - x2)))


# def preprocess_stock_data(
#     stock_data: DataFrame,
#     add_indicators: dict[str, str],
#     rescaled: bool = True,
#     fillna: bool = False,
# ) -> ndarray:
#     stock_data["index"] = range(0, len(stock_data))
#     stock_data["hlc3"] = HLC3(
#         stock_data.high, stock_data.low, stock_data.close)
#     stock_data["rsi14"] = RSISmoothIndicator(stock_data.close, fillna=False)
#     stock_data["rsi9"] = RSISmoothIndicator(stock_data.close, 9, fillna=False)
#     stock_data["cci"] = CCISmoothIndicator(
#         stock_data.high, stock_data.low, stock_data.close, fillna=False)
#     stock_data["wt"] = WaveTrendIndicator(stock_data.hlc3, fillna=False)
#     stock_data["adx"] = ADXSmoothIndicator(
#         stock_data.high, stock_data.low, stock_data.close, fillna=False)
#     # stock_data["ground_signal"] = get_signal_labels(stock_data["close"], -4)

#     # stock_data.dropna(axis=0, inplace=True)
#     data = stock_data[add_indicators].values.reshape(-1, len(add_indicators))
#     # target = stock_data["ground_signal"].values

#     return data  # , target
