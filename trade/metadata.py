import MetaTrader5 as mt5
from enum import Enum
from numpy import recarray, ndarray
from typing import Union
from pandas import Series

CandleLike = Union[Series, recarray, ndarray]


class AssetState(Enum):
    NULL_POSITION = 0
    WAITING_POSITION = 1
    ON_POSITION = 2


class EntrySignal(Enum):
    NEUTRAL = -1
    BUY = mt5.POSITION_TYPE_BUY
    SELL = mt5.POSITION_TYPE_SELL


class ExitSignal(Enum):
    EXIT = 1
    HOLD = 0


class TimeFrames(Enum):
    M1 = mt5.TIMEFRAME_M1
    M2 = mt5.TIMEFRAME_M2
    M3 = mt5.TIMEFRAME_M3
    M4 = mt5.TIMEFRAME_M4
    M5 = mt5.TIMEFRAME_M5
    M6 = mt5.TIMEFRAME_M6
    M10 = mt5.TIMEFRAME_M10
    M12 = mt5.TIMEFRAME_M12
    M15 = mt5.TIMEFRAME_M15
    M20 = mt5.TIMEFRAME_M20
    M30 = mt5.TIMEFRAME_M30
    H1 = mt5.TIMEFRAME_H1
    H2 = mt5.TIMEFRAME_H2
    H3 = mt5.TIMEFRAME_H3
    H4 = mt5.TIMEFRAME_H4
    H6 = mt5.TIMEFRAME_H6
    H8 = mt5.TIMEFRAME_H8
    H12 = mt5.TIMEFRAME_H12
    D1 = mt5.TIMEFRAME_D1
    W1 = mt5.TIMEFRAME_W1
    MN1 = mt5.TIMEFRAME_MN1


class OrderTypes(Enum):
    BUY = mt5.ORDER_TYPE_BUY  # Market Buy order
    SELL = mt5.ORDER_TYPE_SELL  # Market Sell order
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT  # Buy Limit pending order
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT  # Sell Limit pending order
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP  # Buy Stop pending order
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP  # Sell Stop pending order
    # Upon reaching the order price a pending Buy Limit order is placed at the StopLimit price
    BUY_STOP_LIMIT = mt5.ORDER_TYPE_BUY_STOP_LIMIT
    # Upon reaching the order price a pending Sell Limit order is placed at the StopLimit price
    SELL_STOP_LIMIT = mt5.ORDER_TYPE_SELL_STOP_LIMIT
    # Order to close a position by an opposite one
    CLOSE_BY = mt5.ORDER_TYPE_CLOSE_BY


class InverseOrderTypes(Enum):
    BUY = mt5.ORDER_TYPE_SELL  # If Buy order then sell it to close position
    SELL = mt5.ORDER_TYPE_BUY  # If Sell order then buy it to close position
