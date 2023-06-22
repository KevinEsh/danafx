import numpy as np

from trade.metadata import CandleLike, TradePosition, ExitSignal, PositionType
from trade.strategies.abstract import ExitTradingStrategy, Hyperparameter

from datatools.custom import get_recarray, shift, find_supreme

class DirectionChangeExitStrategy(ExitTradingStrategy):
    # config_window = Hyperparameter("window", "numeric", (2, 1000))
    config_neutral_length = Hyperparameter("neutral_length", "numeric", (0, 10))
    config_lag = Hyperparameter("lag", "numeric", (0, 3))
    config_only_profit = Hyperparameter("only_profit", "boolean")

    def __init__(
        self,
        # window: int = 14,
        neutral_length: float = 0,
        lag: int = 1,
        only_profit: bool = False,
    ) -> None:
        super().__init__()
        # self.config_window._check_bounds(window, init=True)
        self.config_neutral_length._check_bounds(neutral_length, init=True)
        self.config_lag._check_bounds(lag, init=True)
        self.config_only_profit._check_bounds(only_profit, init=True)

        # self._window = window
        self._neutral_length = neutral_length
        self._lag = lag
        self._only_profit = only_profit

        self.min_bars = lag

    # @property
    # def window(self):
    #     return self._window

    # @window.setter
    # def window(self, window):
    #     self.config_window._check_bounds(window)
    #     self._window = window

    @property
    def neutral_length(self):
        return self._neutral_length

    @neutral_length.setter
    def neutral_length(self, neutral_length):
        self.config_neutral_length._check_bounds(neutral_length)
        self._neutral_length = neutral_length

    @property
    def only_profit(self):
        return self._only_profit

    @only_profit.setter
    def only_profit(self, only_profit):
        self.config_only_profit._check_bounds(only_profit)
        self._only_profit = only_profit

    @property
    def lag(self):
        return self._lag

    @lag.setter
    def lag(self, lag):
        self.config_lag._check_bounds(lag)
        self._lag = lag

    def generate_exit_signal(self, candle: CandleLike, position: TradePosition) -> ExitSignal:

        # If lag is zero, consider the current candle; else, get the candle from lag periods ago
        if self._lag > 0:
            candle = self.train_data[-self._lag]

        if candle.time <= position.time:
            return ExitSignal.HOLD

        # Determine the direction and length of this candle
        candle_direction = candle.close >= candle.open
        candle_length = abs(candle.close - candle.open)

        # Compare with the direction of our position
        position_type = PositionType._value2member_map_[position.type]
        position_direction = position_type == PositionType.BUY

        if self._only_profit:
            if position_direction and (position.price_open >= candle.close):
                return ExitSignal.HOLD
            elif not position_direction and (position.price_open <= candle.close):
                return ExitSignal.HOLD
        # print(candle_direction, position_direction, candle.close, position.price_open, candle_length)
        
        # Generate an exit signal if the directions are opposite and exceeds the threshold
        if (position_direction != candle_direction) and (candle_length > self.neutral_length):
            return ExitSignal.EXIT #ExitSignal.SELL if position_direction else ExitSignal.BUY
        else:
            return ExitSignal.HOLD

    def batch_exit_signals(
        self, 
        entry_signals: np.recarray, 
        as_prices: bool = False
    ) -> np.recarray:
        if self.train_data is None:
            raise RuntimeError("fit method must be called before")

        n = entry_signals.shape[0]
        m = self.train_data.shape[0]

        if entry_signals.shape[0] != self.train_data.shape[0]:
            raise ValueError(f"entry_signals lenght must be {m} but received {n}")

        opens = self.train_data.open

        if not as_prices:
            buy_entry_indexes = np.where(entry_signals.buy)[0]
            sell_entry_indexes = np.where(entry_signals.sell)[0]
        else:
            buy_entry_indexes = np.where(~np.isnan(entry_signals.buy))[0]
            sell_entry_indexes = np.where(~np.isnan(entry_signals.sell))[0]

        if self._lag == 0:
            candle_buy_breaks = np.abs(self.train_data.low - opens) > self.neutral_length
            candle_sell_breaks = np.abs(self.train_data.high - opens) > self.neutral_length

            buy_exit_indexes = np.where(candle_buy_breaks)[0]
            sell_exit_indexes = np.where(candle_sell_breaks)[0]
        else:
            candle_directions = self.train_data.close > opens
            candle_breaks = np.abs(self.train_data.close - opens) > self.neutral_length
        
            buy_exit_indexes = np.where(shift(~candle_directions & candle_breaks, self.lag, False))[0]
            sell_exit_indexes = np.where(shift(candle_directions & candle_breaks, self.lag, False))[0]

        buy_exit_signals = np.zeros(n, dtype=bool)
        sell_exit_signals = np.zeros(n, dtype=bool)

        for b_entry in buy_entry_indexes:
            b_exit = find_supreme(buy_exit_indexes, b_entry + self._lag)
            if b_exit is not None:
                buy_exit_signals[b_exit] = True

        for s_entry in sell_entry_indexes:
            s_exit = find_supreme(sell_exit_indexes, s_entry + self._lag)
            if s_exit is not None:
                sell_exit_signals[s_exit] = True

        if not as_prices:
            return get_recarray([buy_exit_signals, sell_exit_signals], names=["buy", "sell"])

        if self._lag == 0:
            buy_exit_prices = np.where(buy_exit_signals, opens - self.neutral_length, np.NaN)
            sell_exit_prices = np.where(sell_exit_signals, opens + self.neutral_length, np.NaN)
        else:
            buy_exit_prices = np.where(buy_exit_signals, opens, np.NaN)
            sell_exit_prices = np.where(sell_exit_signals, opens, np.NaN)


        # if self._only_profit:
        #     for b_entry in buy_entry_indexes:
        #         b_exit = find_supreme(buy_exit_indexes, b_entry + self._lag)
        #         if b_exit is not None:
        #             buy_exit_signals[b_exit] = True

        #     for s_entry in sell_entry_indexes:
        #         s_exit = find_supreme(sell_exit_indexes, s_entry + self._lag)
        #         if s_exit is not None:
        #             sell_exit_signals[s_exit] = True
            

        return get_recarray([buy_exit_prices, sell_exit_prices], names=["buy", "sell"])