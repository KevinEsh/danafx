import numpy as np

from trade.metadata import CandleLike, TradePosition, ExitSignal, PositionType
from trade.strategies.abstract import ExitTradingStrategy, Hyperparameter

from datatools.custom import get_recarray, shift, find_supreme

class DirectionChangeExitStrategy(ExitTradingStrategy):
    # config_window = Hyperparameter("window", "numeric", (2, 1000))
    config_neutral_length = Hyperparameter("neutral_length", "numeric", (0, 10))
    config_only_profit = Hyperparameter("only_profit", "boolean")
    config_lag = Hyperparameter("lag", "numeric", (0, 3))

    def __init__(
        self,
        # window: int = 14,
        neutral_length: float = 0,
        only_profit: bool = False,
        lag: int = 1,
    ) -> None:
        super().__init__()
        # self.config_window._check_bounds(window, init=True)
        self.config_neutral_length._check_bounds(neutral_length, init=True)
        self.config_only_profit._check_bounds(only_profit, init=True)
        self.config_lag._check_bounds(lag, init=True)

        # self._window = window
        self._neutral_length = neutral_length
        self._only_profit = only_profit
        self._lag = lag

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

    def fit(self, train_data: np.recarray, train_labels: np.ndarray = None):
        if not self.compound_mode:
            super().fit(train_data, train_labels)

    def update_data(self, new_candles: np.recarray) -> None:
        if not self.is_new_data(new_candles):
            return

        if not self.compound_mode:
            super().update_data(new_candles)

    def generate_exit_signal(self, candle: CandleLike, position: TradePosition) -> ExitSignal:

        # If lag is zero, consider the current candle; else, get the candle from lag periods ago
        if self._lag > 0:
            candle = self.train_data[-self._lag]

        if self._only_profit and (position.price_open >= candle.close):
            return ExitSignal.HOLD

        # Determine the direction and length of this candle
        candle_direction = candle.close >= candle.open
        candle_length = abs(candle.close - candle.open)

        # Compare with the direction of our position
        position_type = PositionType._value2member_map_[position.type]
        position_direction = position_type == PositionType.BUY

        # Generate an exit signal if the directions are opposite and exceeds the threshold
        if position_direction != candle_direction and candle_length > self.neutral_length:
            return ExitSignal.EXIT #ExitSignal.SELL if position_direction else ExitSignal.BUY
        else:
            return ExitSignal.HOLD

    def batch_signals(self, entry_signals: np.recarray, as_prices: bool = False) -> np.recarray:
        if self.train_data is None:
            raise RuntimeError("fit method must be called before")

        n = entry_signals.shape[0]
        m = self.train_data.shape[0]

        if n != m:
            raise ValueError(f"entry_signals lenght must be {m} but received {n}")

        opens = self.train_data.open

        if self._lag == 0:
            candle_buy_directions = self.train_data.high > opens
            candle_sell_directions = self.train_data.low < opens
            
        else:
            candle_directions = self.train_data.close > opens
            candle_breaks = np.abs(self.train_data.close - opens) > self.neutral_length
            
            buy_entry_indexes = np.where(entry_signals.buy)[0]
            sell_entry_indexes = np.where(entry_signals.sell)[0]
        
            buy_exit_indexes = np.where(shift(candle_directions & candle_breaks, self.lag, False))[0]
            sell_exit_indexes = np.where(shift(~candle_directions & candle_breaks, self.lag, False))[0]

            buy_exit_signals = np.zeros_like(n, dtype=bool)
            sell_exit_signals = np.zeros_like(n, dtype=bool)

        for b_entry in buy_entry_indexes:
            b_exit = find_supreme(buy_exit_indexes, b_entry)
            if b_exit is None:
                continue
            buy_exit_signals[b_exit] = True
        
        for s_entry in sell_entry_indexes:
            s_exit = find_supreme(sell_exit_indexes, s_entry)
            if s_exit is None:
                continue
            sell_exit_signals[s_exit] = True

        if not as_prices:
            return get_recarray([buy_exit_signals, sell_exit_signals], names=["buy", "sell"])
        
        if self._lag == 0:
            buy_exit_prices = np.where(buy_exit_signals, opens + self.neutral_length, np.NaN)
            sell_exit_prices = np.where(sell_exit_signals, opens + self.neutral_length, np.NaN)
        else:
            buy_exit_prices = np.where(buy_exit_signals, opens, np.NaN)
            sell_exit_prices = np.where(sell_exit_signals, opens, np.NaN)

        return get_recarray([buy_exit_prices, sell_exit_prices], names=["buy", "sell"])