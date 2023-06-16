from typing import Any, Union
from abc import abstractmethod, ABC
from datetime import datetime as dt
from utils.console import get_logger
from trade.brokers import BrokerSession
from trade.state_machine import AssetStateMachine
from trade.strategies.abstract import TradingStrategy, TrailingStopStrategy


class AbstractTraderBot(ABC):
    
    def __init__(
        self,
        symbol: str,
        timeframe: str,
        risk_params: dict,
        leap_in_secs: float = 30,
        interval: str = None,
        adjust_spread: bool = True,
        update_stops: bool =  False,
    ) -> None:
        super().__init__()

        self.broker = None
        self.entry_strategy = None
        self.exit_strategy = None
        self.trailing = None
        self.symbol = symbol
        self.timeframe = timeframe
        self.risk_params = risk_params  # TODO: mejor manera de guardar esto
        self.leap_in_secs = leap_in_secs
        self.adjust_spread = adjust_spread
        self.update_stops =  update_stops
        self.state = AssetStateMachine()

        self.logger = get_logger()
        self.logger.name = symbol

        if interval is None:
            self.start_time = None
            self.end_time = None
        else:
            self._set_active_interval(interval)

    def set_entry_strategy(self, entry_strategy: TradingStrategy) -> None:
        self.entry_strategy = entry_strategy

    def set_exit_strategy(self, exit_strategy: TradingStrategy) -> None:
        self.exit_strategy = exit_strategy

    def set_trailing(self, trailing: TrailingStopStrategy) -> None:
        self.trailing = trailing

    def set_broker(self, broker: BrokerSession) -> None:
        self.broker = broker

    def _set_active_interval(self, interval: str, timezone: str = 'UTC'):
        # Split the interval into start and end
        try:
            start, end = interval.split('-')
            start_hour, start_minute = map(int, start.split(':'))
            end_hour, end_minute = map(int, end.split(':'))
        except ValueError:
            raise ValueError('Invalid interval format. Expected "HH:MM-HH:MM".')

        # Check if the inputs are valid
        if not (0 <= start_hour < 24) or not (0 <= end_hour < 24):
            raise ValueError('Hours should be in range 0-23.')
        if not (0 <= start_minute < 60) or not (0 <= end_minute < 60):
            raise ValueError('Minutes should be in range 0-59.')

        # Convert start and end times to minutes from midnight
        self.start_time = start_hour * 60 + start_minute
        self.end_time = end_hour * 60 + end_minute

    def _is_active(self) -> bool:
        # Get the current time
        if self.start_time is None:
            return True

        now = dt.now()
        current_time = now.hour * 60 + now.minute

        # Check if the current time is in the interval
        if self.start_time <= self.end_time:
            return self.start_time <= current_time < self.end_time
        else:  # Interval wraps around midnight
            return not (self.end_time <= current_time < self.start_time)

    # @abstractmethod
    # def start_session(
    #     self,
    #     login_settings: dict[str, str]
    # ) -> None:
    #     ...

    # @abstractmethod
    # def enable_symbols(
    #     self,
    #     symbols: list[str]
    # ) -> None:
    #     ...

    # @abstractmethod
    # def create_order(
    #     self,
    #     symbol: str,
    #     order_type: str,
    #     price: float,
    #     lot_size: float,
    #     stop_loss: float,
    #     take_profit: float,
    #     deviation: int = 10,
    # ) -> Any:
    #     ...

    # @abstractmethod
    # def close_position(
    #     self,
    #     position: Any,
    #     deviation: int = 10,
    # ) -> Any:
    #     ...

    # @abstractmethod
    # def cancel_order(
    #     self,
    #     order: Any
    # ):
    #     ...

    # @abstractmethod
    # def modify_position(
    #     self,
    #     position: Any,
    #     new_stop_loss: float = None,
    #     new_take_profit: float = None,
    # ):
    #     ...

    # @abstractmethod
    # def get_positions(
    #     self,
    #     symbol: str = None,
    # ) -> tuple[Any]:
    #     ...

    # @abstractmethod
    # def total_positions(
    #     self,
    #     symbol: str = None,
    # ) -> int:
    #     ...

    # @abstractmethod
    # def get_orders(
    #     self,
    #     symbol: str = None,
    # ) -> tuple[Any]:
    #     ...

    # @abstractmethod
    # def total_orders(
    #     self,
    #     symbol: str = None,
    # ) -> int:
    #     ...

    # @abstractmethod
    # def get_ticks(
    #     self,
    #     symbol: str,
    #     n_ticks: int,
    #     as_dataframe: bool,
    #     format_time: bool,
    #     tzone: str = "US/Central",
    # ) -> CandleLike:
    #     ...

    # @abstractmethod
    # def get_candles(
    #     self,
    #     symbol: str,
    #     timeframe: str,
    #     n_candles: int,
    #     from_candle: int,
    #     as_dataframe: bool,
    #     format_time: bool,
    #     tzone: str = "US/Central"
    # ) -> CandleLike:
    #     ...

    # @abstractmethod
    # def get_exchange_rate(
    #     self,
    #     symbol: str
    # ) -> float:
    #     ...

    # @abstractmethod
    # def get_current_price(
    #     self,
    #     symbol: str,
    #     order_type: Union[OrderTypes, str]
    # ) -> float:
    #     ...

    # @abstractmethod
    # def calculate_lot_size(
    #     symbol: str,
    #     open_price: float,
    #     stop_loss: float,
    #     risk_pct: float,
    # ) -> float:
    #     ...
