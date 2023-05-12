import numpy as np


def crossingover(arr1: np.ndarray, arr2: np.ndarray, delta: float = 0):
    """Check if the value of arr2 is greater than the final value of arr2
    #and if the value of arr1 on the previous bar was less than or equal to
    the value of arr2

    Args:
        arr1 (ndarray): Source data that has to cross over from bottom to top
        arr2 (ndarray): Source data to test crossing condition

    Returns:
        bool: Signal if the arr1 crosses over arr2
    """
    # Find the points where arr1 crosses over arr2
    cross_points = np.logical_and(
        arr1[:-1] <= arr2[:-1] + delta,  # below condition
        arr1[1:] > arr2[1:] + delta)  # over condition

    # Create a boolean array of the same shape as the input arrays
    result = np.zeros_like(arr1, dtype=bool)

    # Set the values of the result array to True where arr1 crosses over arr2
    result[1:][cross_points] = True

    return result


def crossingunder(arr1: np.ndarray, arr2: np.ndarray, delta: float = 0):
    """Check if the value of arr1 is greater than the final value of arr2
    #and if the value of arr1 on the previous bar was less than or equal to
    the value of arr2

    Args:
        arr1 (ndarray): Source data that has to cross over from bottom to top
        arr2 (ndarray): Source data to test crossing condition

    Returns:
        bool: True if the arr1 crosses under arr2
    """
    # Find the points where arr1 crosses over arr2
    cross_points = np.logical_and(
        arr1[:-1] >= arr2[:-1] + delta,  # upper condition
        arr1[1:] < arr2[1:] + delta)  # under condition

    # Create a boolean array of the same shape as the input arrays
    result = np.zeros_like(arr1, dtype=bool)

    # Set the values of the result array to True where arr1 crosses over arr2
    result[1:][cross_points] = True

    return result
