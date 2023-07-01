import numpy as np

from trade.metadata import CandleLike, TradePosition, ExitSignal, PositionType
from trade.strategies.abstract import ExitTradingStrategy, Hyperparameter

from datatools.custom import get_recarray, shift, find_supreme, find_index

def get_exits(candles, length, lag, as_prices: bool = False):
    if lag == 0:
        # candle high/low has to break the length
        mask_buy = np.abs(candles.low - candles.open) > length
        mask_sell = np.abs(candles.high - candles.open) > length
    else:
        # candle direction must be oposite and break the length
        candle_directions = candles.close > candles.open
        candle_breaks = np.abs(candles.close - candles.open) > length

        mask_buy = shift(~candle_directions & candle_breaks, lag, False)
        mask_sell = shift(candle_directions & candle_breaks, lag, False)

    # get all exit indexes from masks
    buy_exit_indexes = np.where(mask_buy)[0]
    sell_exit_indexes = np.where(mask_sell)[0]

    if not as_prices:
        # not prices just return indexes
        buy_exits = get_recarray([buy_exit_indexes], names="indexes")
        sell_exits = get_recarray([sell_exit_indexes], names="indexes")
    else:
        # length on lag != 0 is just the candle's open
        length = (length if lag == 0 else 0)
        buy_exit_prices = candles[mask_buy].open - length
        sell_exit_price = candles[mask_sell].open + length

        buy_exits = get_recarray([buy_exit_indexes, buy_exit_prices], names=['indexes', 'prices'])
        sell_exits = get_recarray([sell_exit_indexes, sell_exit_price], names=['indexes', 'prices'])

    return buy_exits, sell_exits

def get_entries(entry_signals, as_prices: bool = False):
    if not as_prices:
        # entry signals are booleans arrays so extract indexes where you find Trues
        buy_entry_indexes = np.where(entry_signals.buy)[0]
        sell_entry_indexes = np.where(entry_signals.sell)[0]

        # transform them to recarray
        buy_entries = get_recarray([buy_entry_indexes], names="indexes")
        sell_entries = get_recarray([sell_entry_indexes], names="indexes")
    else:
        # entry signals are NaNs or prices get the indexes and prices. this means remove all NaNs
        mask_buy = ~np.isnan(entry_signals.buy)
        mask_sell = ~np.isnan(entry_signals.sell)

        # get all non-NaNs indexes
        buy_entry_indexes = np.where(mask_buy)[0]
        sell_entry_indexes = np.where(mask_sell)[0]

        # get all prices
        buy_entry_prices = entry_signals.buy[mask_buy]
        sell_entry_prices = entry_signals.sell[mask_sell]

        # transform them to recarray
        buy_entries = get_recarray([buy_entry_indexes, buy_entry_prices], names=['indexes', 'prices'])
        sell_entries = get_recarray([sell_entry_indexes, sell_entry_prices], names=['indexes', 'prices'])
    
    return buy_entries, sell_entries

def get_exit_prices(
    buy_exit_indexes,
    sell_exit_indexes,
    candles,
    length, 
    lag,
    ):
    length = (length if lag == 0 else 0)
    buy_exit_prices = candles[buy_exit_indexes].open - length
    sell_exit_price = candles[sell_exit_indexes].open + length
    return buy_exit_prices, sell_exit_price


def match_signals(
    entries, 
    exits,
    n: int,
    lag: int,
    as_prices: bool = False,
    is_buy: bool = False,
    only_profit: bool = False,
    last_price: float = np.NaN,
) -> np.recarray:
    # Create new arrays to store exit information
    exit_indexes =  exits.indexes
    confirmed_exit_indexes = np.full(n, np.NaN)

    if as_prices:
        exit_prices = exits.prices
        confirmed_exit_prices = np.full(n, np.NaN)

    last_index = n - 1
    for entry_i, entry_p in entries:
        if entry_i >= last_index: continue

        if only_profit:
            exit_i = find_exit_profit(entry_i + lag, entry_p, exit_indexes, exit_prices, is_buy, as_index=True)
        else:
            exit_i = find_supreme(entry_i + lag, exit_indexes, as_index=True)

        if exit_i is None:
            confirmed_exit_indexes[entry_i] = last_index
            if as_prices:
                confirmed_exit_prices[entry_i] = last_price
        else:
            confirmed_exit_indexes[entry_i] = exit_indexes[exit_i]
            if as_prices:
                confirmed_exit_prices[entry_i] = exit_prices[exit_i]

    return (confirmed_exit_indexes, confirmed_exit_prices) if as_prices else confirmed_exit_indexes


