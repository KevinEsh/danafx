"""
An extension library for NumPy_ that implements common array operations not present in NumPy.

Window operations
-----------------

- :func:`numpy_ext.expanding`
- :func:`numpy_ext.expanding_apply`
- :func:`numpy_ext.rolling`
- :func:`numpy_ext.rolling_apply`

Operations with nans
--------------------

- :func:`numpy_ext.nans`
- :func:`numpy_ext.drop_na`
- :func:`numpy_ext.fill_na`
- :func:`numpy_ext.fill_not_finite`
- :func:`numpy_ext.prepend_na`

Others
------
- :func:`numpy_ext.apply_map`
- :func:`numpy_ext.expstep_range`

Functions
---------

"""
from functools import partial
from joblib import Parallel, delayed
from typing import Callable, Any, Union, Generator, Tuple, List

import numpy as np
from numpy.lib.recfunctions import merge_arrays, stack_arrays
from numpy.core.records import fromarrays as get_recarray


Number = Union[int, float]

def shift(
    arr: np.ndarray, 
    n: int = 1, 
    fill_value: Any = np.nan, 
    inplace: bool = False
) -> np.ndarray:
    """
    Shifts the elements in a numpy array.

    Parameters:
        arr (np.ndarray): The input array.
        n (int, optional): The number of places to shift. Positive for right shift, negative for left shift. Defaults to 1.
        fill_value (Any, optional): The value to fill the new spots with. Defaults to np.nan.
        inplace (bool, optional): If True, performs operation in-place, modifying the original array. Otherwise, creates a new array. Defaults to False.

    Returns:
        np.ndarray: The array after shifting the elements.
    """
    if inplace:
        if n > 0:
            arr[n:] = arr[:-n]
            arr[:n] = fill_value
        elif n < 0:
            arr[:n] = arr[-n:]
            arr[n:] = fill_value
        return arr
    
    if n > 0:
        result = np.empty_like(arr)
        result[:n] = fill_value
        result[n:] = arr[:-n]
    elif n < 0:
        result = np.empty_like(arr)
        result[n:] = fill_value
        result[:n] = arr[-n:]
    else:
        result = arr
    return result

def addpop(arr: np.recarray, value: Number) -> np.ndarray:
    """Appends a value to the end of an array and pops the first value of the array.

    Args:
      array: The NumPy array to append the value to and pop the first value from.
      value: The value to append to the end of the array.

    Returns:
      The new array after the value has been appended and the first value has been popped.
    """

    # Append the value to the end of the array.
    arr = np.append(arr, value)

    # Pop the first value of the array.
    return np.delete(arr, 0)


def append_recarrays(arrays: Tuple[np.recarray]) -> np.recarray:
    return stack_arrays(arrays, usemask=False, asrecarray=True)


def addpop_recarrays(arr1: np.recarray, arr2: np.recarray) -> np.recarray:
    stacked_recarray = append_recarrays((arr1, arr2))
    return np.delete(stacked_recarray, np.s_[:arr2.shape[0]])


def concat_recarrays(
    arr1: np.recarray,
    arr2: np.recarray,
) -> np.recarray:
    return merge_arrays(
        (arr1, arr2),
        fill_value=np.nan,
        asrecarray=True,
        flatten=True)


def find_index(arr, value):
    if np.isin(value, arr):
        return np.searchsorted(arr, value)
    else:
        return None


def find_supreme(value, arr, as_index: bool = False):
    """
    Given a sorted numpy array and a value, this function finds the 
    smallest value in the array that is greater than or equal to the value.

    Parameters
    ----------
    arr : numpy.ndarray
        A sorted numpy array.
    value : int
        The value to find the smallest supreme of in the array.

    Returns
    -------
    int or None
        The index of the smallest value in the array that is greater than or equal to
        the value. If all elements in the array are less than the value, returns None.

    Example
    -------
    >>> arr = np.array([1, 2, 3, 4, 5, 6])
    >>> value = 4
    >>> print(find_smallest_supreme(arr, value))
    3
    """
    idx = np.searchsorted(arr, value, side='left')
    if idx == len(arr) or arr[idx] < value:
        return None
    else:
        return idx if as_index else arr[idx]

