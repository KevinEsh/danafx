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

        self.account_info = mt5.account_info() #._asdict() TODO
        self.leverage = self.account_info.leverage
        self.balance = self.account_info.balance
        self.account_currency = self.account_info.currency

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

        # If exists, switch it on
        for real_symbol in symbols:
            if not mt5.symbol_select(real_symbol, True):
                raise RuntimeError(f"Unable to switch {real_symbol} on")
            #TODO: self.symbols_info[real_symbol] = mt5.symbol_info(real_symbol)
        return

    def create_market_order(
        self,
        symbol: str,
        order_type: str,
        lot_units: int,
        stop_loss: float,
        take_profit: float,
        deviation: int = 10,
    ) -> None:
        """Create a new market order. This new order will be transactioned almost immidiately

        Args:
            symbol (str): Asset name to buy/sell
            order_type (str): "SELL" or "BUY"
            lot_units (float): Number of micro lots to buy/sell. Acknowledge 0.01 standard lot is a micro lot 
            stop_loss (float): Price at which the position will automatically exit with defined losses
            take_profit (float): Price at which the position will automatically exit with defined gains
            deviation (int): Number of pips to miss if the price order is not fulfilled

        Returns:
            mt5.OrderSendResult: _description_
        """
        if not self.symbols_info.get(symbol):
            raise ValueError(f"Symbol {symbol} not initilized")
        
        if order_type not in ORDER_TYPES_BOOK:
            raise ValueError("action must be 'buy' or 'sell'")

        # Find the filling mode of symbol
        symbol_info = mt5.symbol_info(symbol)
        # filling_type = symbol_info.filling_mode #TODO: averiguar como funciona esta wea

        if order_type == "sell":
            # maximum price that a buyer is willing to pay for a share
            open_price = symbol_info.bid
        else:
            # minimum price that a seller is willing to take for that same share
            open_price = symbol_info.ask 
        
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
            "type": ORDER_TYPES_BOOK[order_type],
            "price": round(open_price, digits),
            "sl": round(stop_loss, digits),
            "tp": round(take_profit, digits),
            "deviation": deviation,
            "type_filling": 1,  # filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
            "comment": f"open {order_type} for {symbol}",
        }

        # Send the order to MT5
        order_result = mt5.order_send(request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Error creating order. Code: {order_result.retcode}, details: {order_result.comment}")

        print(f"Successfully order created {symbol}")
        # TODO: crear un algoritmo que sume estas ordenes a una mini-cache
        return order_result

    def close_position(
        self,
        position: object,
        # price: float,
        deviation: int = 10,
    ):
        # Create the inverse request
        open_request = position.request
        close_price = mt5.symbol_info_tick(open_request.symbol).bid

        close_request = {
            "action": open_request.action, #TODO: Revisar si esta wea no ocasiona un bug
            "position": position.order,
            "symbol": open_request.symbol,
            "volume": position.volume,
            "type": INV_ORDER_TYPES_BOOK[open_request.type],
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
            raise RuntimeError(f"Error closing position. Code {order_result.retcode}, details: {order_result.comment}")

        print(f"Successfully position closed {open_request.symbol}")
        return order_result

    def cancel_order(self, order: mt5.OrderSendResult) -> bool:
        """Cancel an order which hasn't been taking place

        Args:
            order_number (int): _description_

        Returns:
            bool: _description_
        """
        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": order.order,
            "comment": f"cancel {order.symbol}"
        }

        # Send order to MT5
        order_result = mt5.order_send(request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Error closing order. Code {order_result.retcode}, Details: {order_result.comment}")

        print(f"Successfully order closed {order.symbol}")
        return order_result

    def modify_position(
        self,
        order: int,
        new_stop_loss: float = None,
        new_take_profit: float = None,
    ) -> bool:
        """Modify an open position with new stop_loss and take_profit

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
            raise RuntimeError(f"Error modifying position. Code {order_result.retcode}, details: {order_result.comment}")

        print(f"Successfully order closed {order_result.symbol}")
        return order_result

    def get_ticks(
        self,
        symbol: str,
        number_of_ticks: int,
        format_time: bool = True,
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

        # Extract n Ticks before now
        ticks = mt5.copy_ticks_from(symbol, from_date, number_of_ticks,  mt5.COPY_TICKS_ALL)

        # Transform Tuple into a DataFrame
        df_ticks = DataFrame(ticks)

        # Convert number format of the date into date format
        if format_time:
            cst = timezone(tzone)
            df_ticks["time"] = to_datetime(df_ticks["time_msc"], unit="ms", utc=True)
            df_ticks["time"] = df_ticks["time"].dt.tz_convert(cst)

        return df_ticks.set_index("time")

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        number_of_candles: int,
        format_time: bool = False,
        tzone: str = "US/Central"
    ) -> DataFrame:
        """Query previous candlestick data from symbol. Convert the data into DataFrame

        Args:
            symbol (_type_): _description_
            timeframe (_type_): _description_
            number_of_candles (_type_): _description_

        Returns:
            _type_: _description_
        """
        mt5_timeframe = TIMEFRAMES_BOOK[timeframe]

        # Extract n Candles before now
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, number_of_candles)

        # Transform Tuple into a DataFrame
        df_rates = DataFrame(rates)

        # Convert number format of the date into date format
        if format_time:
            cst = timezone(tzone)
            df_rates['time'] = to_datetime(df_rates['time'], unit='s', utc=True)
            df_rates['time'] = df_rates['time'].dt.tz_convert(cst)

        return df_rates.set_index("time")

    def get_open_orders(self) -> list[dict[str, int]]:
        # Function to retrieve all open orders from MT5
        # if not self._open_orders and not self.__orders_updated:
        #     self._open_orders = {order[0]: order for order in mt5.orders_get()}
        #     self._orders_updated = True
        # return self._open_orders
        return mt5.orders_total()

    def get_open_positions(self):
        # Function to retrieve all open positions
        # Get position objects
        self.positions = mt5.positions_get()
        # Return position objects
        return self.positions

    def get_exchange_rate(self, symbol: str) -> float:
        base_currency = symbol[3:]
        if base_currency == self.account_currency:
            exchange_rate = 1.
        else:
            m1 = TIMEFRAMES_BOOK["M1"]
            exchange_symbol = base_currency + self.account_currency
            exchange_rate = mt5.copy_rates_from_pos(exchange_symbol, m1, 0, 1).open

        return exchange_rate
    
    def get_pipvalue(self, symbol: str) -> float:
        base_currency = symbol[3:]
        if base_currency == "JPY":
            pip_value = 0.01
        else:
            pip_value = 0.0001

        return pip_value
        
    def calculate_sltp(
        self,
        symbol: str,
        order_type: str,
        price: float,
        pips: float,
        rr_ratio: float,
    ) -> tuple[float]:
        pip_amount = self.get_pipvalue(symbol) * pips
        
        if order_type == "buy":
            take_profit = price + rr_ratio * pip_amount
            stop_loss = price - pip_amount
        elif order_type == "sell":
            take_profit = price - rr_ratio * pip_amount
            stop_loss = price + pip_amount
        else:
            take_profit = 0.0
            stop_loss = 0.0

        return stop_loss, take_profit

    def calculate_sltp_2(
        self,
        symbol: str,
        order_type: str,
        price: float,
        lot_size: float,
        risk_pct: float,
        rr_ratio: float,
    ) -> tuple[float]:
        exchange_rate = self.get_exchange_rate(symbol)
        pip_amount = risk_pct * self.balance * lot_size * exchange_rate / (100_000 * lot_size)

        if order_type == "buy":
            take_profit = price + rr_ratio * pip_amount
            stop_loss = price - pip_amount
        elif order_type == "sell":
            take_profit = price - rr_ratio * pip_amount
            stop_loss = price + pip_amount
        else:
            take_profit = 0.0
            stop_loss = 0.0

        return stop_loss, take_profit
            

    def calculate_sltp_3(
            self,
            order_type: str,
            price: float,
            risk_pct: float = 0.01,
            reward_pct: float = 0.02,
    ) -> tuple[float]:
        # Find the TP and SL threshold in absolute price
        if order_type == 'buy':
            # Compute the variations in absolute price
            take_profit = price * (1 + reward_pct / self.leverage)
            stop_loss = price * (1 - risk_pct / self.leverage)
        elif order_type == mt5.ORDER_TYPE_SELL:
            # Compute the variations in absolute price
            take_profit = price * (1 - reward_pct / self.leverage)
            stop_loss = price * (1 + risk_pct / self.leverage)
        else:
            take_profit = 0.0
            stop_loss = 0.0

        return stop_loss, take_profit


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
    session.get_candles("EURUSD", "M1", 1)
    # o = session.create_order("BCHUSD", "SELL", 1, 137.00, 126.70)
    # print(o)

    # sleep(5)
    # session.close_position(o)
