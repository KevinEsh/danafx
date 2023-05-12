from numpy import ndarray


def crossingover(
    source1: ndarray,
    source2: ndarray,
    delta: float = 0
) -> bool:
    """Check if the final value of source1 is greater than the final value of source2
    #and if the value of source1 on the previous bar was less than or equal to
    the value of source2

    Args:
        source1 (ndarray): Source data that has to cross over from bottom to top
        source2 (ndarray): Source data to test crossing condition

    Returns:
        bool: Signal if the source1 crosses over source2
    """
    if (source1[-1] > source2[-1] + delta) and (source1[-2] <= source2[-2]):
        return True
    else:
        return False


def crossingunder(
    source1: ndarray,
    source2: ndarray,
    delta: float = 0,
) -> bool:
    """Check if the final value of source1 is greater than the final value of source2
    #and if the value of source1 on the previous bar was less than or equal to
    the value of source2

    Args:
        source1 (ndarray): Source data that has to cross over from bottom to top
        source2 (ndarray): Source data to test crossing condition

    Returns:
        bool: Signal if the source1 crosses under source2
    """
    if (source1[-1] < source2[-1] + delta) and (source1[-2] >= source2[-2]):
        return True
    else:
        return False
