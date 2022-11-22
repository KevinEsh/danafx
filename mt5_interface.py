import MetaTrader5 as mt5
from timeframe_info import mt5_timeframe_book


# Function to start Meta Trader 5 (MT5)
def start_session(login_settings: dict[str, str]) -> bool:
    # path = "C:\Program Files\MetaTrader 5\\terminal64.exe"  # TODO

    # Attempt to start MT5
    if not mt5.initialize(**login_settings):
        raise ConnectionAbortedError(f"Initialization Failed. {mt5.last_error()}")

    # unused params for login function
    login_settings.pop("path")
    login_settings.pop("portable")

    # Login to MT5. If you don’t do login, you’ll find that there will be times when your script will suddenly fail to pull data, for no discernable reason.

    if not mt5.login(**login_settings):
        raise PermissionError(f"Login failed. {mt5.last_error()}")

    print(mt5.terminal_info()._asdict())

    return


# Function to initialize a symbol on MT5
def initialize_symbols(my_symbols: list[str]) -> None:
    # Get a list of all symbols supported in MT5
    all_symbols = [symbol.name for symbol in mt5.symbols_get()]  # TODO: crear cache

    # Check each symbol in symbol_array to ensure it exists
    nonexistent_symbols = set(my_symbols) - set(all_symbols)
    if nonexistent_symbols:
        raise ValueError(f"Sybmols {nonexistent_symbols} do not exist")

     # If it exists, enable it
    for provided_symbol in my_symbols:
        if not mt5.symbol_select(provided_symbol, True):
            raise ValueError(f"Unable to enable symbol {provided_symbol}")
    return


# Function to place a trade on MT5
def place_order(
        order_type: str,
        symbol: str,
        volume: float,
        price: float,
        stop_loss: float,
        take_profit: float,
        comment: str = "No comment"
) -> None:
    # If order type SELL_STOP
    if order_type == "SELL_STOP":
        order_type = mt5.ORDER_TYPE_SELL_STOP
    elif order_type == "BUY_STOP":
        order_type = mt5.ORDER_TYPE_BUY_STOP
    # Create the request
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": round(price, 3),
        "sl": round(stop_loss, 3),
        "tp": round(take_profit, 3),
        "type_filling": mt5.ORDER_FILLING_RETURN,
        "type_time": mt5.ORDER_TIME_GTC,
        "comment": comment
    }
    # Send the order to MT5
    order_result = mt5.order_send(request)
    # Notify based on return outcomes
    if order_result[0] == 10009:
        print(f"Order for {symbol} successful")
    else:
        print(f"Error placing order. ErrorCode {order_result[0]}, Error Details: {order_result}")
    return order_result


# Function to cancel an order
def cancel_order(order_number: int) -> bool:
    # Create the request
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order_number,
        "comment": "Order Removed"
    }
    # Send order to MT5
    order_result = mt5.order_send(request)
    return order_result


# Function to modify an open position
def modify_position(order_number: int, symbol: str, new_stop_loss: float, new_take_profit: float) -> bool:
    # Create the request
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "sl": new_stop_loss,
        "tp": new_take_profit,
        "position": order_number
    }
    # Send order to MT5
    order_result = mt5.order_send(request)
    return order_result[0] == 10009


# Function to query previous candlestick data from MT5
def query_historic_data(symbol: str, timeframe: str, number_of_candles: int):
    """Convert the timeframe into an MT5 friendly format

    Args:
        symbol (_type_): _description_
        timeframe (_type_): _description_
        number_of_candles (_type_): _description_

    Returns:
        _type_: _description_
    """
    mt5_timeframe = mt5_timeframe_book[timeframe]
    # Retrieve data from MT5
    rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 1, number_of_candles)
    return rates


# Function to retrieve all open orders from MT5
def get_open_orders():
    orders = mt5.orders_get()
    order_array = []
    for order in orders:
        order_array.append(order[0])
    return order_array


# Function to retrieve all open positions
def get_open_positions():
    # Get position objects
    positions = mt5.positions_get()
    # Return position objects
    return positions
