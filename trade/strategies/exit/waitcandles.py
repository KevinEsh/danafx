import numpy as np

from trade.metadata import CandleLike, TradePosition, ExitSignal, PositionType, TimeFrames
from trade.strategies.abstract import ExitTradingStrategy, Hyperparameter

from datatools.custom import get_recarray

def candle_diff(star_time, end_time, timeframe):
    
    if timeframe == 'MN1':
        time_per_candle = 2592000
    else:
        if timeframe[0] == 'M':
            time_per_candle = 60
        elif timeframe[0] == 'H':
            time_per_candle = 3600
        elif timeframe[0] == 'D':
            time_per_candle = 86400
        elif timeframe[0] == 'W':
            time_per_candle = 604800
        time_per_candle *= int(timeframe[1:])
    return (end_time - star_time) // time_per_candle

class WaitCandlesExitStrategy(ExitTradingStrategy):
    config_timeframe = Hyperparameter("timeframe", "categoric", TimeFrames._member_names_)
    config_n_candles_losse = Hyperparameter("n_candles_losse", "numeric", (1, 1e7))
    config_n_candles_strict = Hyperparameter("n_candles_strict", "numeric", (1, 1e7))
    config_pippetes = Hyperparameter("pippetes", "numeric", (1, 1e7))
    config_point = Hyperparameter("point", "numeric", (1e-5, 1e-1))

    def __init__(
        self,
        timeframe: str,
        n_candles_losse: int = 1,
        n_candles_strict: int = 1,
        pippetes: int = 10,
        point: float = 0.00001,
    ) -> None:
        super().__init__()
        self.timeframe = timeframe
        self.n_candles_losse = n_candles_losse
        self.n_candles_strict = n_candles_strict
        self.pippetes = pippetes
        self.point = point
        self.min_bars = 1

    @property
    def timeframe(self):
        return self._timeframe

    @timeframe.setter
    def timeframe(self, timeframe):
        self.config_timeframe._check_bounds(timeframe)
        self._timeframe = timeframe

    @property
    def n_candles_losse(self):
        return self._n_candles_losse

    @n_candles_losse.setter
    def n_candles_losse(self, n_candles_losse):
        self.config_n_candles_losse._check_bounds(n_candles_losse)
        self._n_candles_losse = n_candles_losse

    @property
    def n_candles_strict(self):
        return self._n_candles_strict

    @n_candles_strict.setter
    def n_candles_strict(self, n_candles_strict):
        self.config_n_candles_strict._check_bounds(n_candles_strict)
        self._n_candles_strict = n_candles_strict

    @property
    def pippetes(self):
        return self._pippetes

    @pippetes.setter
    def pippetes(self, pippetes):
        self.config_pippetes._check_bounds(pippetes)
        self._pippetes = pippetes

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, point):
        self.config_point._check_bounds(point)
        self._point = point

    def generate_exit_signal(
        self,
        candle: CandleLike,
        position: TradePosition,
    ) -> ExitSignal:
        margin = self._point * self._pippetes
        n_candles = candle_diff(candle.time, position.time, self._timeframe)

        position_type = PositionType._value2member_map_[position.type]
        position_direction = position_type == PositionType.BUY

        if n_candles >= self._n_candles_strict:
            return ExitSignal.EXIT
        elif n_candles < self._n_candles_losse:
            return ExitSignal.HOLD
        elif position_direction and (position.price_open >= candle.close + margin):
            return ExitSignal.EXIT
        elif not position_direction and (position.price_open <= candle.close - margin):
            return ExitSignal.EXIT
        else:
            return ExitSignal.HOLD

    def batch_exit_signals(
        self, 
        entry_signals: np.recarray, 
    ) -> np.recarray:
        if self.train_data is None:
            raise RuntimeError("fit method must be called before")

        n = entry_signals.shape[0]
        m = self.train_data.shape[0]
        if n != m:
            raise ValueError(f"entry_signals lenght must be {m} but received {n}")

        opens = self.train_data.open
        margin = self._point * self._pippetes

        buy_exit_indexes = entry_signals.buy_index + self.n_candles_strict
        sell_exit_indexes = entry_signals.sell_index + self.n_candles_strict

        # valid exits must be less than the last candle
        valid_buy_mask = buy_exit_indexes < n
        valid_sell_mask = sell_exit_indexes < n

        # Initialize the result arrays with np.nan
        buy_exit_prices = np.full_like(buy_exit_indexes, np.nan, dtype=float)
        sell_exit_prices = np.full_like(sell_exit_indexes, np.nan, dtype=float)

        # Assign valid exits to the prices arrays
        buy_exit_prices[valid_buy_mask] = opens[buy_exit_indexes[valid_buy_mask]]
        sell_exit_prices[valid_sell_mask] = opens[sell_exit_indexes[valid_sell_mask]]

        return get_recarray([
            buy_exit_indexes, buy_exit_prices, sell_exit_indexes, sell_exit_prices], 
            names=['buy_index', 'buy_price', 'sell_index', 'sell_price'])
