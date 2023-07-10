import MetaTrader5 as mt5
from typing import Union
from pytz import timezone
from numpy import recarray
from datetime import datetime
from dataclasses import dataclass
from pandas import DataFrame, to_datetime

from trade.brokers.abstract import BrokerSession
from trade.metadata import OrderTypes, TimeFrames, InverseOrderTypes, CandleLike


def count_decimals(number: float) -> int:
    s = str(number)
    if '.' not in s:
        return 0
    return len(s) - s.index('.') - 1


def check_symbol(symbol):
    if len(symbol) != 6:
        raise ValueError(f"Invalid symbol format. Expected 'XXXYYY', got '{symbol}'")


def check_order_type(order_type: str):
    if order_type not in OrderTypes._member_names_:
        raise ValueError(
            f"{order_type=} not supported. Must be {OrderTypes._member_names_}")


def check_order_sent(order_result, action: str):
    if order_result.retcode != mt5.TRADE_RETCODE_DONE:
        raise RuntimeError(
            f"Error {order_result.retcode} while {action} order. {order_result.comment}")


def bound_lot(symbol: str,  lot_size: float) -> float:
    symbol_info = mt5.symbol_info(symbol)

    # Delimit lot size by the min and max allowed amount
    if lot_size < symbol_info.volume_min:
        return symbol_info.volume_min
    elif lot_size > symbol_info.volume_max:
        return symbol_info.volume_max
    else:
        step = symbol_info.volume_step
        return step * round(lot_size / step)


def get_pipette_unit(symbol: str) -> float:
    """Calculate the value of a single pip for the given currency pair.

    Args:
        symbol (str): Currency pair in the format of 'XXXYYY', such as 'GBPUSD', 'USDJPY', etc.
                    'XXX' is the base currency and 'YYY' is the quote currency.

    Returns:
        float: the value of a pip in that currency pair. For JPY pairs, it's usually 0.001. For most
            other pairs like EUR/USD, it's 0.00001.

    Raises:
        ValueError: If symbol is not of the format 'XXXYYY'.
    """
    check_symbol(symbol)

    base_currency = symbol[3:].upper()
    if base_currency == "JPY":
        return 0.001
    else:
        return 0.00001


