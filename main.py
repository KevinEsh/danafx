from utils.config import get_settings
from trade.brokers import Mt5Session
from trade.bots import SingleTraderBot
# from trade.strategies.trending import DualMavStrategy
# from trade.strategies.momentum import RsiStrategy
# from trade.strategies.trending import TrendlineBreakStrategy
from trade.strategies import DualNadarayaKernelStrategy
from trade.strategies import ZigZagEntryStrategy, CompoundTradingStrategy, Priority, And, Or
from trade.strategies.exit import DirectionChangeExitStrategy
from trade.strategies.trailingstop import AtrBandTrailingStop

login_settings = get_settings("settings/demo/login.json")
# trading_settings = get_settings("settings/demo/trading.json")

symbol = "EURUSD"

# Login on a broker session
broker = Mt5Session()
broker.start_session(login_settings["mt5_login"])
broker.enable_symbols([symbol])

# Select strategy
# strategy = DualMavStrategy(5, 200, neutral_band=(-0.0004, 0.0004), inverse=True)
# strategy = DualRmaStrategy(5, 200, neutral_band=(-0.0004, 0.0004), inverse=True)
# strategy = RsiStrategy(14, (0, 23), (70, 100), mode="outband")
# strategy = TrendlineBreakStrategy(window=5, alpha=1.856, offset=-1)
# strategy = DualNadarayaKernelStrategy(
#     window_rqk=9,
#     window_rbfk=9 - 1,
#     alpha_rq=1,
#     lag=1,
#     n_bars=20,
#     neutral_band=(-0.000028, 0.000028),
# )

entry_strategy = DualNadarayaKernelStrategy(
    window_rqk=30,
    window_rbfk=30 - 2,
    alpha_rq=17.7,
    n_bars=30,
    lag=1,
    band=(-1.3177564853306123e-06, 1.3177564853306123e-06),
)
# engulfing_candle_strategy = MinMaxStrategy(
#     window=1,
#     lag=0,
#     band=(-0.0003, 0.0003),
#     neutral_length=0.00005
# )

# basic_strategy = ZigZagEntryStrategy(
#     window=1,
#     lag=1,
#     band=(-0.000, 0.000),
#     # neutral_length=0.00015
# )

# entry_strategy = Priority(
#     engulfing_candle_strategy,
#     basic_strategy,
# )

exit_strategy = DirectionChangeExitStrategy(
    length=0.00017,
    lag=1,
    only_profit=True,
)

trailing = AtrBandTrailingStop(
    window=14,
    multiplier=2.2,
    neutral_band=(-0.000, 0.000),
    rr_ratio=3.0,
    lag=1,
)

risk_params = {
    # "pipettes": 15,
    "risk_pct": 0.01,
}

# strategy = CompoundTradingStrategy(
#     entry_strategy,
#     exit_strategy
# )

trader = SingleTraderBot(
    symbol=symbol,
    timeframe="M3",
    risk_params=risk_params, 
    leap_in_secs=2,
    interval="13:30-11:30",
    update_stops=True,
    adjust_spread=False,
)

trader.set_broker(broker)
trader.set_entry_strategy(entry_strategy)
trader.set_exit_strategy(exit_strategy)
trader.set_trailing_strategy(trailing)

trader.run()