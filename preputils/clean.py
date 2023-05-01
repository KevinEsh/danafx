from pandas import Series
from trade.metadata import CandleLike
from numpy import recarray, ndarray
from numpy.lib.recfunctions import merge_arrays
from numpy.core.records import fromarrays

def copy_format(data: CandleLike, from_data: CandleLike, names: list[str]) -> CandleLike:
    # Create a new object with the same type as the input
    # TODO: checar si funciona esto
    data_like = type(from_data)(data)
    if isinstance(data_like, Series):
        data_like.name = names
        data_like.index = from_data.index
    else:
        data_like = as_recarray(data, names=names)
    return data_like

def as_recarray(arrays: list[ndarray], names: list[str]) -> recarray:
    return fromarrays(arrays, names=names)

def concat_recarrays(
    arr1: recarray, 
    arr2: recarray, 
) -> recarray:
    return merge_arrays((arr1, arr2), asrecarray=True, flatten=True)

    # Create a new recarray with an additional field
    # out_dtypes = arr1.dtype.descr + arr2.dtype.descr #new_dtypes #[('field3', '<i8')]
    # new_arr = recarray(arr1.shape, dtype=out_dtypes)
    # for name in arr1.dtype.names:
    #     new_arr[name] = arr1[name]
    # for name in arr2.dtype.names:
    #     new_arr[name] = arr2[name]

    # return new_arr.view(recarray)
