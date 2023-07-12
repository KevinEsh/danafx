import numpy as np

from trade.metadata import CandleLike, TradePosition, PositionType, EntrySignal
from trade.strategies.abstract import TrailingStopStrategy, Hyperparameter

from datatools.custom import get_recarray

class SimpleTrailingStrategy(TrailingStopStrategy):
    config_pippetes_stop = Hyperparameter("pippetes_stop", "numeric", (1, 1e10))
    config_pippetes_take = Hyperparameter("pippetes_take", "numeric", (0, 1e10))
    config_point = Hyperparameter("point", "numeric", (1e-5, 1))

    def __init__(
        self,
        pippetes_stop: int,
        pippetes_take: int = None,
        point: float = 0.00001,
    ) -> None:
        super().__init__()
        self.pippetes_stop = pippetes_stop
        self.pippetes_take = pippetes_take
        self.point = point
        self.min_bars = 1

    @property
    def pippetes_stop(self):
        return self._pippetes_stop

    @pippetes_stop.setter
    def pippetes_stop(self, pippetes_stop):
        self.config_pippetes_stop._check_bounds(pippetes_stop)
        self._pippetes_stop = pippetes_stop

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, point):
        self.config_point._check_bounds(point)
        self._point = point

    @property
    def pippetes_take(self):
        return self._pippetes_take

    @pippetes_take.setter
    def pippetes_take(self, pippetes_take):
        self.config_pippetes_take._check_bounds(pippetes_take)
        self._pippetes_take = pippetes_take

    def get_levels(self, candle: CandleLike, signal: EntrySignal):        
        if signal == EntrySignal.BUY:
            stop_level = candle.close - self._pippetes_stop * self._point
            take_level = candle.close + self._pippetes_take * self._point
        else:
            stop_level = candle.close + self._pippetes_stop * self._point
            take_level = candle.close - self._pippetes_take * self._point

        return stop_level, take_level
    
    def get_adjustment(self, candle: CandleLike, position: TradePosition) -> float:
        return None, None

    def batch_levels(self, entry_signals: np.recarray) -> np.recarray:
        adj_stop = self._pippetes_stop * self._point
        adj_take = self._pippetes_stop * self._point

        stop_buy = entry_signals.buy_price - adj_stop
        take_buy = entry_signals.buy_price + adj_take

        stop_sell = entry_signals.sell_price + adj_stop
        take_sell = entry_signals.sell_price - adj_take
        return get_recarray(
            [stop_buy, take_buy, stop_sell, take_sell], 
            names=['buy_stop', 'buy_take', 'sell_stop', 'sell_take'])

    def batch_exit_signals(self, entry_signals: np.recarray) -> np.recarray:
        if self.train_data is None:
            raise RuntimeError("fit method must be called before")

        n = entry_signals.shape[0]
        m = self.train_data.shape[0]
        if n != m:
            raise ValueError(f"entry_signals lenght must be {m} but received {n}")

        highs = self.train_data.high
        lows = self.train_data.low
        adj_stop = self._pippetes_stop * self._point
        adj_take = self._pippetes_take * self._point

        # get buy exits
        buy_indexes = np.where(entry_signals.buy_index)[0]
        buy_exit_indexes = np.full(n, np.NaN)
        buy_exit_prices = np.full(n, np.NaN)

        for entry_i in buy_indexes:
            entry_price = entry_signals.buy_price[entry_i]
            stop_level = entry_price - adj_stop
            take_level = entry_price + adj_take

            stop_touches = lows[entry_i:] <= stop_level
            take_touches = highs[entry_i:] >= take_level

            stop_index = np.argmax(stop_touches) + entry_i if np.any(stop_touches) else None 
            take_index = np.argmax(take_touches) + entry_i if np.any(take_touches) else None 
        
            if stop_index is None and take_index is None:
                continue
            
            if stop_index is None:
                buy_exit_indexes[entry_i] = take_index
                buy_exit_prices[entry_i] = take_level
            elif take_index is None:
                buy_exit_indexes[entry_i] = stop_index
                buy_exit_prices[entry_i] = stop_level
            else:
                if stop_index == take_index or stop_index < take_index:
                    buy_exit_indexes[entry_i] = stop_index
                    buy_exit_prices[entry_i] = stop_level
                else:
                    buy_exit_indexes[entry_i] = take_index
                    buy_exit_prices[entry_i] = take_level

        # get sell exits
        sell_indexes = np.where(entry_signals.sell_index)[0]
        sell_exit_indexes = np.full(n, np.NaN)
        sell_exit_prices = np.full(n, np.NaN)

        for entry_i in sell_indexes:
            entry_price = entry_signals.sell_price[entry_i]
            stop_level = entry_price + adj_stop
            take_level = entry_price - adj_take

            stop_touches = highs[entry_i:] >= stop_level
            take_touches = lows[entry_i:] <= take_level

            stop_index = np.argmax(stop_touches) + entry_i if np.any(stop_touches) else None 
            take_index = np.argmax(take_touches) + entry_i if np.any(take_touches) else None

            if stop_index is None and take_index is None:
                continue
            
            if stop_index is None:
                sell_exit_indexes[entry_i] = take_index
                sell_exit_prices[entry_i] = take_level
            elif take_index is None:
                sell_exit_indexes[entry_i] = stop_index
                sell_exit_prices[entry_i] = stop_level
            else:
                if stop_index == take_index or stop_index < take_index:
                    sell_exit_indexes[entry_i] = stop_index
                    sell_exit_prices[entry_i] = stop_level
                else:
                    sell_exit_indexes[entry_i] = take_index
                    sell_exit_prices[entry_i] = take_level

        return get_recarray([
            buy_exit_indexes, buy_exit_prices, 
            sell_exit_indexes, sell_exit_prices], 
            names=["buy_index", "buy_price", "sell_index", "sell_price"])

