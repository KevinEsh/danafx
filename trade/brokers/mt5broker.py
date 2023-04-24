import MetaTrader5 as mt5
from pytz import timezone
from numpy import recarray
from datetime import datetime
from dataclasses import dataclass
from pandas import DataFrame, to_datetime

from trade.brokers.abstract import BrokerSession
from trade.metadata import OrderTypes, TimeFrames, InverseOrderTypes


@dataclass
class Mt5Session(BrokerSession):

    def start_session(self, login_settings: dict[str, str]) -> None:
        """Start a Meta Trader 5 (MT5) session

        Args:
            login_settings (dict[str, str]): _description_

        Raises:
            ConnectionAbortedError: _description_
            PermissionError: _description_
        """
        # Attempt to start MT5
        if not mt5.initialize(**login_settings):
            raise ConnectionAbortedError(
                f"Initialization Failed. {mt5.last_error()}")

        # unused params for login function
        login_settings.pop("path")
        login_settings.pop("portable")

        # Login to MT5. If you don’t do login, you’ll find that there will be times
        # when your script will suddenly fail to pull data, for no discernable reason.
        if not mt5.login(**login_settings):
            raise PermissionError(f"Login failed. {mt5.last_error()}")

        self.account_info = mt5.account_info()  # ._asdict() TODO
        # self.leverage = self.account_info.leverage
        # self.balance = self.account_info.balance
        # self.account_currency = self.account_info.currency

        return

    def enable_symbols(self, symbols: list[str]) -> None:
        """Function to initialize a symbol on MT5

        Args:
            my_symbols (list[str]): _description_

        Raises:
            ValueError: _description_
            ValueError: _description_
        """
        # Get a list of all symbols supported in MT5
        self.symbols = symbols
        all_symbols = [symbol.name for symbol in mt5.symbols_get()]

        # Check each symbol in symbol_array to ensure it exists
        nonexistent_symbols = set(self.symbols) - set(all_symbols)
        if nonexistent_symbols:
            raise ValueError(f"Symbols {nonexistent_symbols} do not exist")

        # If exists, switch it on
        for real_symbol in self.symbols:
            if not mt5.symbol_select(real_symbol, True):
                raise RuntimeError(f"Unable to switch {real_symbol} on")

        return

    def create_order(
        self,
        symbol: str,
        order_type: str,
        price: float,
        lot_size: float,
        stop_loss: float,
        take_profit: float,
        deviation: int = 10,
    ) -> mt5.TradeOrder:
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
        # if not self.symbols_info.get(symbol):
        #     raise ValueError(f"Symbol {symbol} not initilized")

        if order_type not in OrderTypes._member_names_:
            raise ValueError(
                f"{order_type=} not supported. Must be {OrderTypes._member_names_}")

        # Find the filling mode of symbol
        order_type = OrderTypes[order_type]
        symbol_info = mt5.symbol_info(symbol)
        # filling_type = symbol_info.filling_mode #TODO: averiguar como funciona esta wea

        if not price:
            if order_type == OrderTypes.SELL:
                # maximum price that a buyer is willing to pay for a share
                open_price = symbol_info.bid
            elif order_type == OrderTypes.BUY:
                # minimum price that a seller is willing to take for that same share
                open_price = symbol_info.ask
            else:
                open_price = (symbol_info.ask + symbol_info.bid) / 2
        else:
            open_price = price

        digits = symbol_info.digits
        # spread = symbol_info.spread
        # micro_lot = symbol_info.volume_step
        # lot_size = micro_lot * lot_units
        # volume_min = symbol_info.volume_min
        # volume_max = symbol_info.volume_max

        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "type": order_type.value,
            "price": round(open_price, digits),
            "volume": round(lot_size, 2),
            "sl": round(stop_loss, digits),
            "tp": round(take_profit, digits),
            "deviation": deviation,
            # The order stays in the queue until it is manually canceled
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,  # mt5.ORDER_FILLING_IOC,
            "comment": f"open {order_type.name.lower()} {symbol}",
        }

        # Send the order to MT5
        order_result = mt5.order_send(request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(
                f"Error creating order. Code: {order_result.retcode}, details: {order_result.comment}")

        return mt5.orders_get(symbol=symbol)

    def close_position(
        self,
        position: mt5.TradePosition,
        deviation: int = 10,
    ):
        symbol_info = mt5.symbol_info_tick(position.symbol)
        order_type = OrderTypes._value2member_map_[position.type]
        inv_order_type = InverseOrderTypes[order_type.name]

        if order_type == OrderTypes.SELL:
            # maximum price that a buyer is willing to pay for a share
            close_price = symbol_info.bid
        elif order_type == OrderTypes.BUY:
            # minimum price that a seller is willing to take for that same share
            close_price = symbol_info.ask
        else:
            close_price = (symbol_info.ask + symbol_info.bid) / 2

        # Create the inverse request
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": inv_order_type.value,
            "price": close_price,
            "deviation": deviation,
            # The order stays in the queue until it is manually canceled
            "type_time": mt5.ORDER_TIME_GTC,
            # Fill or kill means that the order must be filled completely or canceled immediately
            "type_filling": mt5.ORDER_FILLING_IOC,
            "comment": f"close {order_type.name.lower()} {position.symbol}",
        }

        # Send the order to MT5
        order_result = mt5.order_send(close_request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(
                f"Error closing position. Code {order_result.retcode}, details: {order_result.comment}")

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
            raise RuntimeError(
                f"Error canceling order. Code {order_result.retcode}, Details: {order_result.comment}")

        return order_result

    def modify_position(
        self,
        position: mt5.TradePosition,
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
            "position": position.ticket,
            "symbol": position.symbol,
            "sl": new_stop_loss,
            "tp": new_take_profit,
        }

        # Send order to MT5
        order_result = mt5.order_send(request)

        # Notify based on return outcomes
        if order_result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(
                f"Error modifying position. Code {order_result.retcode}, details: {order_result.comment}")

        return order_result

    def get_positions(
        self,
        symbol: str = None,
    ) -> tuple[mt5.TradePosition]:
        return mt5.positions_get(symbol=symbol)

    def total_positions(
        self,
        symbol: str = None,
    ) -> tuple[mt5.TradePosition]:
        if not symbol:
            return mt5.positions_total()
        else:
            return len(self.get_positions(symbol))

    def get_orders(
        self,
        symbol: str
    ) -> tuple[mt5.TradeOrder]:
        # Function to retrieve all open orders from MT5
        return mt5.orders_get(symbol=symbol)

    def total_orders(
        self,
        symbol: str = None,
    ) -> tuple[mt5.TradePosition]:
        if not symbol:
            return mt5.orders_total()
        else:
            return len(self.get_orders(symbol))

    def get_ticks(
        self,
        symbol: str,
        n_ticks: int,
        as_dataframe: bool = False,
        format_time: bool = False,
        tzone: str = "US/Central",
    ) -> DataFrame:
        """Extract n ticks before now

        Args:
            symbol (str): Symbol to extract data
            n_ticks (int): Number of ticks retrieved before now
            tzone (str, optional): Convert the datetime to specific timezone. Defaults to "US/Central".

        Returns:
            DataFrame: All ticks data transformed into DataFrame
        """
        # Compute now date
        from_date = datetime.now()

        # Extract n Ticks before now
        ticks = mt5.copy_ticks_from(
            symbol, from_date, n_ticks,  mt5.COPY_TICKS_ALL)

        if not as_dataframe:
            return ticks.view(recarray)

        # Transform Tuple into a DataFrame
        df_ticks = DataFrame(ticks)

        # Convert number format of the date into date format
        if format_time:
            cst = timezone(tzone)
            df_ticks["time"] = to_datetime(
                df_ticks["time_msc"], unit="ms", utc=True)
            df_ticks["time"] = df_ticks["time"].dt.tz_convert(cst)

        return df_ticks.set_index("time")

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        n_candles: int,
        from_candle: int = 0,
        as_dataframe: bool = False,
        format_time: bool = False,
        tzone: str = "US/Central"
    ) -> DataFrame:
        """Query previous candlestick data from symbol. Convert the data into DataFrame

        Args:
            symbol (_type_): _description_
            timeframe (_type_): _description_
            n_candles (_type_): _description_

        Returns:
            _type_: _description_
        """
        mt5_tf = TimeFrames[timeframe].value

        # Extract n Candles before now
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, from_candle, n_candles)

        if not as_dataframe:
            return rates.view(recarray)

        # Transform Tuple into a DataFrame
        df_rates = DataFrame(rates)

        # Convert number format of the date into date format
        if format_time:
            cst = timezone(tzone)
            df_rates['time'] = to_datetime(
                df_rates['time'], unit='s', utc=True)
            df_rates['time'] = df_rates['time'].dt.tz_convert(cst)

        return df_rates.set_index("time")

    def get_exchange_rate(self, symbol: str) -> float:
        base_currency = symbol[3:]
        if base_currency == self.account_info.currency:
            exchange_rate = 1.0
        else:
            m1 = TimeFrames["M1"].value
            exchange_symbol = self.account_info.currency + base_currency
            # exchange_rate = mt5.copy_rates_from_pos(exchange_symbol, m1, 0, 1)[0][1]  # open price
            exchange_rate = mt5.copy_rates_from_pos(
                exchange_symbol, m1, 0, 1)[0][3]  # low price

        return exchange_rate

    def get_pip_unit(self, symbol: str) -> float:
        """Calculate the value of a single pip for the given currency pair

        Args:
            symbol (str): Currency pair such as GBPUSD, USDJPY, etc.

        Returns:
            float: the value of a pip in that currency pair
        """
        base_currency = symbol[3:]
        if base_currency == "JPY":
            pip_unit = 0.01
        else:
            pip_unit = 0.0001  # For EUR/USD

        return pip_unit

    def calculate_sltp(
        self,
        symbol: str,
        order_type: str,
        price: float,
        pips: float,
        rr_ratio: float,
    ) -> tuple[float]:
        pip_amount = self.get_pip_unit(symbol) * pips

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
        risk_tolerance: float,
        rr_ratio: float,
    ) -> tuple[float]:
        balance = mt5.account_info().balance
        exchange_rate = self.get_exchange_rate(symbol)
        # margin_free = mt5.account_info().margin_free
        pip_amount = risk_tolerance * balance * \
            exchange_rate / (100_000 * lot_size)

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
        risk_tolerance: float = 0.01,
        reward_pct: float = 0.02,
    ) -> tuple[float]:
        """_summary_

        Args:
            order_type (str): _description_
            price (float): _description_
            risk_tolerance (float, optional): _description_. Defaults to 0.01.
            reward_pct (float, optional): _description_. Defaults to 0.02.

        Returns:
            tuple[float]: _description_
        """
        # Find the TP and SL threshold in absolute price
        if order_type == 'buy':
            # Compute the variations in absolute price
            take_profit = price * (1 + reward_pct / self.leverage)
            stop_loss = price * (1 - risk_tolerance / self.leverage)
        elif order_type == mt5.ORDER_TYPE_SELL:
            # Compute the variations in absolute price
            take_profit = price * (1 - reward_pct / self.leverage)
            stop_loss = price * (1 + risk_tolerance / self.leverage)
        else:
            take_profit = 0.0
            stop_loss = 0.0

        return stop_loss, take_profit

    def calc_risk_params(
        self,
        symbol: str,
        order_type: str,
        pips: int,
        risk_tolerance: float,
        rr_ratio: float,
    ) -> tuple[float]:
        """Calculates the price, lot size, stop loss and take profit based on the
        account balance, risk tolerance, pips until hit a stop loss, and risk reward ratio

        Args:
            symbol (str): Currency pair ticker
            order_type (str): Type could be "buy" or "sell"
            pips (int): The distance in pips between the entry price and the stop loss price.
            risk_tolerance (float): The percentage of account balance that can be risked on a single trade.
            rr_ratio (float): Risk/Reward radio between stop loss & take profit thresholds

        Returns:
            tuple[float]: price, lot_size, stop_loss, take_profit
        """
        # Calculate the maximum amount that can be risked on a single trade
        symbol_info = mt5.symbol_info(symbol)
        balance = mt5.account_info().balance
        max_risk_amount = balance * risk_tolerance

        # Calculate the amount in pips to be risked
        pip_amount = self.get_pip_unit(symbol) * pips

        # Calculate the proper lot_size based on the risked_amount and the pip_amount
        exchange_rate = self.get_exchange_rate(symbol)
        lot_size = max_risk_amount * exchange_rate / (100_000. * pip_amount)

        # Delimit lot size by the min and max allowed amount
        if lot_size < symbol_info.volume_min:
            lot_size = symbol_info.volume_min
        elif lot_size > symbol_info.volume_max:
            lot_size = symbol_info.volume_max

        # Calculate stop loss & take profit based on the risk/reward ratio and current bid-ask price
        order_type = OrderTypes[order_type]
        if order_type == OrderTypes.BUY:
            # ask is the minimum price that a seller is willing to take for that same share
            open_price = symbol_info.ask
            take_profit = open_price + rr_ratio * pip_amount
            stop_loss = open_price - pip_amount
        elif order_type == OrderTypes.SELL:
            # bid is the maximum price that a buyer is willing to pay for a share
            open_price = symbol_info.bid
            take_profit = open_price - rr_ratio * pip_amount
            stop_loss = open_price + pip_amount

        # If pip amount is zero, do not put any stop loss or take profit. This can be achieved by:
        if pip_amount == 0.0:
            take_profit = 0.0
            stop_loss = 0.0

        return open_price, lot_size, stop_loss, take_profit


if __name__ == "__main__":
    from setup import get_settings
    login_settings = get_settings("settings/demo/login.json")
    trading_settings = get_settings("settings/demo/trading.json")

    mt5_login_settings = login_settings["mt5_login"]

    session = BrokerSession()

    # Start MT5
    session.start_session(mt5_login_settings)
    session.initialize_symbols(["EURUSD"])
    session.get_candles("EURUSD", "M1", 1)
    # o = session.create_order("BCHUSD", "SELL", 1, 137.00, 126.70)
    # print(o)

    # sleep(5)
    # session.close_position(o)