def find_infimum(value, arr, as_index: bool = False):
    """
    Given a sorted numpy array and a value, this function finds the 
    smallest value in the array that is greater than or equal to the value.

    Parameters
    ----------
    arr : numpy.ndarray
        A sorted numpy array.
    value : int
        The value to find the smallest supreme of in the array.

    Returns
    -------
    int or None
        The index of the smallest value in the array that is greater than or equal to
        the value. If all elements in the array are less than the value, returns None.

    Example
    -------
    >>> arr = np.array([1, 2, 3, 4, 5, 6])
    >>> value = 4
    >>> print(find_smallest_supreme(arr, value))
    3
    """
    raise NotImplementedError()
    idx = np.searchsorted(arr, value, side='left')
    if idx == len(arr) or arr[idx] > value:
        return None
    else:
        return idx if as_index else arr[idx]

def expstep_range(
    start: Number,
    end: Number,
    min_step: Number = 1,
    step_mult: Number = 1,
    round_func: Callable = None
) -> np.ndarray:
    """
    Return spaced values within a given interval. Step is increased by a multiplier on each iteration.

    Parameters
    ----------
    start : int or float
        Start of interval, inclusive
    end : int or float
        End of interval, exclusive
    min_step : int or float, optional
        Minimal step between values. Must be bigger than 0. Default is 1.
    step_mult : int or float, optional
        Multiplier by which to increase the step on each iteration. Must be bigger than 0. Default is 1.
    round_func: Callable, optional
        Vectorized rounding function, e.g. np.ceil, np.floor, etc. Default is None.

    Returns
    -------
    np.ndarray
        Array of exponentially spaced values.

    Examples
    --------
    >>> expstep_range(1, 100, min_step=1, step_mult=1.5)
    array([ 1.        ,  2.        ,  3.5       ,  5.75      ,  9.125     ,
           14.1875    , 21.78125   , 33.171875  , 50.2578125 , 75.88671875])
    >>> expstep_range(1, 100, min_step=1, step_mult=1.5, round_func=np.ceil)
    array([ 1.,  2.,  4.,  6., 10., 15., 22., 34., 51., 76.])
    >>> expstep_range(start=-1, end=-100, min_step=1, step_mult=1.5)
    array([ -1.        ,  -2.        ,  -3.5       ,  -5.75      ,
            -9.125     , -14.1875    , -21.78125   , -33.171875  ,
           -50.2578125 , -75.88671875])

    Generate array of ints

    >>> expstep_range(start=100, end=1, min_step=1, step_mult=1.5).astype(int)
    array([100,  99,  97,  95,  91,  86,  79,  67,  50,  25])
    """
    if step_mult <= 0:
        raise ValueError('mult_step should be bigger than 0')

    if min_step <= 0:
        raise ValueError('min_step should be bigger than 0')

    last = start
    values = []
    step = min_step

    sign = 1 if start < end else -1

    while start < end and last < end or start > end and last > end:
        values.append(last)
        last += max(step, min_step) * sign
        step = abs(step * step_mult)

    values = np.array(values)
    if not round_func:
        return values

    values = np.array(round_func(values))
    _, idx = np.unique(values, return_index=True)
    return values[np.sort(idx)]


def apply_map(func: Callable[[Any], Any], array: Union[List, np.ndarray]) -> np.ndarray:
    """
    Apply a function element-wise to an array.

    Parameters
    ----------
    func : Callable[[Any], Any]
        Function that accepts one argument and returns a single value.
    array : Union[List, np.ndarray]
        Input array or a list. Any lists will be converted to np.ndarray first.

    Returns
    -------
    np.ndarray
        Resulting array.

    Examples
    --------
    >>> apply_map(lambda x: 0 if x < 3 else 1, [[2, 2], [3, 3]])
    array([[0, 0],
           [1, 1]])
    """
    array = np.array(array)
    array_view = array.flat
    array_view[:] = [func(x) for x in array_view]
    return array


#############################
# Operations with nans
#############################


