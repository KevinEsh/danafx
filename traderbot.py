from time import sleep
from logging import log

from trade.broker import BrokerSession
from trade.state_machine import AssetStateMachine
from trade.strategies import MovingAverageStrategy

# class TradingStrategy:
#     def __init__(self) -> None:
#         pass
#         self.price = 1.08105
#         self.position = None

#     def get_entry_signal(self, data):
#         if data.close > self.price:
#             return 1
#         # if data.close < self.price:
#         #     return -1
#         else:
#             return 0

#     def get_exit_signal(self, data):
#         if data.close >= self.price + 0.00001 * 5:
#             return 1
#         # elif data.close <= self.price - 0.0001 * 2:
#         #     return 1
#         else:
#             return 0


class SingleTraderBot:

    def __init__(
        self,
        symbol: str,
        broker: BrokerSession,
        timeframe: str,
        strategy: str,
        leap_in_secs: float,
        risk_params: dict,
    ) -> None:
        from setup import get_settings

        login_settings = get_settings("settings/demo/login.json")
        # trading_settings = get_settings("settings/demo/trading.json")

        mt5_login_settings = login_settings["mt5_login"]

        symbol = "EURUSD"
        # Start MT5 App & Broker
        self.broker = BrokerSession()
        self.broker.start_session(mt5_login_settings)
        self.broker.initialize_symbols([symbol])
        self.state = AssetStateMachine(symbol)
        self.symbol = symbol
        self.timeframe = "M1"
        self.leap_in_secs = 5
        self.strategy = MovingAverageStrategy(20, 200)
        self.risk_params = {
            "pips": 20,
            "risk_tolerance": 0.02,
            "rr_ratio": 2,
        }

    def add_strategy(self, strategy) -> None:
        pass

    def run(self) -> None:
        """_summary_
        """
        # Select symbol to run strategy on
        # symbol_for_strategy = self.live_trading_symbols[0]  # TODO: parallel computing with all symbols
        # Set up a previous time variable

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
            print(current_candle.close)

            # Always update data to save computational time and memory
            self.strategy.update_data(last_candles)

            if self.state.no_position:

                # If no position is placed, create an entry signal, this signal could be buy, sell or neutral
                entry_signal = self.strategy.get_entry_signal(current_candle)
                print(entry_signal)

                if self.state.is_entry(entry_signal):
                    print(f"Creating {entry_signal.name} order for {self.symbol}")
                    order_type = entry_signal.name.lower()  # TODO
                    order_params = self.broker.calc_risk_params(self.symbol, order_type, **self.risk_params)
                    self.order = self.broker.create_order(self.symbol, order_type, *order_params)
                    self.state.transition(entry_signal)
                    print(f"Order created for {self.symbol}")

            if self.state.awaiting_position:

                self.strategy.position = self.broker.get_positions(self.symbol)[-1]
                print(f"Position {self.strategy.position.ticket} placed for {self.symbol}")
                self.state.transition(entry_signal)

            if self.state.on_long or self.state.on_short:

                exit_signal = self.strategy.get_exit_signal(current_candle)

                if self.state.is_exit(exit_signal):
                    self.broker.close_position(self.strategy.position, order_type)
                    self.strategy.position = None
                    self.state.transition(exit_signal)
                    print(f"Position {self.strategy.position.ticket} closed for {self.symbol}")

                else:
                    # strategy.update_trailing_stop(order=position, trailing_stop_pips=10, pip_size=trading_settings['pip_size'])
                    pass

            sleep(self.leap_in_secs)

    def set_init_state(self):
        # self.open_positions = self.broker.get_open_positions()
        # self.open_orders = self.broker.get_open_orders()
        pass


if __name__ == "__main__":
    symbol = "EURUSD"
    trader = SingleTraderBot(symbol)
    trader.run()
