from time import sleep
from utils.console import logger

from trade.metadata import AssetState, EntrySignal
from trade.brokers import BrokerSession, Mt5Session
from trade.state_machine import AssetStateMachine
from trade.strategies.abstract import TradingStrategy, TrailingStopStrategy


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
        self.trailing = None
        self.symbol = symbol
        self.timeframe = timeframe
        self.risk_params = risk_params  # TODO: mejor manera de guardar esto
        self.leap_in_secs = leap_in_secs
        logger.name = f"{symbol}"

    def set_strategy(self, strategy: TradingStrategy) -> None:
        self.strategy = strategy

    def set_trailing(self, trailing: TrailingStopStrategy) -> None:
        self.trailing = trailing

    def set_broker(self, broker: BrokerSession) -> None:
        self.broker = broker

    def set_init_state(self):

        # Check is at the beggining of the session there are pending orders to be placed
        if self.broker.total_orders(self.symbol) > 0:
            # TODO: quiza algun dia se implemente un cancel_order early
            orders = self.broker.get_orders(self.symbol)
            self.state = AssetStateMachine(AssetState.WAITING_POSITION)
            logger.warning(f"order {orders[-1].ticket} found. Bot will wait position to take place")

        # Check if there is a position in place. It will be monitored and modified
        elif self.broker.total_positions(self.symbol) > 0:
            positions = self.broker.get_positions(self.symbol)
            self.strategy.position = positions[-1]
            self.trailing.position = positions[-1]
            self.state = AssetStateMachine(AssetState.ON_POSITION)
            logger.warning(f"position {positions[-1].ticket} found. Bot will monitor it")

        # No positions, no orders then start looking for a new oportunity
        else:
            self.state = AssetStateMachine(AssetState.NULL_POSITION)
            logger.info("looking for entry signals")

        # Calculate the minimal amount of data to get accurate predictions
        min_bars = max(self.strategy.min_bars, self.trailing.min_bars)
        train_data = self.broker.get_candles(self.symbol, self.timeframe, min_bars, 1)

        # Train the models
        self.strategy.fit(train_data)
        self.trailing.fit(train_data)

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
            self.trailing.update_data(last_candles)

            # If no position is placed, create an entry signal
            if self.state.null_position:
                entry_signal = self.strategy.get_entry_signal(current_candle)
                # print(entry_signal.name)
                # entry_signal = EntrySignal.BUY

                # If you get and entry signal either BUY or SELL, create an market order
                if self.state.is_entry(entry_signal):
                    order_params = self.calc_risk_params(current_candle, entry_signal)
                    self.broker.create_order(self.symbol, entry_signal.name, *order_params)
                    self.state.next()
                    logger.info(f"{entry_signal.name.lower()} order created on {self.symbol}")

            if self.state.awaiting_position:
                positions = self.broker.get_positions(self.symbol)

                if positions:
                    self.strategy.position = positions[-1]
                    self.state.next()
                    logger.info(f"position {self.strategy.position.ticket} placed for {self.symbol}")

            elif self.state.on_position:
                if self.broker.total_positions(self.symbol) == 0:
                    logger.info(f"position {self.strategy.position.ticket} on {self.symbol} closed by broker")
                    self.strategy.position = None
                    self.trailing.position = None
                    self.state.next()
                    continue

                exit_signal = self.strategy.get_exit_signal(current_candle)

                if self.state.is_exit(exit_signal):
                    self.broker.close_position(self.strategy.position)
                    logger.info(
                        f"position {self.strategy.position.ticket} on {self.symbol} closed by bot")
                    self.strategy.position = None
                    self.trailing.position = None
                    self.state.next()
                    continue

                if self.trailing is not None:
                    stop_loss = self.trailing.calculate_stop_level(current_candle, self.strategy.position)
                    take_profit = self.strategy.position.tp
                    print(stop_loss)
                    if abs(stop_loss - self.strategy.position.sl) >= 0.00001:
                        self.broker.modify_position(self.strategy.position, stop_loss, take_profit)
                        positions = self.broker.get_positions(self.symbol)
                        self.strategy.position = positions[-1]
                        self.trailing.position = positions[-1]

            sleep(self.leap_in_secs)

    def calc_risk_params(
        self,
        candle: str,
        signal: EntrySignal,
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
        # Calculate stop loss & take profit based on the risk/reward ratio and current bid-ask price
        risk_pct = self.risk_params["risk_pct"]
        rr_ratio = self.risk_params["rr_ratio"]
        # print(f"{signal=}, {risk_pct=}, {rr_ratio=}")
        open_price = self.broker.get_current_price(self.symbol, signal.name)
        stop_loss = self.trailing.calculate_stop_level(candle, signal=signal)
        lot_size = self.broker.calculate_lot_size(self.symbol, open_price, stop_loss, risk_pct)

        if rr_ratio == 0:
            take_profit = 0
        elif signal == EntrySignal.BUY:
            take_profit = open_price + rr_ratio * abs(open_price - stop_loss)
        else:
            take_profit = open_price - rr_ratio * abs(open_price - stop_loss)

        return open_price, lot_size, stop_loss, take_profit


if __name__ == "__main__":
    from utils.config import get_settings
    # from trade.strategies.trending import DualMavStrategy
    # from trade.strategies.momentum import RsiStrategy
    # from trade.strategies.trending import TrendlineBreakStrategy
    from trade.strategies.trending import DualNadarayaKernelStrategy
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
    strategy = DualNadarayaKernelStrategy(
        window_rqk=7,
        window_rbfk=7 - 1,
        alpha_rq=0.7,
        n_bars=20,
        lag=1,
        neutral_band=(-0.0003, 0.0003),
    )

    trailing = AtrBandTrailingStop(
        window=14,
        multiplier=2,
        neutral_band=(-0.0001, 0.0001),
        lag=1,
    )

    risk_params = {
        # "pipettes": 15,
        "risk_pct": 0.04,
        "rr_ratio": 2.5,
    }

    trader = SingleTraderBot(symbol, "M3", risk_params, 5)
    trader.set_broker(broker)
    trader.set_strategy(strategy)
    trader.set_trailing(trailing)

    trader.run()