def nans(shape: Union[int, Tuple[int, ...]], dtype=np.float64) -> np.ndarray:
    """
    Return a new array of a given shape and type, filled with np.nan values.

    Parameters
    ----------
    shape : int or tuple of ints
        Shape of the new array, e.g., (2, 3) or 2.
    dtype: data-type, optional

    Returns
    -------
    np.ndarray
        Array of np.nans of the given shape.

    Examples
    --------
    >>> nans(3)
    array([nan, nan, nan])
    >>> nans((2, 2))
    array([[nan, nan],
           [nan, nan]])
    >>> nans(2, np.datetime64)
    array(['NaT', 'NaT'], dtype=datetime64)
    """
    if np.issubdtype(dtype, np.integer):
        dtype = np.float
    arr = np.empty(shape, dtype=dtype)
    arr.fill(np.nan)
    return arr


def drop_na(array: np.ndarray) -> np.ndarray:
    """
    Return a given array flattened and with nans dropped.

    Parameters
    ----------
    array : np.ndarray
        Input array.

    Returns
    -------
    np.ndarray
        New array without nans.

    Examples
    --------
    >>> drop_na(np.array([np.nan, 1, 2]))
    array([1., 2.])
    """
    # find the indices of the NaN values in the array
    nan_indices = np.where(np.isnan(array))

    # delete the NaN values from the array
    return np.delete(array, nan_indices)
    # return array[~np.isnan(array)]


def fill_na(array: np.ndarray, value: Any) -> np.ndarray:
    """
    Return a copy of array with nans replaced with a given value.

    Parameters
    ----------
    array : np.ndarray
        Input array.
    value : Any
        Value to replace nans with.

    Returns
    -------
    np.ndarray
        A copy of array with nans replaced with the given value.

    Examples
    --------
    >>> fill_na(np.array([np.nan, 1, 2]), -1)
    array([-1.,  1.,  2.])
    """
    ar = array.copy()
    ar[np.isnan(ar)] = value
    return ar


def fill_not_finite(array: np.ndarray, value: Any = 0) -> np.ndarray:
    """
    Return a copy of array with nans and infs replaced with a given value.

    Parameters
    ----------
    array : np.ndarray
        Input array.
    value : Any, optional
        Value to replace nans and infs with. Default is 0.

    Returns
    -------
    np.ndarray
        A copy of array with nans and infs replaced with the given value.

    Examples
    --------
    >>> fill_not_finite(np.array([np.nan, np.inf, 1, 2]), 99)
    array([99., 99.,  1.,  2.])
    """
    ar = array.copy()
    ar[~np.isfinite(array)] = value
    return ar


def prepend_na(array: np.ndarray, n: int) -> np.ndarray:
    """
    Return a copy of array with nans inserted at the beginning.

    Parameters
    ----------
    array : np.ndarray
        Input array.
    n : int
        Number of elements to insert.

    Returns
    -------
    np.ndarray
        New array with nans added at the beginning.

    Examples
    --------
    >>> prepend_na(np.array([1, 2]), 2)
    array([nan, nan,  1.,  2.])
    """
    if not len(array):  # if empty, simply create empty array
        return np.hstack((nans(n), array))

    elem = array[0]
    dtype = np.float64
    if hasattr(elem, 'dtype'):
        dtype = elem.dtype

    if hasattr(elem, '__len__') and len(elem) > 1:  # if the array has many dimension
        if isinstance(array, np.ndarray):
            array_shape = array.shape
        else:
            array_shape = np.array(array).shape
        return np.vstack((nans((n, *array_shape[1:]), dtype), array))
    else:
        return np.hstack((nans(n, dtype), array))


#############################
# window operations
#############################


