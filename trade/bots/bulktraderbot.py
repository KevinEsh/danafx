from time import sleep

from trade.metadata import EntrySignal, AssetState, CandleLike
from trade.bots.abstract import AbstractTraderBot

# TODO: parallel computing with all symbols
class BulkTraderBot(AbstractTraderBot):

    def set_init_state(self):
        positions = self.broker.get_positions(self.symbol)
        orders = self.broker.get_orders(self.symbol)

        # Check if there is a position in place at the beggining of the session. It will be monitored and modified
        if positions:
            self.position = positions[-1]
            self.state.set(AssetState.ON_POSITION)
            self.logger.warning(f"position {self.position.ticket} found. Bot will monitor it")

        # Check if there is a pending order to be placed
        elif orders:
            # TODO: quiza algun dia se implemente un cancel_order early
            order = orders[-1]
            self.state.set(AssetState.WAITING_POSITION)
            self.logger.warning(f"order {order.ticket} found. Bot will wait position to take place")

        # No positions, no orders then start looking for a new oportunity
        else:
            self.state.set(AssetState.NULL_POSITION)
            self.logger.info("looking for entry signals")

        # Calculate the minimal amount of data to get accurate predictions
        min_bars = max((
            self.entry_strategy.min_bars, 
            # self.exit_strategy.min_bars, 
            self.trailing_strategy.min_bars))

        train_data = self.broker.get_candles(self.symbol, self.timeframe, min_bars, 1)

        # Train the models
        self.entry_strategy.fit(train_data)
        # self.exit_strategy.fit(train_data)
        self.trailing_strategy.fit(train_data)

    def run(self) -> None:
        """_summary_
        """
        self.logger.info("running bulktraderbot")
        self.set_init_state()
        last_traded_candle_time = None

        # Start a live trading session
        while self.is_active():
            # Retrieve the latest candle data
            candles = self.broker.get_candles(self.symbol, self.timeframe, 2)
            last_candles, current_candle = candles[:-1], candles[-1]

            # Always update data to save computational time and memory
            self.entry_strategy.update_data(last_candles)
            # self.exit_strategy.update_data(last_candles)
            self.trailing_strategy.update_data(last_candles)

            # print(current_candle.close)

            entry_signal = self.entry_strategy.get_entry_signal(current_candle)
            # print(entry_signal.name)
            # entry_signal = EntrySignal.BUY

            # If you get and entry signal either BUY or SELL, create a market order
            if self.state.is_entry(entry_signal) and last_traded_candle_time != current_candle.time:
                entry_params = self.calculate_entry_params(current_candle, entry_signal)
                last_traded_candle_time = current_candle.time

                self.broker.create_order(self.symbol, entry_signal.name, *entry_params)
                self.logger.info(f"{entry_signal.name.lower()} order created")

            orders = self.broker.get_orders(self.symbol)
            positions = self.broker.get_positions(self.symbol)
            # print(positions)

            # Once the bot has created an order, the bot waits till the broker place the position
            # if orders:
            #     self.logger.info(f"position {self.position.ticket} placed")
            #     self.state.next()

            # # The position has been placed
            # if self.state.on_position:
                
            #     # Suddently the position is not there, that means the app closed the position (e.i. manually closed, took SL/TP)                
            #     if not positions:
            #         self.logger.info(f"position {self.position.ticket} closed on app")
            #         self.position = None
            #         self.state.next()
            #         continue
                
            #     # If a exit strategy has been set, generate an exit signal to early out the position
            #     if self.exit_strategy:
            #         exit_signal = self.exit_strategy.get_exit_signal(current_candle, self.position)

            #         if self.state.is_exit(exit_signal):
            #             self.broker.close_position(self.position)
            #             self.logger.info(f"position {self.position.ticket} closed by bot")
            #             self.position = None
            #             self.state.next()
            #             continue
                
            #     # At the end if no early exit, test if the trailing strategy updates the SL/TP levels
            #     if self.trailing_strategy:
            #         stop_loss, take_profit = self.recalculate_stop_levels(current_candle, self.position)

            #         if abs(stop_loss - self.position.sl) >= 0.00001 or abs(take_profit - self.position.tp) >= 0.00001:
            #             self.broker.modify_position(self.position, stop_loss, take_profit)
            #             self.position = self.broker.get_positions(self.symbol)[-1]
            #             self.logger.info(f"position {self.position.ticket} modified {stop_loss=:.5f}, {take_profit=:.5f}")

            sleep(self.leap_in_secs)
        self.logger.info("bulktraderbot session finished")

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
        # risk_pct = self.risk_params["risk_pct"]
        # print(f"{signal=}, {risk_pct=}, {rr_ratio=}")
        stop_loss, take_profit = self.trailing_strategy.get_levels(candle, signal)
        open_price = self.broker.get_current_price(self.symbol, signal.name)

        lot_size = 0.01 # self.broker.calculate_lot_size(self.symbol, open_price, stop_loss, risk_pct)

        return open_price, lot_size, stop_loss, take_profit

    def recalculate_stop_levels(self, candle, position) -> tuple[float, ...]:
        # Calculate new stop level based on whether we are in a long or short position

        # TODO:  mover la estragia de neutralidad dentro de la estrategia, ofrecer diferentes modos al usuario
        # TODO: ofrecer al usuario actualizar take_profit si lo desea
        # lower_nb, upper_nb = self.trailing_strategy.neutral_band

        if position.type == EntrySignal.BUY.value:
            new_stop_loss, _ = self.trailing_strategy.calculate_stop_levels(candle, EntrySignal.BUY)

            # if new stop_loss is not greater than current we don't update
            # if (new_stop_loss > position.price_open + upper_nb and new_stop_loss > position.sl):
            if new_stop_loss > position.sl:
                return new_stop_loss, position.tp
            else:
                return position.sl, position.tp

        elif position.type == EntrySignal.SELL.value:
            new_stop_loss, _ = self.trailing_strategy.calculate_stop_levels(candle, EntrySignal.SELL)

            # if new stop_loss is not lower than current we don't update
            # if (new_stop_loss < position.price_open + lower_nb and new_stop_loss < position.sl):
            if new_stop_loss < position.sl:
                return new_stop_loss, position.tp
            else:
                return position.sl, position.tp
