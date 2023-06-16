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
    config_rr_ratio = Hyperparameter("rr_ratio", "numeric", (0, 100))

    def __init__(
        self,
        window: int = 14,
        multiplier: float = 1.1,
        neutral_band: float = (0, 0),
        rr_ratio: float = None,
        lag: int = 1,
    ) -> None:
        super().__init__()
        self.config_window._check_bounds(window, init=True)
        self.config_multiplier._check_bounds(multiplier, init=True)
        self.config_neutral_band._check_bounds(neutral_band, init=True)
        self.config_lag._check_bounds(lag, init=True)
        self.config_rr_ratio._check_bounds(rr_ratio, init=True)

        self._window = window
        self._multiplier = multiplier
        self._neutral_band = neutral_band
        self._lag = lag
        self._rr_ratio = rr_ratio

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
    def rr_ratio(self):
        return self._rr_ratio

    @rr_ratio.setter
    def rr_ratio(self, rr_ratio):
        self.config_rr_ratio._check_bounds(rr_ratio)
        self._rr_ratio = rr_ratio

    def fit(self, train_data: np.recarray, train_labels: np.ndarray = None):
        if not self.compound_mode:
            super().fit(train_data, train_labels)

        # Pre-calculate ATR
        self._batch = train_data[-self.min_bars:]
        self._atrs = ATR(
            self._batch.high,
            self._batch.low,
            self._batch.close,
            self._window)

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

    def get_adjustment(self, candle):
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

        return self._multiplier * atr, candle

    def batch_levels(self):
        ...


if __name__ == "__main__":
    AtrBandTrailingStop()
