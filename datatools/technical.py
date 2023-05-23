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
    if isinstance(arr1, list):
        arr1 = np.array(arr1)

    if isinstance(arr2, list):
        arr2 = np.array(arr2)

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
    if isinstance(arr1, list):
        arr1 = np.array(arr1)

    if isinstance(arr2, list):
        arr2 = np.array(arr2)

    # Find the points where arr1 crosses over arr2
    cross_points = np.logical_and(
        arr1[:-1] >= arr2[:-1] + delta,  # upper condition
        arr1[1:] < arr2[1:] + delta)  # under condition

    # Create a boolean array of the same shape as the input arrays
    result = np.zeros_like(arr1, dtype=bool)

    # Set the values of the result array to True where arr1 crosses over arr2
    result[1:][cross_points] = True

    return result


def above(arr1: np.ndarray, arr2: np.ndarray, delta: float = 0):
    """Check if the value of arr1 is currently greater than the final value of arr2,
    and if the value of arr1 on the previous time step was less than or equal to
    the value of arr2.

    Args:
        arr1 (ndarray): First time series to check for a crossover.
        arr2 (ndarray): Second time series used as a reference for the crossover.
        delta (float, optional): A threshold value to add/subtract from arr2. Default is 0.

    Returns:
        bool: True if arr1 is currently above arr2 and was below or equal to it on the previous time step.
    """
    if isinstance(arr1, list):
        arr1 = np.array(arr1)

    if isinstance(arr2, list):
        arr2 = np.array(arr2)

    return np.where(arr1 > arr2 + delta, True, False)


def below(arr1: np.ndarray, arr2: np.ndarray, delta: float = 0):
    """Check if the value of arr1 is currently greater than the final value of arr2,
    and if the value of arr1 on the previous time step was less than or equal to
    the value of arr2.

    Args:
        arr1 (ndarray): First time series to check for a crossover.
        arr2 (ndarray): Second time series used as a reference for the crossover.
        delta (float, optional): A threshold value to add/subtract from arr2. Default is 0.

    Returns:
        bool: True if arr1 is currently above arr2 and was below or equal to it on the previous time step.
    """
    if isinstance(arr1, list):
        arr1 = np.array(arr1)

    if isinstance(arr2, list):
        arr2 = np.array(arr2)

    return np.where(arr1 < arr2 + delta, True, False)


def onband(
    arr1: np.ndarray,
    arr2: np.ndarray,
    band: tuple[float, float] = (0, 0)
) -> np.ndarray:
    """Check if the value of arr1 is currently greater than the final value of arr2,
    and if the value of arr1 on the previous time step was less than or equal to
    the value of arr2.

    Args:
        arr1 (ndarray): First time series to check for a crossover.
        arr2 (ndarray): Second time series used as a reference for the crossover.
        delta (float, optional): A threshold value to add/subtract from arr2. Default is 0.

    Returns:
        bool: True if arr1 is currently above arr2 and was below or equal to it on the previous time step.
    """
    if isinstance(arr1, list):
        arr1 = np.array(arr1)

    if isinstance(arr2, list):
        arr2 = np.array(arr2)

    return np.logical_and(
        arr1 <= arr2 + band[1],
        arr1 >= arr2 + band[0],
    )
