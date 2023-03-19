import MetaTrader5 as mt5
from pytz import timezone
from datetime import datetime
from dataclasses import dataclass
from pandas import DataFrame, to_datetime
from metadata import ORDER_TYPES_BOOK, TIMEFRAMES_BOOK, INV_ORDER_TYPES_BOOK


@dataclass
class BrokerSession():

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

        self.leverage = mt5.account_info().leverage

        return

    def initialize_symbols(self, symbols: list[str]) -> None:
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
        nonexistent_symbols = set(symbols) - set(all_symbols)
        if nonexistent_symbols:
            raise ValueError(f"Symbols {nonexistent_symbols} do not exist")

        # If it exists, enable it
        for provided_symbol in symbols:
            if not mt5.symbol_select(provided_symbol, True):
                raise ValueError(f"Unable to enable symbol {provided_symbol}")
        return

    def create_order(
        self,
        symbol: str,
        ordtype: str,
        lot_units: int,
        stop_loss: float,
        take_profit: float,
        deviation: int = 10,
    ) -> None:
        """Create a new order on MetaTrader5

        Args:
            symbol (str): Ticker name to purchase/sell
            order_type (str): "SELL_STOP" or "BUY_STOP"
            lot_units (float): Volume of the ticker to purchase/sell
            price (float): The unitarium price to purchase/sell each stock
            stop_loss (float): #TODO
            take_profit (float): #TODO
            comment (str, optional): Add a comment if you need it. Defaults to "No comment".

        Returns:
            _type_: _description_
        """

        # Find the filling mode of symbol #TODO
        symbol_info = mt5.symbol_info(symbol)
        order_type = ORDER_TYPES_BOOK[ordtype]

        filling_type = symbol_info.filling_mode
        open_price = symbol_info.bid
        digits = symbol_info.digits
        # spread = symbol_info.spread
        micro_lot = symbol_info.volume_step
        lot_size = micro_lot * lot_units
        # volume_min = symbol_info.volume_min
        # volume_max = symbol_info.volume_max

        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": round(open_price, digits),
            "sl": round(stop_loss, digits),
            "tp": round(take_profit, digits),
            "deviation": deviation,
            "type_filling": 1,  # filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
            "comment": f"open {symbol}",
        }

        # Send the order to MT5
        order_result = mt5.order_send(request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Error creating order. Error Code: {order_result.retcode}, Error Details: {order_result.comment}")
            return

        print(f"Successfully order created {symbol}")
        # TODO: crear un algoritmo que sume estas ordenes a una mini-cache
        return order_result

    def close_position(
        self,
        order: object,
        # price: float,
        deviation: int = 10,
    ):
        # Create the inverse request
        open_request = order.request
        close_price = mt5.symbol_info_tick(open_request.symbol).bid
        order_type = mt5.ORDER_TYPE_BUY if open_request.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL

        close_request = {
            "position": order.order,
            "action": open_request.action,
            "symbol": open_request.symbol,
            "volume": order.volume,
            "type": order_type,
            "price": close_price,
            "deviation": deviation,
            "type_filling": open_request.type_filling,
            "type_time": open_request.type_time,
            "comment": f"close {open_request.symbol}",
        }

        # Send the order to MT5
        order_result = mt5.order_send(close_request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Error closing order. Error code {open_request.retcode}, Error details: {order_result.comment}")
            return

        print(f"Successfully order closed {open_request.symbol}")
        return order_result

    def cancel_order(self, order: int) -> bool:
        """Function to cancel an order

        Args:
            order_number (int): _description_

        Returns:
            bool: _description_
        """
        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": order.order,
            "comment": f"remove {order.symbol}"
        }
        # Send order to MT5
        order_result = mt5.order_send(request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Error closing order. Error Code {order_result.retcode}, Error Details: {order_result}")
            return

        print(f"Successfully order closed {order.symbol}")
        return order_result

    def modify_position(
        self,
        order: int,
        new_stop_loss: float = None,
        new_take_profit: float = None,
    ) -> bool:
        """Function to modify an open position

        Args:
            order (int): _description_
            symbol (str): _description_
            new_stop_loss (float): _description_
            new_take_profit (float): _description_

        Returns:
            bool: _description_
        """
        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": order.order,
            "symbol": order.symbol,
            "sl": new_stop_loss,
            "tp": new_take_profit,
        }
        # Send order to MT5
        order_result = mt5.order_send(request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Error closing order. Error Code {order_result.retcode}, Error Details: {order_result}")

        print(f"Successfully order closed {order_result.symbol}")
        return order_result

    def get_ticks(
        self,
        symbol: str,
        number_of_ticks: int,
        tzone: str = "US/Central",
    ) -> DataFrame:
        """Extract n ticks before now

        Args:
            symbol (str): Symbol to extract data
            number_of_ticks (int): Number of ticks retrieved before now
            tzone (str, optional): Convert the datetime to specific timezone. Defaults to "US/Central".

        Returns:
            DataFrame: All ticks data transformed into DataFrame
        """
        # Compute now date
        from_date = datetime.now()
        cst = timezone(tzone)

        # Extract n Ticks before now
        ticks = mt5.copy_ticks_from(symbol, from_date, number_of_ticks,  mt5.COPY_TICKS_ALL)

        # Transform Tuple into a DataFrame
        df_ticks = DataFrame(ticks)

        # Convert number format of the date into date format
        df_ticks["time"] = to_datetime(df_ticks["time"], unit="s", utc=True)
        df_ticks['time'] = df_ticks['time'].dt.tz_convert(cst)

        return df_ticks.set_index("time")

    def get_candles(
            self,
            symbol: str,
            timeframe: str,
            number_of_candles: int,
            tzone: str = "US/Central"
    ) -> DataFrame:
        """Query previous candlestick data from MT5. Convert the data into DataFrame

        Args:
            symbol (_type_): _description_
            timeframe (_type_): _description_
            number_of_candles (_type_): _description_

        Returns:
            _type_: _description_
        """
        mt5_timeframe = TIMEFRAMES_BOOK[timeframe]
        cst = timezone(tzone)

        # Extract n Candles before now
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, number_of_candles)

        # Transform Tuple into a DataFrame
        df_rates = DataFrame(rates)

        # Convert number format of the date into date format
        df_rates['time'] = to_datetime(df_rates['time'], unit='s', utc=True)
        df_rates['time'] = df_rates['time'].dt.tz_convert(cst)

        return df_rates.set_index("time")

    def get_open_orders(self) -> list[dict[str, int]]:
        # Function to retrieve all open orders from MT5
        # if not self._open_orders and not self.__orders_updated:
        #     self._open_orders = {order[0]: order for order in mt5.orders_get()}
        #     self._orders_updated = True
        # return self._open_orders
        print(mt5.orders_total())

    def get_open_positions(self):
        # Function to retrieve all open positions
        # Get position objects
        positions = mt5.positions_get()
        print(positions)
        # Return position objects
        return positions

    def calculate_best_price(
        self,
        symbol: str,
        order_type: str,
    ) -> float:
        symbol_info = mt5.symbol_
        if order_type == mt5.ORDER_TYPE_BUY:
            return mt5

    def calculate_risk_reward_thresholds(
            self,
            price: float,
            ordtype: str,
            risk_pct: float = 0.01,
            reward_pct: float = 0.02,
    ) -> tuple[float]:
        # Find the TP and SL threshold in absolute price
        if ordtype == mt5.ORDER_TYPE_BUY:
            # price = mt5.symbol_info(symbol).ask

            # Compute the variations in absolute price
            take_profit = price * (1 + reward_pct / self.leverage)
            stop_loss = price * (1 - risk_pct / self.leverage)

        elif ordtype == mt5.ORDER_TYPE_SELL:
            # price = mt5.symbol_info(symbol).bid

            # Compute the variations in absolute price
            take_profit = price * (1 - reward_pct / self.leverage)
            stop_loss = price * (1 + risk_pct / self.leverage)

        else:
            take_profit = 0.0
            stop_loss = 0.0

        return take_profit, stop_loss


if __name__ == "__main__":
    from setup import get_settings
    from time import sleep

    login_settings = get_settings("settings/demo/login.json")
    trading_settings = get_settings("settings/demo/trading.json")

    mt5_login_settings = login_settings["mt5_login"]

    session = BrokerSession()

    # Start MT5
    session.start_session(mt5_login_settings)
    session.initialize_symbols(["BCHUSD"])
    # o = session.create_order("BCHUSD", "SELL", 1, 137.00, 126.70)
    # print(o)

    # sleep(5)
    # session.close_position(o)