def calculate_sltp(
    symbol: str,
    order_type: str,
    price: float,
    pipettes: float = None,
    rr_ratio: float = None,
) -> tuple[float]:
    # If pip amount is zero, do not put any stop loss or take profit. This can be achieved by:
    if not pipettes:
        return 0.0, 0.0

    # Calculate the amount in pips to be risked
    pip_amount = get_pipette_unit(symbol) * pipettes
    order_type = OrderTypes[order_type]

    if order_type == OrderTypes.BUY:
        # ask is the minimum price that a seller is willing to take for that same share
        stop_loss = price - pip_amount
        take_profit = price + rr_ratio * pip_amount if rr_ratio else 0.0
    elif order_type == OrderTypes.SELL:
        # bid is the maximum price that a buyer is willing to pay for a share
        stop_loss = price + pip_amount
        take_profit = price - rr_ratio * pip_amount if rr_ratio else 0.0

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

    def create_order(
        self,
        symbol: str,
        order_type: str,
        price: float,
        lot_size: float,
        stop_loss: float = None,
        take_profit: float = None,
        deviation: int = 5,
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
        check_symbol(symbol)
        check_order_type(order_type)

        symbol_info = mt5.symbol_info(symbol)
        price_digits = symbol_info.digits
        lot_digits = count_decimals(symbol_info.volume_step)

        order_type = OrderTypes[order_type]
        open_price = price if price != 0 else self.get_current_price(order_type)
        # filling_type = symbol_info.filling_mode #TODO: averiguar como funciona esta wea
        # spread = symbol_info.spread

        # Create the order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "type": order_type.value,
            "price": round(open_price, price_digits),
            "volume": round(lot_size, lot_digits),
            "deviation": deviation,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,  # mt5.ORDER_FILLING_IOC,
            # "comment": f"open {order_type.name.lower()} {symbol}", #TODO: como hacer el comentario menos inutil?
        }

        # Optional parameters
        if stop_loss is not None:
            request["sl"] = round(stop_loss, price_digits)
        if take_profit is not None:
            request["tp"] = round(take_profit, price_digits)

        # Send the order to MT5 and check the result
        order_result = mt5.order_send(request)
        check_order_sent(order_result, "creating")

        # The order stays in the queue until it is canceled
        return mt5.orders_get(symbol=symbol)  # TODO: cambiar esto por order_result

    def close_position(
        self,
        position: mt5.TradePosition,
        deviation: int = 5,
    ):
        order_type = OrderTypes._value2member_map_[position.type]
        inv_order_type = InverseOrderTypes[order_type.name]
        close_price = self.get_current_price(position.symbol, order_type)

        # Create the inverse request
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": inv_order_type.value,
            "price": close_price,
            "deviation": deviation,
            "type_time": mt5.ORDER_TIME_GTC,
            # Fill or kill means that the order must be filled completely or canceled immediately
            "type_filling": mt5.ORDER_FILLING_IOC,
            "comment": f"close {order_type.name.lower()} {position.symbol}",
        }

        # Send the order to MT5
        order_result = mt5.order_send(close_request)
        check_order_sent(order_result, "closing")

        # The order stays in the queue until it is canceled
        return order_result

    def cancel_order(self, order: mt5.OrderSendResult):
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
        check_order_sent(order_result, "canceling")

        # The order stays in the queue until it is canceled
        return order_result

    def modify_position(
        self,
        position: mt5.TradePosition,
        new_stop_loss: float = None,
        new_take_profit: float = None,
    ):
        """Modify an open position with new stop_loss and take_profit

        Args:
            order (int): _description_
            symbol (str): _description_
            new_stop_loss (float): _description_
            new_take_profit (float): _description_

        Returns:
            bool: _description_
        """
        symbol_info = mt5.symbol_info(position.symbol)
        price_digits = symbol_info.digits

        # Create the request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "symbol": position.symbol,
            # "sl": new_stop_loss,
            # "tp": new_take_profit,
        }

        # Optional parameters
        if new_stop_loss is not None:
            request["sl"] = round(new_stop_loss, price_digits)
        if new_take_profit is not None:
            request["tp"] = round(new_take_profit, price_digits)
        # Send order to MT5
        order_result = mt5.order_send(request)
        check_order_sent(order_result, "modifying")

        return order_result

    def get_positions(
        self,
        symbol: str = None,
    ) -> tuple[mt5.TradePosition]:
        """Retrieves the current open trading positions.

        Args:
            symbol (str, optional): The symbol for which to retrieve open positions.
                If None (default), all open positions are returned.

        Returns:
            tuple[mt5.TradePosition]: A tuple containing the open trading positions.
                Each position is represented as an instance of the mt5.TradePosition class.

        Raises:
            RuntimeError: If the MetaTrader 5 terminal is not running or fails to provide the positions.
        """
        if symbol is None:
            return mt5.positions_get()
        return mt5.positions_get(symbol=symbol)

    def total_positions(
        self,
        symbol: str = None,
    ) -> int:
        """Retrieves the number of open trading positions.

        Args:
            symbol (str, optional): The symbol for which to calculate open positions.
                If None (default), total number of open positions are returned.

        Returns:
            int: Number of open positions

        Raises:
            RuntimeError: If the MetaTrader 5 terminal is not running or fails to provide the positions.
        """
        if symbol is None:
            return mt5.positions_total()
        return len(mt5.positions_get(symbol=symbol))

    def get_orders(
        self,
        symbol: str = None,
    ) -> tuple[mt5.TradeOrder]:
        """Retrieves the current open trading orders.

        Args:
            symbol (str, optional): The symbol for which to retrieve open orders.
                If None (default), all open orders are returned.

        Returns:
            tuple[mt5.TradeOrder]: A tuple containing the open trading orders.
                Each order is represented as an instance of the mt5.TradeOrder class.

        Raises:
            RuntimeError: If the MetaTrader 5 terminal is not running or fails to provide the orders.
        """
        if symbol is None:
            return mt5.orders_get()
        return mt5.orders_get(symbol=symbol)

    def total_orders(
        self,
        symbol: str = None,
    ) -> int:
        """Retrieves the number of open trading orders.

        Args:
            symbol (str, optional): The symbol for which to calculate open orders.
                If None (default), total number of open orders are returned.

        Returns:
            int: Number of open orders

        Raises:
            RuntimeError: If the MetaTrader 5 terminal is not running or fails to provide the orders.
        """
        if symbol is None:
            return mt5.orders_total()
        return len(mt5.orders_get(symbol=symbol))

    def get_ticks(
        self,
        symbol: str,
        n_ticks: int,
        as_dataframe: bool = False,
        format_time: bool = False,
        tzone: str = "US/Central",
    ) -> CandleLike:
        """Extract n ticks before now

        Args:
            symbol (str): Symbol to extract data
            n_ticks (int): Number of ticks retrieved before now
            tzone (str, optional): Convert the datetime to specific timezone. Defaults to "US/Central".

        Returns:
            DataFrame: All ticks data transformed into DataFrame
        """
        # Extract n Ticks before now
        try:
            from_date = datetime.utcnow()  # TODO: esta wea no funciona por eso del from_date. Revisar que pedo
            ticks = mt5.copy_ticks_from(symbol, from_date, n_ticks, mt5.COPY_TICKS_ALL)
        except Exception as e:
            raise ValueError(f"An error occurred while getting ticks: {e}")

        if not as_dataframe and not format_time:
            return ticks.view(recarray)

        # Transform Tuple into a DataFrame
        df_ticks = DataFrame(ticks)

        # Convert number format of the date into date format
        if format_time:
            df_ticks["time_msc"] = to_datetime(df_ticks["time_msc"], unit="ms", utc=True)
            df_ticks["time_msc"] = df_ticks["time_msc"].tz_localize('Etc/GMT-3').tz_convert(tzone)

        return df_ticks if as_dataframe else df_ticks.to_records(index=False)

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        n_candles: int,
        from_candle: int = 0,
        as_dataframe: bool = False,
        format_time: bool = False,
        tzone: str = "US/Central"
    ) -> CandleLike:
        """Query previous candlestick data from symbol. Convert the data into DataFrame

        Args:
            symbol (_type_): _description_
            timeframe (_type_): _description_
            n_candles (_type_): _description_

        Returns:
            _type_: _description_
        """
        # Extract n Candles before from_candle in a specific timeframe
        try:
            mt5_tf = TimeFrames[timeframe].value
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, from_candle, n_candles)
        except Exception as e:
            raise ValueError(f"An error occurred while getting candles: {e}")

        if not as_dataframe and not format_time:
            return rates.view(recarray)

        # Transform Tuple into a DataFrame
        df_rates = DataFrame(rates)

        # Convert number format of the date into date format
        if format_time:
            df_rates['time'] = to_datetime(df_rates['time'], unit='s')
            # Localize and convert the timezone without setting 'time' as the index
            df_rates['time'] = df_rates['time'].dt.tz_localize('Etc/GMT-3').dt.tz_convert(tzone)


        return df_rates if as_dataframe else df_rates.to_records(index=False)

    def get_exchange_rate(self, symbol: str) -> float:
        # base_currency = symbol[3:]
        # if base_currency == self.account_info.currency:
        #     exchange_rate = 1.0
        # else:
        #     m10 = TimeFrames["M10"].value
        #     exchange_symbol = self.account_info.currency + base_currency
        #     # exchange_rate = mt5.copy_rates_from_pos(exchange_symbol, m1, 0, 1)[0][1]  # open price
        #     exchange_rate = mt5.copy_rates_from_pos(
        #         exchange_symbol, m10, 0, 1)[0][3]  # low price
        # return exchange_rate
        check_symbol(symbol)

        base_currency = symbol[3:]
        if base_currency == self.account_info.currency:
            return 1.0

        exchange_symbol = base_currency + self.account_info.currency  # standard forex notation: base + quote
        try:
            tick = mt5.symbol_info_tick(exchange_symbol)
            if not tick or tick.ask == 0 or tick.bid == 0:
                # if the direct pair doesn't exist or if bid/ask is not available, try the inverse
                exchange_symbol = self.account_info.currency + base_currency
                tick = mt5.symbol_info_tick(exchange_symbol)
                if tick and tick.ask != 0 and tick.bid != 0:
                    return (tick.bid + tick.ask) / 2
            else:
                return 2 / (tick.bid + tick.ask)

        except Exception as e:
            raise ValueError(f"An error occurred while getting exchange rate: {e}")

        raise ValueError(f"Could not find any exchange rate for {base_currency} with {self.account_info.currency}")

    def calc_risk_params(
        self,
        symbol: str,
        order_type: str,
        pipettes: int = None,
        risk_pct: float = None,
        rr_ratio: float = None,
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
        check_symbol(symbol)
        check_order_type(order_type)

        # Calculate stop loss & take profit based on the risk/reward ratio and current bid-ask price
        open_price = self.get_current_price(symbol, order_type)
        stop_loss, take_profit = calculate_sltp(symbol, order_type, open_price,
                                                pipettes, rr_ratio)
        # # Calculate the proper lot_size based on the risked_amount and the pip_amount
        lot_size = self.calc_adjusted_lot_size(symbol, open_price, stop_loss, risk_pct)

        # # Calculate the maximum amount that can be risked on a single trade
        # risked_balance = mt5.account_info().balance * risk_pct
        #
        # pip_amount = get_pipette_unit(symbol) * pipettes
        # exchange_rate = self.get_exchange_rate(symbol)
        # lot_size = bound_lot(symbol, risked_balance * exchange_rate / (100_000. * pip_amount))

        return open_price, lot_size, stop_loss, take_profit

    def get_current_price(
        self,
        symbol: str,
        order_type: Union[OrderTypes, str]
    ) -> float:
        """Calculate the open price for a market position using MetaTrader5 python package.

        Args:
            symbol (str): The symbol of the currency pair to trade.
            order_type (Union[OrderTypes, str]): The type of the order, either 'BUY' or 'SELL'.

        Returns:
            float: The open price for the given order type.

        Raises:
            ValueError: If the order_type is not a valid OrderTypes value.
        """

        symbol_info = mt5.symbol_info(symbol)

        if isinstance(order_type, str):
            order_type = OrderTypes[order_type]

        if order_type == OrderTypes.BUY:
            # Ask is the minimum price that a seller is willing to take for that same asset.
            return symbol_info.ask
        elif order_type == OrderTypes.SELL:
            # Bid is the maximum price that a buyer is willing to pay for an asset.
            return symbol_info.bid
        else:
            raise ValueError(f"Invalid order type: {order_type}")

    def calculate_lot_size(
        self,
        symbol: str,
        open_price: float,
        stop_loss: float,
        risk_pct: float,
    ) -> float:
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
        check_symbol(symbol)

        # Calculate the amount from your balance that will be risked
        risked_balance = mt5.account_info().balance * risk_pct

        # Calculate the amount in pips to be risked
        price_digits = mt5.symbol_info(symbol).digits
        pip_amount = round(abs(open_price - stop_loss), price_digits)

        # Calculate the proper lot_size based on the risked_balance and the pip_amount
        exchange_rate = self.get_exchange_rate(symbol)
        lot_size = risked_balance * exchange_rate / (100_000. * pip_amount)

        # print(f"{risked_balance=}, {pip_amount=}, {exchange_rate=}, {lot_size=}")

        return bound_lot(symbol, lot_size)


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
