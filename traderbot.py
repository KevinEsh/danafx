from time import sleep
from utils.console import logger

from trade.metadata import AssetState
from trade.brokers import BrokerSession, Mt5Session
from trade.state_machine import AssetStateMachine
from trade.strategies.abstract import TradingStrategy


class SingleTraderBot:

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        risk_params: dict,
        leap_in_secs: float = 30,
    ) -> None:
        self.state = None
        self.broker = None
        self.strategy = None
        self.symbol = symbol
        self.timeframe = timeframe
        self.risk_params = risk_params  # TODO: mejor manera de guardar esto
        self.leap_in_secs = leap_in_secs
        logger.name = f"traderbot.{symbol.lower()}"

    def set_strategy(self, strategy: TradingStrategy) -> None:
        self.strategy = strategy

    def set_broker(self, broker: BrokerSession) -> None:
        self.broker = broker

    def set_init_state(self):

        if self.broker.total_orders(self.symbol) > 0:
            # TODO: quiza algun dia se implemente un cancel_order early
            # orders = self.broker.get_orders(self.symbol)
            # self.strategy.order = orders[-1]
            self.state = AssetStateMachine(AssetState.WAITING_POSITION)

        elif self.broker.total_positions(self.symbol) > 0:
            positions = self.broker.get_positions(self.symbol)
            self.strategy.position = positions[-1]
            self.state = AssetStateMachine(AssetState.ON_POSITION)

        else:
            self.state = AssetStateMachine()

        train_data = self.broker.get_candles(self.symbol, self.timeframe,
                                             self.strategy.min_bars, 1)
        #  self.strategy.min_bars, 1)
        self.strategy.fit(train_data)

    def run(self) -> None:
        """_summary_
        """
        # Select symbol to run strategy on
        # symbol_for_strategy = self.live_trading_symbols[0]  # TODO: parallel computing with all symbols
        # Set up a previous time variable
        logger.info(f"running traderbot on {self.symbol}")
        self.set_init_state()

        # Start a live trading session
        while True:  # TODO:self._is_active():

            # Retrieve the current candle data
            # latest_tick = self.broker.get_ticks(
            #     symbol=self.symbol,
            #     number_of_ticks=1,
            #     format_time=False
            # )[-1]
            # print(latest_tick)
            candles = self.broker.get_candles(self.symbol, self.timeframe, 2)
            last_candles, current_candle = candles[:-1], candles[-1]
            # print(current_candle.close)

            # Always update data to save computational time and memory
            self.strategy.update_data(last_candles)

            # If no position is placed, create an entry signal
            if self.state.null_position:
                entry_signal = self.strategy.get_entry_signal(current_candle)
                # print(entry_signal.name)
                # entry_signal = None

                # If you get and entry signal either BUY or SELL, create an market order
                if self.state.is_entry(entry_signal):
                    order_params = self.broker.calc_risk_params(
                        self.symbol, entry_signal.name, **self.risk_params)
                    self.broker.create_order(
                        self.symbol, entry_signal.name, *order_params)
                    self.state.next()
                    logger.info(
                        f"order {entry_signal.name.lower()} created on {self.symbol}")

            if self.state.awaiting_position:
                positions = self.broker.get_positions(self.symbol)

                if positions:
                    self.strategy.position = positions[-1]
                    self.state.next()
                    logger.info(
                        f"position {self.strategy.position.ticket} placed for {self.symbol}")

            elif self.state.on_position:
                if self.broker.total_positions(self.symbol) == 0:
                    logger.info(
                        f"position {self.strategy.position.ticket} on {self.symbol} closed by broker")
                    self.strategy.position = None
                    self.state.next()

                exit_signal = self.strategy.get_exit_signal(current_candle)

                if self.state.is_exit(exit_signal):
                    self.broker.close_position(self.strategy.position)
                    logger.info(
                        f"position {self.strategy.position.ticket} on {self.symbol} closed by bot")
                    self.strategy.position = None
                    self.state.next()

                else:
                    # strategy.update_trailing_stop(order=position, trailing_stop_pips=10, pip_size=trading_settings['pip_size'])
                    pass

            sleep(self.leap_in_secs)


if __name__ == "__main__":
    from utils.config import get_settings
    # from trade.strategies.trending import DualMavStrategy
    # from trade.strategies.momentum import RsiStrategy
    # from trade.strategies.trending import TrendlineBreakStrategy
    from trade.strategies.trending import DualNadarayaKernelStrategy

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
    strategy = DualNadarayaKernelStrategy(
        window_rqk=6,
        window_rbfk=6 - 3,
        alpha_rq=100,
        n_bars=20,
        lag=0,
        neutral_band=(-0.000055, 0.000055),
    )

    risk_params = {
        "pipettes": 15,
        "risk_tolerance": 0.01,
        "rr_ratio": 1.1,
    }

    trader = SingleTraderBot(symbol, "M1", risk_params, 5)
    trader.set_broker(broker)
    trader.set_strategy(strategy)

    trader.run()
