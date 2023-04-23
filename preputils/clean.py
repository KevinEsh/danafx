from pandas import Series
from trade.metadata import CandleLike


def copy_format(data: CandleLike, from_data: CandleLike, name: str) -> CandleLike:
    # Create a new object with the same type as the input
    # TODO: checar si funciona esto
    data_like = type(from_data)(data)
    if isinstance(data_like, Series):
        data_like.name = name
        data_like.index = from_data.index
    else:
        data_like.dtype.names = from_data.dtype.names
    return data_like
