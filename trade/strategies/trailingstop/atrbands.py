import numpy as np

from trade.metadata import CandleLike, EntrySignal
from trade.indicators import ATR, get_stable_min_bars
from trade.strategies.abstract import TrailingStopStrategy, Hyperparameter

from datatools.custom import append_recarrays


def level(candle, source, is_long: bool):
    if source == "peaks":
        return candle.close
    else:
        return candle.low if is_long else candle.high


class AtrBandTrailingStop(TrailingStopStrategy):
    config_window = Hyperparameter("window", "numeric", (2, 1000))
    config_multiplier = Hyperparameter("multiplier", "numeric", (0, 100))
    config_rr_ratio = Hyperparameter("rr_ratio", "numeric", (0, 10))
    config_lag = Hyperparameter("lag", "numeric", (0, 3))
    config_source = Hyperparameter("source", "categorical", ("close", "peaks"))

    def __init__(
        self,
        window: int = 14,
        multiplier: float = 1.1,
        rr_ratio: float = 2,
        lag: int = 1,
        source: str = "close",
    ) -> None:
        super().__init__()
        self.config_window._check_bounds(window, init=True)
        self.config_multiplier._check_bounds(multiplier, init=True)
        self.config_rr_ratio._check_bounds(rr_ratio, init=True)
        self.config_lag._check_bounds(lag, init=True)
        self.config_source._check_bounds(source, init=True)

        self._window = window
        self._multiplier = multiplier
        self._rr_ratio = rr_ratio
        self._lag = lag
        self._source = source

        self.min_bars = get_stable_min_bars("ATR", window) + lag

        self._batch = None
        self._atrs = None

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, window):
        self.config_window._check_bounds(window)
        self._window = window

    @property
    def multiplier(self):
        return self._multiplier

    @multiplier.setter
    def multiplier(self, multiplier):
        self.config_multiplier._check_bounds(multiplier)
        self._multiplier = multiplier

    @property
    def rr_ratio(self):
        return self._rr_ratio

    @rr_ratio.setter
    def rr_ratio(self, rr_ratio):
        self.config_rr_ratio._check_bounds(rr_ratio)
        self._rr_ratio = rr_ratio

    @property
    def lag(self):
        return self._lag

    @lag.setter
    def lag(self, lag):
        self.config_lag._check_bounds(lag)
        self._lag = lag

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        self.config_source._check_bounds(source)
        self._source = source

    def fit(self, train_data: np.recarray, train_labels: np.ndarray = None):
        # Pre-calculate ATR
        if not self.compound_mode:
            super().fit(train_data, train_labels)

        self._batch = self.train_data[-self.min_bars:]
        self._atrs = ATR(
            self._batch.high,
            self._batch.low,
            self._batch.close,
            self._window)
        print(self._atrs)

    def update_data(self, new_candles: np.recarray) -> None:
        if not self.is_new_data(new_candles):
            return

        if not self.compound_mode:
            super().update_data(new_candles)

        self._batch = self.train_data[-self.min_bars:]
        self._atrs = ATR(
            self._batch.high,
            self._batch.low,
            self._batch.close,
            self._window)

    def calc_risk_levels(self, price: float, rr_ratio: float, risk_pct: float):

        return lot_size, stop_loss, take_profit

    def calculate_stop_level(self, candle: CandleLike) -> float:
        # Check if the strategy has been fitted
        if self._atrs is None:
            raise ValueError("Strategy has not been fitted. Call 'fit' before 'calculate_stop_level'.")

        # Get ATR value and price value from current or past data
        if self._lag == 0:
            batch = append_recarrays((self._batch, candle))
            atr = ATR(batch.high, batch.low, batch.close, self._window)[-1]
        else:
            atr = self._atrs[-self._lag]
            candle = self._batch[-self._lag]

        price_open = self.position.price_open
        stop_loss = self.position.sl

        # Calculate new stop level based on whether we are in a long or short position
        if self.position.type == EntrySignal.BUY.value:
            # highest_price = np.max(self._batch.close)
            price_level = level(candle, self._source, True)
            new_stop_loss = price_level - self._multiplier * atr

            # if new stop_loss is not greater than current we don't update
            if price_level < price_open + self._tolerance or new_stop_loss <= stop_loss:
                return stop_loss

        elif self.position.type == EntrySignal.SELL.value:
            # lowest_price = np.min(self._batch.close)
            price_level = level(candle, self._source, False)
            stop_loss = price_level + self._multiplier * atr

            # if new stop_loss is not lower than current we don't update
            if stop_loss >= self.position.sl:
                return self.position.sl

        return stop_loss

    def batch_levels(self):
        ...