def rolling(
    array: np.ndarray,
    window: int,
    skip_na: bool = False,
    as_array: bool = False
) -> Union[Generator[np.ndarray, None, None], np.ndarray]:
    """
    Roll a fixed-width window over an array.
    The result is either a 2-D array or a generator of slices, controlled by `as_array` parameter.

    Parameters
    ----------
    array : np.ndarray
        Input array.
    window : int
        Size of the rolling window.
    skip_na : bool, optional
        If False, the sequence starts with (window-1) windows filled with nans. If True, those are omitted.
        Default is False.
    as_array : bool, optional
        If True, return a 2-D array. Otherwise, return a generator of slices. Default is False.

    Returns
    -------
    np.ndarray or Generator[np.ndarray, None, None]
        Rolling window matrix or generator

    Examples
    --------
    >>> rolling(np.array([1, 2, 3, 4, 5]), 2, as_array=True)
    array([[nan,  1.],
           [ 1.,  2.],
           [ 2.,  3.],
           [ 3.,  4.],
           [ 4.,  5.]])

    Usage with numpy functions

    >>> arr = rolling(np.array([1, 2, 3, 4, 5]), 2, as_array=True)
    >>> np.sum(arr, axis=1)
    array([nan,  3.,  5.,  7.,  9.])
    """
    if not any(isinstance(window, t) for t in [int, np.integer]):
        raise TypeError(f'Wrong window type ({type(window)}) int expected')

    window = int(window)

    if array.size < window:
        raise ValueError('array.size should be bigger than window')

    def rows_gen():
        if not skip_na:
            yield from (prepend_na(array[:i + 1], (window - 1) - i) for i in np.arange(window - 1))

        starts = np.arange(array.size - (window - 1))
        yield from (array[start:end] for start, end in zip(starts, starts + window))

    return np.array([row for row in rows_gen()]) if as_array else rows_gen()


def rolling_apply(
    func: Callable,
    window: int,
    *arrays: np.ndarray,
    prepend_nans: bool = True,
    n_jobs: int = 1,
    **kwargs
) -> np.ndarray:
    """
    Roll a fixed-width window over an array or a group of arrays, producing slices.
    Apply a function to each slice / group of slices, transforming them into a value.
    Perform computations in parallel, optionally.
    Return a new np.ndarray with the resulting values.

    Parameters
    ----------
    func : Callable
        The function to apply to each slice or a group of slices.
    window : int
        Window size.
    *arrays : list
        List of input arrays.
    prepend_nans : bool
        Specifies if nans should be prepended to the resulting array
    n_jobs : int, optional
        Parallel tasks count for joblib. If 1, joblib won't be used. Default is 1.
    **kwargs : dict
        Input parameters (passed to func, must be named).

    Returns
    -------
    np.ndarray

    Examples
    --------
    >>> arr = np.array([1, 2, 3, 4, 5])
    >>> rolling_apply(sum, 2, arr)
    array([nan,  3.,  5.,  7.,  9.])
    >>> arr2 = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
    >>> func = lambda a1, a2, k: (sum(a1) + max(a2)) * k
    >>> rolling_apply(func, 2, arr, arr2, k=-1)
    array([  nan,  -5.5,  -8.5, -11.5, -14.5])
    """
    if not any(isinstance(window, t) for t in [int, np.integer]):
        raise TypeError(f'Wrong window type ({type(window)}) int expected')

    window = int(window)

    if max(len(x.shape) for x in arrays) != 1:
        raise ValueError('Wrong array shape. Supported only 1D arrays')

    if len({array.size for array in arrays}) != 1:
        raise ValueError('Arrays must be the same length')

    def _apply_func_to_arrays(idxs):
        return func(*[array[idxs[0]:idxs[-1] + 1] for array in arrays], **kwargs)

    array = arrays[0]
    rolls = rolling(
        array if len(arrays) == n_jobs == 1 else np.arange(len(array)),
        window=window,
        skip_na=True
    )

    if n_jobs == 1:
        if len(arrays) == 1:
            arr = list(map(partial(func, **kwargs), rolls))
        else:
            arr = list(map(_apply_func_to_arrays, rolls))
    else:
        f = delayed(_apply_func_to_arrays)
        arr = Parallel(n_jobs=n_jobs)(f(idxs[[0, -1]]) for idxs in rolls)

    return prepend_na(arr, n=window - 1) if prepend_nans else np.array(arr)


