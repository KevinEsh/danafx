import numpy as np

from trade.metadata import CandleLike, EntrySignal, TradePosition
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
    config_neutral_band = Hyperparameter("neutral_band", "interval", (-10, 10))
    config_lag = Hyperparameter("lag", "numeric", (0, 3))
    config_source = Hyperparameter("source", "categoric", ("close", "peaks"))

    def __init__(
        self,
        window: int = 14,
        multiplier: float = 1.1,
        neutral_band: float = (0, 0),
        lag: int = 1,
        source: str = "close",
    ) -> None:
        super().__init__()
        self.config_window._check_bounds(window, init=True)
        self.config_multiplier._check_bounds(multiplier, init=True)
        self.config_neutral_band._check_bounds(neutral_band, init=True)
        self.config_lag._check_bounds(lag, init=True)
        self.config_source._check_bounds(source, init=True)

        self._window = window
        self._multiplier = multiplier
        self._neutral_band = neutral_band
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
    def neutral_band(self):
        return self._neutral_band

    @neutral_band.setter
    def neutral_band(self, neutral_band):
        self.config_neutral_band._check_bounds(neutral_band)
        self._neutral_band = neutral_band

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

        self._batch = train_data[-self.min_bars:]
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

    def calculate_stop_level(
        self,
        candle: CandleLike,
        position: TradePosition = None,
        signal: EntrySignal = None,
    ) -> float:
        # Check if the strategy has been fitted
        if self._atrs is None:
            raise ValueError("Strategy has not been fitted. Call 'fit' before 'calculate_stop_level'.")
        print(self.train_data.time[-3:])
        # Get ATR value and price value from current or past data
        if self._lag == 0:
            batch = append_recarrays((self._batch, candle))
            atr = ATR(batch.high, batch.low, batch.close, self._window)[-1]
        else:
            atr = self._atrs[-self._lag]
            candle = self._batch[-self._lag]

        if position is None and signal in (EntrySignal.BUY, EntrySignal.SELL):
            return self._first_stop_level(candle, signal, atr)
        elif position is not None:
            return self._update_stop_level(candle, position, atr)
        else:
            raise ValueError("No position or signal provided")

    def _first_stop_level(self, candle, signal, atr) -> float:
        # Calculate new stop level based on whether we are in a long or short position
        if signal == EntrySignal.BUY:
            price_level = level(candle, self._source, True)
            stop_loss = price_level - self._multiplier * atr

        elif signal == EntrySignal.SELL:
            price_level = level(candle, self._source, False)
            stop_loss = price_level + self._multiplier * atr

        return stop_loss

    def _update_stop_level(self, candle, position, atr) -> float:
        # Calculate new stop level based on whether we are in a long or short position
        price_open = position.price_open
        stop_loss = position.sl
        lower_nb, upper_nb = self.neutral_band

        if position.type == EntrySignal.BUY.value:
            price_level = level(candle, self._source, True)
            new_stop_loss = candle.close - self._multiplier * atr

            # if new stop_loss is not greater than current we don't update
            if (new_stop_loss > price_open + upper_nb and new_stop_loss > stop_loss):
                return new_stop_loss
            else:
                return stop_loss

        elif position.type == EntrySignal.SELL.value:
            price_level = level(candle, self._source, False)
            new_stop_loss = candle.close + self._multiplier * atr

            # if new stop_loss is not lower than current we don't update
            if (new_stop_loss < price_open + lower_nb and new_stop_loss < stop_loss):
                return new_stop_loss
            else:
                return position.sl

    def batch_levels(self):
        ...


if __name__ == "__main__":
    AtrBandTrailingStop()
