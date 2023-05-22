
from sklearn.preprocessing import MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import numpy as np
from pandas import DataFrame
from datatools.transform import Smoother, RangeScaler


def build_pipeline(config_data):
    for col_name, config in config_data.items():
        trans = config.get("transform")
        if not trans:
            continue
        transformers = []
        for action, params in trans.items():
            if action == "scaled":
                t = (f"{col_name}_{action}", Scaler(
                    **params), col_name)  # TODO
            elif action == "smoother":
                t = (f"{col_name}_{action}", Smoother(**params), col_name)
            elif action == "fillna":
                t = (f"{col_name}_{action}", Filler(
                    **params), col_name)  # TODO
            transformers.append(t)

    return ColumnTransformer(transformers)


# Define the columns and their corresponding transformers
column_transformer = ColumnTransformer(
    transformers=[
        ("smooth_ema_3", Smoother(**params), ["col1", "col2"]),
        ("smooth_sma_2", Smoother(**params), ["col1", "col2"]),
        ("range_scaler", RangeScaler(**params))
        # Normalize col1 using StandardScaler
        ('standard_scaler_1', StandardScaler(**params), ['col1']),
        # Normalize col2 using MinMaxScaler
        ('minmax_scaler_1', MinMaxScaler(**params), ['col2']),
    ])


# Assuming recarray data has been loaded into 'data'


def transform(candles):
    df = DataFrame()

    # Adding new columns
    df['range'] = candles.high - candles.low
    df['change'] = candles.close - candles.open

    # Define your custom scaler
    def custom_scaler(X):
        # Define your custom transformation here
        return X / np.max(X)

    CustomScaler = FunctionTransformer(custom_scaler, kw_args={})

    # Define preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('minmax_for_range', MinMaxScaler((-1, 1)), ['range']),
            ('custom_for_change', CustomScaler, ['change']),
        ])

    # Apply preprocessing pipeline
    df_preprocessed = preprocessor.fit_transform(df)
    f = get_recarray(df_preprocessed.T, names=["rate", "change"])

    concat_recarrays(candles, f)
# If you want the output to remain a DataFrame
#df_preprocessed = pd.DataFrame(df_preprocessed, columns=['range', 'change'])
# Assuming 'df' is your DataFrame
# df_preprocessed.to_records(index=False)


# Apply the transformations to the columns of interest
columns_to_transform = ['col1', 'col2']
data[columns_to_transform] = column_transformer.fit_transform(
    data[columns_to_transform])


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