def find_exit_profit(
    entry_index: int,
    entry_price: float,
    exit_indexes: np.ndarray,
    exit_prices: np.ndarray,
    is_buy: bool,
    as_index: bool = False,
) -> int:
    # Combine the conditions using the logical AND operator
    reset_indexes = np.arange(exit_indexes.shape[0])
    possible_exit_indexes = reset_indexes[exit_indexes >= entry_index]

    if is_buy:
        confirmation_mask = exit_prices[possible_exit_indexes] > entry_price
    else:
        confirmation_mask = exit_prices[possible_exit_indexes] < entry_price

    if np.any(confirmation_mask):
        first_confirmation = np.argmax(confirmation_mask)
        exit_index = possible_exit_indexes[first_confirmation]
        return exit_index if as_index else int(exit_indexes[exit_index])
    return None

# def match_prices_profit(
#     entry_indexes,
#     entry_prices,
#     exit_indexes,
#     exit_prices,
#     candles,
#     length: float,
#     is_buy: bool,
# ) -> np.recarray:
#     n = candles.shape[0]
#     exit_signals_profit = np.full(n, np.NaN)
#     exit_prices_profit = np.full(n, np.NaN)

#     for entry_i, entry_p in zip(entry_indexes, entry_prices):
#         exit_i = find_exit_profit(entry_i, entry_p, exit_indexes, exit_prices, is_buy)
#         exit_i = n - 1 if (exit_i is None) else exit_i #TODO: poner un parametro para que el algo siempre cierre todas las operacion con la ultima vela
#         print(entry_i, exit_i)
#         exit_signals_profit[entry_i] = exit_i
#         exit_prices_profit[entry_i] = candles[exit_i].open + length

#     return exit_signals_profit, exit_prices_profit


class DirectionChangeExitStrategy(ExitTradingStrategy):
    # config_window = Hyperparameter("window", "numeric", (2, 1000))
    config_length = Hyperparameter("length", "numeric", (0, 10))
    config_lag = Hyperparameter("lag", "numeric", (0, 3))
    config_only_profit = Hyperparameter("only_profit", "boolean")

    def __init__(
        self,
        # window: int = 14,
        length: float = 0,
        lag: int = 1,
        only_profit: bool = False,
    ) -> None:
        super().__init__()
        # self._window = window
        self.length = length
        self.lag = lag
        self.only_profit = only_profit
        self.min_bars = lag + 1

    # @property
    # def window(self):
    #     return self._window

    # @window.setter
    # def window(self, window):
    #     self.config_window._check_bounds(window)
    #     self._window = window

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, length):
        self.config_length._check_bounds(length)
        self._length = length

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
        if (position_direction != candle_direction) and (candle_length > self.length):
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
        if n != m:
            raise ValueError(f"entry_signals lenght must be {m} but received {n}")

        buy_entries, sell_entries = get_entries(entry_signals, as_prices)
        buy_exits, sell_exits = get_exits(self.train_data, self._length, self._lag, as_prices)

        if not as_prices:
            buy_exit_signals = match_signals(buy_entries, buy_exits, n, self._lag, True, True)
            sell_exit_signals = match_signals(sell_entries, sell_exits, n, self._lag, True, False)
            return get_recarray([buy_exit_signals, sell_exit_signals], names=["buy", "sell"])

        else:
            last_price = self.train_data[-1].close
            if self._only_profit:
                buy_exit_prices = match_signals(buy_entries, buy_exits, n, self._lag, True, True, True, last_price)
                sell_exit_prices = match_signals(sell_entries, sell_exits, n, self._lag, True, False, True, last_price)
            else:
                buy_exit_prices = match_signals(buy_entries, buy_exits, n, self._lag, True, True, last_price=last_price)
                sell_exit_prices = match_signals(sell_entries, sell_exits, n, self._lag, True, False, last_price=last_price)
            return get_recarray([*buy_exit_prices, *sell_exit_prices], names=["buy", "buy_price", "sell", "sell_price"])

        # if self._lag == 0:
        #     buy_exit_prices = np.where(buy_exit_signals, opens - self.length, np.NaN)
        #     sell_exit_prices = np.where(sell_exit_signals, opens + self.length, np.NaN)
        # else:
        #     buy_exit_prices = np.where(buy_exit_signals, opens, np.NaN)
        #     sell_exit_prices = np.where(sell_exit_signals, opens, np.NaN)



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