def expanding(
    array: np.ndarray,
    min_periods: int = 1,
    skip_na: bool = True,
    as_array: bool = False
) -> Union[Generator[np.ndarray, None, None], np.ndarray]:
    """
    Roll an expanding window over an array.
    The window size starts at min_periods and gets incremented by 1 on each iteration.
    The result is either a 2-D array or a generator of slices, controlled by `as_array` parameter.

    Parameters
    ----------
    array : np.ndarray
        Input array.
    min_periods : int, optional
        Minimum size of the window. Default is 1.
    skip_na : bool, optional
        If False, the windows of size less than min_periods are filled with nans. If True, they're dropped.
        Default is True.
    as_array : bool, optional
        If True, return a 2-D array. Otherwise, return a generator of slices. Default is False.

    Returns
    -------
    np.ndarray or Generator[np.ndarray, None, None]

    Examples
    --------
    >>> expanding(np.array([1, 2, 3, 4, 5]), 3, as_array=True)
    array([array([1, 2, 3]), array([1, 2, 3, 4]), array([1, 2, 3, 4, 5])],
          dtype=object)
    """
    if not any(isinstance(min_periods, t) for t in [int, np.integer]):
        raise TypeError(
            f'Wrong min_periods type ({type(min_periods)}) int expected')

    min_periods = int(min_periods)

    if array.size < min_periods:
        raise ValueError('array.size should be bigger than min_periods')

    def rows_gen():
        if not skip_na:
            yield from (nans(i) for i in np.arange(1, min_periods))

        yield from (array[:i] for i in np.arange(min_periods, array.size + 1))

    return np.array([row for row in rows_gen()]) if as_array else rows_gen()


def expanding_apply(
    func: Callable,
    min_periods: int,
    *arrays: np.ndarray,
    prepend_nans: bool = True,
    n_jobs: int = 1,
    **kwargs
) -> np.ndarray:
    """
    Roll an expanding window over an array or a group of arrays producing slices.
    The window size starts at min_periods and gets incremented by 1 on each iteration.
    Apply a function to each slice / group of slices, transforming them into a value.
    Perform computations in parallel, optionally.
    Return a new np.ndarray with the resulting values.

    Parameters
    ----------
    func : Callable
        The function to apply to each slice or a group of slices.
    min_periods : int
        Minimal size of expanding window.
    *arrays : list
        List of input arrays.
    prepend_nans : bool
        Specifies if nans should be prepended to the resulting array
    n_jobs : int, optional
        Parallel tasks count for joblib. If 1, joblib won't be used. Default is 1.
    **kwargs : dict
        Input parameters (passed to func, must be named).

    Returns
    -------
    np.ndarray

    Examples
    --------
    >>> arr = np.array([1, 2, 3, 4, 5])
    >>> expanding_apply(sum, 2, arr)
    array([nan,  3.,  6., 10., 15.])
    >>> arr2 = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
    >>> func = lambda a1, a2, k: (sum(a1) + max(a2)) * k
    >>> expanding_apply(func, 2, arr, arr2, k=-1)
    array([  nan,  -5.5,  -9.5, -14.5, -20.5])
    """
    if not any(isinstance(min_periods, t) for t in [int, np.integer]):
        raise TypeError(
            f'Wrong min_periods type ({type(min_periods)}) int expected')

    min_periods = int(min_periods)

    if max(len(x.shape) for x in arrays) != 1:
        raise ValueError('Supported only 1-D arrays')

    if len({array.size for array in arrays}) != 1:
        raise ValueError('Arrays must be the same length')

    def _apply_func_to_arrays(idxs):
        return func(*[array[idxs.astype(np.int)] for array in arrays], **kwargs)

    array = arrays[0]
    rolls = expanding(
        array if len(arrays) == n_jobs == 1 else np.arange(len(array)),
        min_periods=min_periods,
        skip_na=True
    )

    if n_jobs == 1:
        if len(arrays) == 1:
            arr = list(map(partial(func, **kwargs), rolls))
        else:
            arr = list(map(_apply_func_to_arrays, rolls))
    else:
        f = delayed(_apply_func_to_arrays)
        arr = Parallel(n_jobs=n_jobs)(map(f, rolls))

    return prepend_na(arr, n=min_periods - 1) if prepend_nans else np.array(arr)
