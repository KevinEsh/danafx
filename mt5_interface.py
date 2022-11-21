import MetaTrader5


# Function to start Meta Trader 5 (MT5)
def start_mt5(login_settings: dict[str, str]) -> bool:
    path = "C:/Program Files/ICMarkets - MetaTrader 5/terminal64.exe" #TODO

    # Attempt to start MT5
    if not MetaTrader5.initialize(**login_settings, path=path):
        raise ConnectionAbortedError("MT5 Initialization Failed")
    print("Trading Bot Starting")

    # Login to MT5
    if not MetaTrader5.login(**login_settings):
        raise PermissionError("Login Fail")

    print("Trading Bot Logged in and Ready to Go!")
    return



# Function to initialize a symbol on MT5
def initialize_symbols(my_symbols: list[str]) -> None:
    # Get a list of all symbols supported in MT5
    all_symbols = [symbol.name for symbol in MetaTrader5.symbols_get()] #TODO: crear cache

    # Check each symbol in symbol_array to ensure it exists
    nonexistent_symbols = set(my_symbols) - set(all_symbols)
    if nonexistent_symbols:
        raise ValueError(f"Sybmols {nonexistent_symbols} do not exist")

     # If it exists, enable it
    for provided_symbol in my_symbols:
        if not MetaTrader5.symbol_select(provided_symbol, True):
            raise ValueError(f"Unable to enable symbol {provided_symbol}")
    return


# Function to place a trade on MT5
def place_order(order_type:str, symbol:str, volume, price, stop_loss, take_profit, comment):
    # If order type SELL_STOP
    if order_type == "SELL_STOP":
        order_type = MetaTrader5.ORDER_TYPE_SELL_STOP
    elif order_type == "BUY_STOP":
        order_type = MetaTrader5.ORDER_TYPE_BUY_STOP
    # Create the request
    request = {
        "action": MetaTrader5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": round(price, 3),
        "sl": round(stop_loss, 3),
        "tp": round(take_profit, 3),
        "type_filling": MetaTrader5.ORDER_FILLING_RETURN,
        "type_time": MetaTrader5.ORDER_TIME_GTC,
        "comment": comment
    }
    # Send the order to MT5
    order_result = MetaTrader5.order_send(request)
    # Notify based on return outcomes
    if order_result[0] == 10009:
        print(f"Order for {symbol} successful")
    else:
        print(f"Error placing order. ErrorCode {order_result[0]}, Error Details: {order_result}")
    return order_result


# Function to cancel an order
def cancel_order(order_number):
    # Create the request
    request = {
        "action": MetaTrader5.TRADE_ACTION_REMOVE,
        "order": order_number,
        "comment": "Order Removed"
    }
    # Send order to MT5
    order_result = MetaTrader5.order_send(request)
    return order_result


# Function to modify an open position
def modify_position(order_number, symbol, new_stop_loss, new_take_profit):
    # Create the request
    request = {
        "action": MetaTrader5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "sl": new_stop_loss,
        "tp": new_take_profit,
        "position": order_number
    }
    # Send order to MT5
    order_result = MetaTrader5.order_send(request)
    if order_result[0] == 10009:
        return True
    else:
        return False


# Function to convert a timeframe string in MetaTrader 5 friendly format
def set_query_timeframe(timeframe):
    # Implement a Pseudo Switch statement. Note that Python 3.10 implements match / case but have kept it this way for
    # backwards integration
    timeframe_dict = {
    "M1": MetaTrader5.TIMEFRAME_M1,
    "M2": MetaTrader5.TIMEFRAME_M2,
    "M3": MetaTrader5.TIMEFRAME_M3,
    "M4": MetaTrader5.TIMEFRAME_M4,
    "M5": MetaTrader5.TIMEFRAME_M5,
    "M6": MetaTrader5.TIMEFRAME_M6,
    "M10": MetaTrader5.TIMEFRAME_M10,
    "M12": MetaTrader5.TIMEFRAME_M12,
    "M15": MetaTrader5.TIMEFRAME_M15,
    "M20": MetaTrader5.TIMEFRAME_M20,
    "M30": MetaTrader5.TIMEFRAME_M30,
    "H1": MetaTrader5.TIMEFRAME_H1,
    "H2": MetaTrader5.TIMEFRAME_H2,
    "H3": MetaTrader5.TIMEFRAME_H3,
    "H4": MetaTrader5.TIMEFRAME_H4,
    "H6": MetaTrader5.TIMEFRAME_H6,
    "H8": MetaTrader5.TIMEFRAME_H8,
    "H12": MetaTrader5.TIMEFRAME_H12,
    "D1": MetaTrader5.TIMEFRAME_D1,
    "W1": MetaTrader5.TIMEFRAME_W1,
    "MN1": MetaTrader5.TIMEFRAME_MN1,
    }


# Function to query previous candlestick data from MT5
def query_historic_data(symbol, timeframe, number_of_candles):
    # Convert the timeframe into an MT5 friendly format
    mt5_timeframe = set_query_timeframe(timeframe)
    # Retrieve data from MT5
    rates = MetaTrader5.copy_rates_from_pos(symbol, mt5_timeframe, 1, number_of_candles)
    return rates


# Function to retrieve all open orders from MT5
def get_open_orders():
    orders = MetaTrader5.orders_get()
    order_array = []
    for order in orders:
        order_array.append(order[0])
    return order_array


# Function to retrieve all open positions
def get_open_positions():
    # Get position objects
    positions = MetaTrader5.positions_get()
    # Return position objects
    return positions
