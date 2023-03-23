from broker import BrokerSession
from state_machine import TradingStateMachine
from time import sleep


class TradingStrategy:
    def __init__(self, symbol: str) -> None:
        pass

    def generate_signal(data):
        if data.price >= 1.71:
            return 1
        else:
            return 0


class TraderBot:

    def __init__(self, login_settings) -> None:
        from setup import get_settings

        login_settings = get_settings("settings/demo/login.json")
        # trading_settings = get_settings("settings/demo/trading.json")

        mt5_login_settings = login_settings["mt5_login"]

        symbol = "EURUSD"
        # Start MT5
        self.broker = BrokerSession()
        self.broker.start_session(mt5_login_settings)
        self.broker.initialize_symbols([symbol])
        self.state = TradingStateMachine(symbol)
        self.symbol = symbol
        self.timeframe = "M1"
        self.open_positions = None
        self.seconds_leap = 1

    def run(self) -> None:
        """_summary_
        """
        # Select symbol to run strategy on
        # symbol_for_strategy = self.live_trading_symbols[0]  # TODO: parallel computing with all symbols
        # Set up a previous time variable

        # Start a while loop to poll MT5
        while True:  # TODO:self._is_active():

            # Retrieve the current candle data
            latest_tick = self.broker.get_ticks(
                symbol=self.symbol,
                number_of_ticks=1,
                format_time=False
            )
            latest_candle = self.broker.get_candles(
                symbol=self.symbol,
                timeframe=self.timeframe,
                number_of_candles=1,
                format_time=True
            )

            print(latest_candle)
            # print(latest_tick)

            # if self.state.no_position():
            #     entry_signal = self.strategy.generate_signal(latest_tick)
            #     if entry_signal != 0:
            #         new_position = self.create_position(entry_signal)
            #         self.state.transition(entry_signal)

            # elif self.state.on_long_position():
            #     pass
            #     #    strategy.update_trailing_stop(order=position, trailing_stop_pips=10, pip_size=trading_settings['pip_size'])
            # elif self.state.on_short_position():
            #     pass

            sleep(self.seconds_leap)

    def set_init_state(self):
        # self.open_positions = self.broker.get_open_positions()
        # self.open_orders = self.broker.get_open_orders()
        pass


if __name__ == "__main__":
    symbol = "EURUSD"
    trader = TraderBot(symbol)
    trader.run()
