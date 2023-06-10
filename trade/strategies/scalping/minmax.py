from numpy import ndarray, max as npmax, min as npmin
from datatools.custom import append_recarrays, get_recarray, shift
from datatools.technical import crossingover, crossingunder

from trade.metadata import CandleLike, EntrySignal
from trade.indicators import MAX, MIN
from trade.strategies.abstract import Hyperparameter, TradingStrategy


class MinMaxStrategy(TradingStrategy):
    config_window = Hyperparameter("window", "numeric", (1, 1000))
    config_lag = Hyperparameter("lag", "numeric", (0, 3))
    config_band = Hyperparameter("band", "interval", (-1000, 1000))

    def __init__(
        self,
        window: int = 2,
        lag: int = 1,
        band: tuple = (0, 0),
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window._check_bounds(window, init=True)
        self.config_lag._check_bounds(lag, init=True)
        self.config_band._check_bounds(band, init=True)

        self._window = window
        self._lag = lag
        self._band = band

        self.min_bars = window + lag

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, window):
        self.config_window._check_bounds(window)
        self._window = window
        self.min_bars = window + self._lag

    @property
    def lag(self):
        return self._lag

    @lag.setter
    def lag(self, lag):
        self.config_lag._check_bounds(lag)
        self._lag = lag
        self.min_bars = self._window + lag

    @property
    def band(self):
        return self._band

    @band.setter
    def band(self, band):
        self.config_band._check_bounds(band)
        self._band = band

    def _minmax(self):
        # Precalculate RQK & RBFK. This will save computational time
        self._batch = self.train_data[-self.min_bars:]
        if self._window == 1:
            self._highest = self._batch[-self._lag -1].high
            self._lowest = self._batch[-self._lag -1].low
        else:
            self._highest = MAX(self._batch.high, self._window)[-self._lag -1]
            self._lowest = MIN(self._batch.low, self._window)[-self._lag -1]

    def fit(
        self,
        train_data: CandleLike,
        train_labels: ndarray = None
    ) -> None:
        if not self.compound_mode:
            super().fit(train_data, train_labels)
        self._minmax()

    def update_data(self, new_candles: CandleLike) -> None:
        if not self.is_new_data(new_candles):
            return
        if not self.compound_mode:
            super().update_data(new_candles)
        self._minmax()

    def generate_entry_signal(self, candle: CandleLike) -> int:
        # If lag = 0 that means we need to calculate indicators with current candle
        if self._lag == 0:
            price = candle.close
        else:
            price = self._batch[-self._lag].close

        # print(self._lowest, price, self._highest,)

        # Detect when price breaks level and return signal
        if self._highest + self._band[1] < price:
            return EntrySignal.BUY
        elif self._lowest + self._band[0] > price:
            return EntrySignal.SELL
        else:
            return EntrySignal.NEUTRAL

    def batch_signals(self):
        if self._window == 1:
            highs = self.train_data.high
            lows = self.train_data.low
        else:
            highs = MAX(self.train_data.high, self._window)
            lows = MIN(self.train_data.low, self._window)

        if self._lag == 0:
            buy_signals = shift(highs) + self._band[1] < highs
            sell_signals = shift(lows) + self._band[0] > lows
        else:
            closes = self.train_data.close
            buy_signals = shift(shift(highs) + self._band[1] < closes, self._lag)
            sell_signals = shift(shift(lows) + self._band[0] > closes, self._lag)

        return get_recarray([buy_signals, sell_signals], names=["buy", "sell"])
