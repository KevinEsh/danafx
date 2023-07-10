import MetaTrader5 as mt5
from enum import Enum
from numpy import recarray
from typing import Union
from pandas import Series

CandleLike = Union[Series, recarray]
TickLike = Union[Series, recarray]
TradePosition = mt5.TradePosition #ticket=425102858, time=1686945604, time_msc=1686945604865, time_update=1686945604, time_update_msc=1686945604865, type=1, magic=0, identifier=425102858, reason=0, volume=1.0, price_open=1.6921300000000001, sl=1.69791, tp=1.6844999999999999, price_current=1.6923300000000001, swap=0.0, profit=-11.82, symbol='GBPCAD', comment='', external_id=''
TradeOrder = mt5.TradeOrder  # ticket=413560923, time_setup=1685669761, time_setup_msc=1685669761748, time_done=0, time_done_msc=0, time_expiration=0, type=5, type_time=0, type_filling=2, state=1, magic=0, position_id=0, position_by_id=0, reason=0, volume_initial=0.15, volume_current=0.15, price_open=2.04554, sl=0.0, tp=0.0, price_current=2.06425, price_stoplimit=0.0, symbol='GBPNZD', comment='', external_id='')
#SymbolInfo(custom=False, chart_mode=0, select=True, visible=True, session_deals=0, session_buy_orders=0, session_sell_orders=0, volume=0, volumehigh=0, volumelow=0, time=1688763002, digits=5, spread=185, spread_float=True, ticks_bookdepth=10, trade_calc_mode=0, trade_mode=4, start_time=0, expiration_time=0, trade_stops_level=0, trade_freeze_level=0, trade_exemode=2, swap_mode=1, swap_rollover3days=3, margin_hedged_use_leg=False, expiration_mode=15, filling_mode=2, order_mode=127, order_gtc_mode=0, option_mode=0, option_right=0, bid=17.0895, bidhigh=17.39485, bidlow=17.07062, ask=17.09135, askhigh=17.39715, asklow=17.07155, last=0.0, lasthigh=0.0, lastlow=0.0, volume_real=0.0, volumehigh_real=0.0, volumelow_real=0.0, option_strike=0.0, point=1e-05, trade_tick_value=0.045558277376902497, trade_tick_value_profit=0.045558277376902497, trade_tick_value_loss=0.04556533799847484, trade_tick_size=1e-05, trade_contract_size=100000.0, trade_accrued_interest=0.0, trade_face_value=0.0, trade_liquidity_rate=0.0, volume_min=0.01, volume_max=50.0, volume_step=0.01, volume_limit=0.0, swap_long=-440.0, swap_short=230.0, margin_initial=100000.0, margin_maintenance=0.0, session_volume=0.0, session_turnover=0.0, session_interest=0.0, session_buy_orders_volume=0.0, session_sell_orders_volume=0.0, session_open=17.23778, session_close=17.2391, session_aw=0.0, session_price_settlement=0.0, session_price_limit_min=0.0, session_price_limit_max=0.0, margin_hedged=100000.0, price_change=-0.8675, price_volatility=0.0, price_theoretical=0.0, price_greeks_delta=0.0, price_greeks_theta=0.0, price_greeks_gamma=0.0, price_greeks_vega=0.0, price_greeks_rho=0.0, price_greeks_omega=0.0, price_sensitivity=0.0, basis='', category='', currency_base='USD', currency_profit='MXN', currency_margin='USD', bank='', description='US Dollar vs Mexican Peso', exchange='', formula='', isin='', name='USDMXN', page='', path='Forex\\Exotics\\USDMXN')

class AssetState(Enum):
    NULL_POSITION = 0
    WAITING_POSITION = 1
    ON_POSITION = 2


class EntrySignal(Enum):
    NEUTRAL = -1
    BUY = mt5.POSITION_TYPE_BUY
    SELL = mt5.POSITION_TYPE_SELL


class ExitSignal(Enum):
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    EXIT = mt5.ORDER_TYPE_CLOSE_BY
    HOLD = -1


class PositionType(Enum):
    BUY = mt5.POSITION_TYPE_BUY
    SELL = mt5.POSITION_TYPE_SELL


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
