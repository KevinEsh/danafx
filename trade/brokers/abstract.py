from typing import Any, Union
from abc import abstractmethod, ABC
from trade.metadata import CandleLike, OrderTypes


class BrokerSession(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def start_session(
        self,
        login_settings: dict[str, str]
    ) -> None:
        ...

    @abstractmethod
    def enable_symbols(
        self,
        symbols: list[str]
    ) -> None:
        ...

    @abstractmethod
    def create_order(
        self,
        symbol: str,
        order_type: str,
        price: float,
        lot_size: float,
        stop_loss: float,
        take_profit: float,
        deviation: int = 10,
    ) -> Any:
        ...

    @abstractmethod
    def close_position(
        self,
        position: Any,
        deviation: int = 10,
    ) -> Any:
        ...

    @abstractmethod
    def cancel_order(
        self,
        order: Any
    ):
        ...

    @abstractmethod
    def modify_position(
        self,
        position: Any,
        new_stop_loss: float = None,
        new_take_profit: float = None,
    ):
        ...

    @abstractmethod
    def get_positions(
        self,
        symbol: str = None,
    ) -> tuple[Any]:
        ...

    @abstractmethod
    def total_positions(
        self,
        symbol: str = None,
    ) -> int:
        ...

    @abstractmethod
    def get_orders(
        self,
        symbol: str = None,
    ) -> tuple[Any]:
        ...

    @abstractmethod
    def total_orders(
        self,
        symbol: str = None,
    ) -> int:
        ...

    @abstractmethod
    def get_ticks(
        self,
        symbol: str,
        n_ticks: int,
        as_dataframe: bool,
        format_time: bool,
        tzone: str = "US/Central",
    ) -> CandleLike:
        ...

    @abstractmethod
    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        n_candles: int,
        from_candle: int,
        as_dataframe: bool,
        format_time: bool,
        tzone: str = "US/Central"
    ) -> CandleLike:
        ...

    @abstractmethod
    def get_exchange_rate(
        self,
        symbol: str
    ) -> float:
        ...

    @abstractmethod
    def get_current_price(
        self,
        symbol: str,
        order_type: Union[OrderTypes, str]
    ) -> float:
        ...

    @abstractmethod
    def calculate_lot_size(
        symbol: str,
        open_price: float,
        stop_loss: float,
        risk_pct: float,
    ) -> float:
        ...
