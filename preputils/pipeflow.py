
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import numpy as np
from preputils.transform import Smoother, RangeScaler


def build_pipeline(config_data):
    for col_name, config in config_data.items():
        trans = config.get("transform")
        if not trans:
            continue
        transformers = []
        for action, params in trans.items():
            if action == "scaled":
                t = (f"{col_name}_{action}", Scaler(**params), col_name) #TODO
            elif action == "smoother":
                t = (f"{col_name}_{action}", Smoother(**params), col_name)
            elif action == "fillna":
                t = (f"{col_name}_{action}", Filler(**params), col_name) #TODO
            transformers.append(t)

    return ColumnTransformer(transformers)

# Define the columns and their corresponding transformers
column_transformer = ColumnTransformer(
    transformers=[
        ("smooth_ema_3", Smoother(**params), ["col1", "col2"]),
        ("smooth_sma_2", Smoother(**params), ["col1", "col2"]),
        ("range_scaler", RangeScaler(**params))
        ('standard_scaler_1', StandardScaler(**params), ['col1']), # Normalize col1 using StandardScaler
        ('minmax_scaler_1', MinMaxScaler(**params), ['col2']), # Normalize col2 using MinMaxScaler
    ])

# Apply the transformations to the columns of interest
columns_to_transform = ['col1', 'col2']
data[columns_to_transform] = column_transformer.fit_transform(data[columns_to_transform])




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
