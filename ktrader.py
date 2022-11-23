import MetaTrader5 as mt5
from metadata import mt5_timeframe_book, mt5_order_type_book
from dataclasses import dataclass
from time import sleep
from datetime import datetime, timedelta


@dataclass
class KTrader():
    backtest_symbols: list[str] = None
    live_trading_symbols: list[str] = None
    __orders_updated: bool = False
    __open_orders: list[float] = None

    def start_session(self, login_settings: dict[str, str]) -> None:
        """Fucntion to start a Meta Trader 5 (MT5) session

        Args:
            login_settings (dict[str, str]): _description_

        Raises:
            ConnectionAbortedError: _description_
            PermissionError: _description_
        """
        # path = "C:\Program Files\MetaTrader 5\\terminal64.exe"  # TODO

        # Attempt to start MT5
        if not mt5.initialize(**login_settings):
            raise ConnectionAbortedError(f"Initialization Failed. {mt5.last_error()}")

        # unused params for login function
        login_settings.pop("path")
        login_settings.pop("portable")

        # Login to MT5. If you don’t do login, you’ll find that there will be times
        # when your script will suddenly fail to pull data, for no discernable reason.
        if not mt5.login(**login_settings):
            raise PermissionError(f"Login failed. {mt5.last_error()}")
        return

    def initialize_symbols(self, my_symbols: list[str]) -> None:
        """Function to initialize a symbol on MT5

        Args:
            my_symbols (list[str]): _description_

        Raises:
            ValueError: _description_
            ValueError: _description_
        """
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

    def place_order(
        self,
        order_type: str,
        symbol: str,
        volume: float,
        price: float,
        stop_loss: float,
        take_profit: float,
        comment: str = "No comment"
    ) -> None:
        """Create a new order on MetaTrader5

        Args:
            order_type (str): "SELL_STOP" or "BUY_STOP"
            symbol (str): Ticker name to purchase/sell
            volume (float): Volume of the ticker to purchase/sell
            price (float): The unitarium price to purchase/sell each stock
            stop_loss (float): #TODO
            take_profit (float): #TODO
            comment (str, optional): Add a comment if you need it. Defaults to "No comment".

        Returns:
            _type_: _description_
        """
        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type_book[order_type],
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

    def cancel_order(self, order_number: int) -> bool:
        """_summary_

        Args:
            order_number (int): _description_

        Returns:
            bool: _description_
        """
        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": order_number,
            "comment": "Order Removed"
        }
        # Send order to MT5
        order_result = mt5.order_send(request)
        return order_result

    def modify_position(
        self,
        order_number: int,
        symbol: str,
        new_stop_loss: float,
        new_take_profit: float,
    ) -> bool:
        """Function to modify an open position

        Args:
            order_number (int): _description_
            symbol (str): _description_
            new_stop_loss (float): _description_
            new_take_profit (float): _description_

        Returns:
            bool: _description_
        """
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

    def query_historic_data(self, symbol: str, timeframe: str, number_of_candles: int):
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

    def get_open_orders(self) -> list[dict[str, int]]:
        if not self.__open_orders and not self.__orders_updated:
            self.__open_orders = [order[0] for order in mt5.orders_get()]
            self.__orders_updated = True
        return self.__open_orders

    # Function to retrieve all open positions

    def get_open_positions(self):
        # Get position objects
        positions = mt5.positions_get()
        # Return position objects
        return positions

    def __is_active(self) -> bool:
        return datetime.now() < self.__active_upto

    def run(self) -> None:
        """_summary_
        """
        # Select symbol to run strategy on
        symbol_for_strategy = self.live_trading_symbols[0]  # TODO: parallel computing with all symbols
        # Set up a previous time variable
        previous_time = 0
        # Set up a current time variable
        current_time = 0
        # Start a while loop to poll MT5
        while self.__is_active():
            # Retrieve the current candle data
            candle_data = self.query_historic_data(
                symbol=symbol_for_strategy,
                timeframe=self.timeframe,
                number_of_candles=1
            )
            # Extract the timedata
            current_time = candle_data[0][0]
            # Compare against previous time
            if current_time != previous_time:
                # Notify user #TODO Erase when tested
                print("New Candle")
                # Update previous time
                previous_time = current_time
                # Retrieve previous orders
                orders = self.get_open_orders()
                # Cancel orders
                for order in orders:
                    self.cancel_order(order)
                # Start strategy one on selected symbol
                # TODO strategy.strategy_one(symbol=symbol_for_strategy, timeframe=trading_settings['timeframe'], pip_size = trading_settings['pip_size'])
            else:
                # Get positions
                positions = self.get_open_positions()
                # Pass positions to update_trailing_stop
                # for position in positions:
                #    strategy.update_trailing_stop(order=position, trailing_stop_pips=10, pip_size=trading_settings['pip_size'])
            sleep(0.1)
