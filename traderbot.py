from time import sleep

from trade.metadata import EntrySignal, AssetState, CandleLike
from trade.bots.abstract import AbstractTraderBot

# TODO: parallel computing with all symbols
class SingleTraderBot(AbstractTraderBot):

    def set_init_state(self):

        # Check if there is a position in place at the beggining of the session. It will be monitored and modified
        if self.broker.total_positions(self.symbol) > 0:
            self.position = self.broker.get_positions(self.symbol)[-1]
            # self.strategy.position = position
            # self.trailing.position = position
            self.state.set(AssetState.ON_POSITION)
            self.logger.warning(f"position {self.position.ticket} found. Bot will monitor it")

        # Check if there is a pending order to be placed
        elif self.broker.total_orders(self.symbol) > 0:
            # TODO: quiza algun dia se implemente un cancel_order early
            order = self.broker.get_orders(self.symbol)[-1]
            self.state.set(AssetState.WAITING_POSITION)
            self.logger.warning(f"order {order.ticket} found. Bot will wait position to take place")

        # No positions, no orders then start looking for a new oportunity
        else:
            # self.state.set(AssetState.NULL_POSITION)
            self.logger.info("looking for entry signals")

        # Calculate the minimal amount of data to get accurate predictions
        min_bars = max(self.strategy.min_bars, self.trailing.min_bars)
        train_data = self.broker.get_candles(self.symbol, self.timeframe, min_bars, 1)

        # Train the models
        self.strategy.fit(train_data)
        self.trailing.fit(train_data)

    def run(self) -> None:
        """_summary_
        """
        self.logger.info("running single traderbot")
        self.set_init_state()

        # Start a live trading session
        while self._is_active():
            # Retrieve the latest candle data and 
            candles = self.broker.get_candles(self.symbol, self.timeframe, 2)
            last_candles, current_candle = candles[:-1], candles[-1]

            # Always update data to save computational time and memory
            self.strategy.update_data(last_candles)
            self.trailing.update_data(last_candles)

            # print(current_candle.close)


            # If no position is on placed, create an entry signal
            if self.state.null_position:
                entry_signal = self.strategy.get_entry_signal(current_candle)
                # print(entry_signal.name)
                # entry_signal = EntrySignal.BUY

                # If you get and entry signal either BUY or SELL, create a market order
                if self.state.is_entry(entry_signal):
                    entry_params = self.calculate_entry_params(current_candle, entry_signal)
                    self.broker.create_order(self.symbol, entry_signal.name, *entry_params)
                    self.state.next()
                    self.logger.info(f"{entry_signal.name.lower()} order created")

            if self.state.awaiting_position:
                positions = self.broker.get_positions(self.symbol)

                if positions:
                    self.position = positions[-1]
                    self.state.next()
                    self.logger.info(f"position {self.position.ticket} placed")

            elif self.state.on_position:
                if self.broker.total_positions(self.symbol) == 0:
                    self.logger.info(f"position {self.position.ticket} closed on app")
                    self.state.next()
                    continue

                exit_signal = self.strategy.get_exit_signal(current_candle)

                if self.state.is_exit(exit_signal):
                    self.broker.close_position(self.position)
                    self.logger.info(f"position {self.position.ticket} closed by bot")
                    self.state.next()
                    continue

                if self.trailing is not None:
                    stop_loss, take_profit = self.update_stop_levels(current_candle, self.position)

                    if abs(stop_loss - self.position.sl) >= 0.00001:
                        self.broker.modify_position(self.position, stop_loss, take_profit)
                        self.position = self.broker.get_positions(self.symbol)[-1]
                        self.logger.info(f"position {self.position.ticket} modified {stop_loss=:.5f}, {take_profit=:.5f}")

            sleep(self.leap_in_secs)
        self.logger.info("single traderbot session finished")

    def calculate_entry_params(
        self,
        candle: CandleLike,
        signal: EntrySignal,
    ) -> tuple[float, ...]:
        """Calculates the price, lot size, stop loss and take profit based on the
        account balance, risk tolerance, pips until hit a stop loss, and risk reward ratio

        Returns:
            tuple[float]: price, lot_size, stop_loss, take_profit
        """
        # Calculate stop loss & take profit based on the risk/reward ratio and current bid-ask price
        risk_pct = self.risk_params["risk_pct"]
        # print(f"{signal=}, {risk_pct=}, {rr_ratio=}")
        stop_loss, take_profit = self.trailing.calculate_stop_levels(candle, signal=signal)

        if self.adjust_spread:
            open_price = self.broker.get_current_price(self.symbol, signal.name)
            adjustment = open_price - candle.close
            stop_loss += adjustment
            take_profit += adjustment
        else:
            open_price = candle.close
    
        lot_size = self.broker.calculate_lot_size(self.symbol, open_price, stop_loss, risk_pct)

        return open_price, lot_size, stop_loss, take_profit

    def update_stop_levels(self, candle, position) -> tuple[float, ...]:
        # Calculate new stop level based on whether we are in a long or short position

        lower_nb, upper_nb = self.trailing._band
        
        if position.type == EntrySignal.BUY.value:
            new_stop_loss, _ = self.trailing.calculate_stop_levels(candle, EntrySignal.BUY)

            # if new stop_loss is not greater than current we don't update
            # if (new_stop_loss > position.price_open + upper_nb and new_stop_loss > position.sl):
            if new_stop_loss > position.sl:
                return new_stop_loss, position.tp
            else:
                return position.sl, position.tp

        elif position.type == EntrySignal.SELL.value:
            new_stop_loss, _ = self.trailing.calculate_stop_levels(candle, EntrySignal.SELL)

            # if new stop_loss is not lower than current we don't update
            # if (new_stop_loss < position.price_open + lower_nb and new_stop_loss < position.sl):
            if new_stop_loss < position.sl:
                return new_stop_loss, position.tp
            else:
                return position.sl, position.tp
            

def break_stop(a, b, c):
    return a < (b + c)

if __name__ == "__main__":
    from utils.config import get_settings
    from trade.brokers import Mt5Session
    # from trade.strategies.trending import DualMavStrategy
    # from trade.strategies.momentum import RsiStrategy
    # from trade.strategies.trending import TrendlineBreakStrategy
    from trade.strategies import DualNadarayaKernelStrategy
    from trade.strategies import MinMaxStrategy
    from trade.strategies.trailingstop import AtrBandTrailingStop

    login_settings = get_settings("settings/demo/login.json")
    # trading_settings = get_settings("settings/demo/trading.json")

    symbol = "GBPUSD" #"EURUSD"

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

    # strategy = DualNadarayaKernelStrategy(
    #     window_rqk=12,
    #     window_rbfk=12 - 1,
    #     alpha_rq=0.3,
    #     n_bars=25,
    #     lag=1,
    #     neutral_band=(-0.0001, 0.0001),
    # )

    strategy = MinMaxStrategy(
        window=1,
        lag=0,
        band=(-0.0007, 0.0007)
    )

    trailing = AtrBandTrailingStop(
        window=14,
        multiplier=2,
        neutral_band=(-0.000, 0.000),
        rr_ratio=1.0,
        lag=1,
    )

    risk_params = {
        # "pipettes": 15,
        "risk_pct": 0.01,
    }

    trader = SingleTraderBot(symbol, "M5", risk_params, 5)
    trader.set_broker(broker)
    trader.set_strategy(strategy)
    trader.set_trailing(trailing)

    trader.run()
