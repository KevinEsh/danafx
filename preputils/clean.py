from pandas import Series
from numpy import recarray, ndarray, nan
from numpy.core.records import fromarrays as asrecarray
from numpy.lib.recfunctions import merge_arrays, stack_arrays


def copy_format(data: ndarray, from_data: recarray, names: list[str]) -> recarray:
    # Create a new object with the same type as the input
    # TODO: checar si funciona esto
    if isinstance(from_data, Series):
        data_like = Series(data)
        data_like.name = names
        data_like.index = from_data.index
    else:
        data_like = asrecarray(data, names=names)
    return data_like

def concat_recarrays(
    arr1: recarray,
    arr2: recarray,
) -> recarray:
    return merge_arrays(
        (arr1, arr2),
        fill_value=nan,
        asrecarray=True, 
        flatten=True)

    # Create a new recarray with an additional field
    # out_dtypes = arr1.dtype.descr + arr2.dtype.descr #new_dtypes #[('field3', '<i8')]
    # new_arr = recarray(arr1.shape, dtype=out_dtypes)
    # for name in arr1.dtype.names:
    #     new_arr[name] = arr1[name]
    # for name in arr2.dtype.names:
    #     new_arr[name] = arr2[name]

    # return new_arr.view(recarray)
