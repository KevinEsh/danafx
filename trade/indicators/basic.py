
from talib import get_functions
from trade.indicators.metadata import __custom_indicators__, __unstable_indicators__


def get_all_indicators():
    """Get a list of all technical indicators from the TALib library and additional custom indicators.

    Returns:
        list: A list of strings representing the names of all technical indicators from the TALib library
        and additional custom indicators.
    """
    talib_indicators = get_functions()
    talib_indicators.extend(__custom_indicators__)
    return talib_indicators


def get_min_bars(indicator: str, window: int) -> int:
    """Calculate the minimal amount of bars to get at least one value from that indicator

    Args:
        indicator (str): Indicator name. Call `get_all_indicators` to see complete list
        window (int): Number of bar were the function is applied sequentialy

    Returns:
        int: minimum amount of bar that the indicator needs
    """
    if indicator not in get_all_indicators():
        ValueError(f"{indicator=} does not exist")

    # Indicator is stable. Window is enough for calculate precise values
    if indicator not in __unstable_indicators__:
        if indicator == "WT":
            return 2 * window + 12
        return window
    else:
        return 1


def get_stable_min_bars(indicator: str, window: int) -> int:
    """Get the minimum number of bars needed to calculate a stable value for a given technical indicator.

    Args:
        indicator (str): The name of the technical indicator to check.
        window (int): The number of bars to use for the indicator calculation.

    Returns:
        int: The minimum number of bars needed to calculate a stable value for the given technical indicator.

    Raises:
        ValueError: If the indicator does not exist in the TALib library or the custom indicators.
        NotImplementedError: If the indicator does not have a formula to calculate stable values.

    Notes:
        This function uses specific formulas for some technical indicators to calculate the minimum number
        of bars needed to obtain a stable value with an error less than 1e-4.
    """
    if indicator not in get_all_indicators():
        ValueError(f"{indicator=} does not exist")

    # Indicator is stable. Window is enough for calculate precise values
    if indicator not in __unstable_indicators__:
        return window

    # Calculate the min amount of bars needed to get a good aproximation i.e. <1e-4 error
    elif indicator == "RSI":
        return int((100. * window - 120.) ** (1./1.479))
    elif indicator == "EMA":
        return int((11.24 * window + 7.26) ** (1./1.2))
    elif indicator == "ATR":  # TODO: ATR uses EMA, check if below is true
        return int((11.24 * window + 7.26) ** (1./1.2)) + 1
    elif indicator == "ADX":
        return int((138.2 * window - 155.55) ** (1./1.53))
    elif indicator == "RQK":
        return 3500  # TODO: experimentar esta madre
    elif indicator == "RBFK":
        return 90  # TODO: confiable, pero mejor experimenta para cualquier ventana
    elif indicator == "WT":
        if 2 <= window <= 14:
            return int(2.36 * window + 61.51)
        else:
            return int((12.85 * window + 19.95) ** (1/1.173))
    else:
        NotImplementedError(
            f"{indicator=} has no formula to get stable values")


if __name__ == "__main__":
    from trade.brokers import Mt5Session
    from matplotlib.pyplot import plot, savefig
    from setup import get_settings

    # Import project settings
    login_settings = get_settings("settings/demo/login.json")
    # trading_settings = get_settings("settings/demo/trading.json")
    mt5_login_settings = login_settings["mt5_login"]

    trader = Mt5Session()
    trader.start_session(mt5_login_settings)
    trader.initialize_symbols(["EURUSD"])
    df = trader.query_historic_data("EURUSD", "M30", 2000)
    # df["hlc3"] = HLC3(df.high, df.low, df.close)
    # df["rsi"] = RSISmoothIndicator(df.close, fillna=False)
    # df["cci"] = CCISmoothIndicator(df.high, df.low, df.close, fillna=False)
    # df["wt"] = WaveTrendIndicator(df.hlc3, fillna=False)
    # df["adx"] = ADXSmoothIndicator(df.high, df.low, df.close, fillna=False)

    df["rqk"] = RQK(df.close)
    df["rbfk"] = RBFK(df.close)

    print(df[["close", "rbf", "rq"]])

    # plot(df[["rsi", "cci", "wt", "adx"]])
    plot(df[["close", "rbf", "rq"]].tail(100))
    savefig("test3.jpeg")
