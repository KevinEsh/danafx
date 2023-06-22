from numpy import ndarray, recarray, where, NaN
from datatools.custom import get_recarray, shift

from trade.indicators import MAX, MIN
from trade.metadata import CandleLike, EntrySignal
from trade.strategies.abstract import Hyperparameter, EntryTradingStrategy


class ZigZagEntryStrategy(EntryTradingStrategy):
    config_window = Hyperparameter("window", "numeric", (1, 1000))
    config_lag = Hyperparameter("lag", "numeric", (0, 3))
    config_band = Hyperparameter("band", "interval", (-1000, 1000))

    def __init__(
        self,
        window: int = 2,
        lag: int = 1,
        band: tuple = (0, 0),
        neutral_length: float = 0
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window._check_bounds(window, init=True)
        self.config_lag._check_bounds(lag, init=True)
        self.config_band._check_bounds(band, init=True)

        self._window = window
        self._lag = lag
        self._band = band
        self.neutral_length = neutral_length

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

    def generate_entry_signal(self, candle: CandleLike) -> EntrySignal:
        # If lag = 0 that means we need to calculate indicators with current candle
        if self._lag > 0:
            candle = self._batch[-self._lag]

        # print(self._lowest, candle.close, self._highest,)

        # Detect when price breaks level and return signal
        if self._highest + self._band[1] < candle.close:
            return EntrySignal.BUY
        elif self._lowest + self._band[0] > candle.close:
            return EntrySignal.SELL
        else:
            return EntrySignal.NEUTRAL

        
    def batch_entry_signals(self, as_prices: bool = False) -> recarray:

        # this is because MAX & MIN don't accept window = 1
        if self._window == 1:
            highs = self.train_data.high
            lows = self.train_data.low
        else:
            highs = MAX(self.train_data.high, self._window)
            lows = MIN(self.train_data.low, self._window)

        # lag=0 means on the current candle we will generate an entry signal.
        # First check if the current high/low breaks previous high/low + tolerance 
        if self._lag == 0:
            buy_entry_signals = shift(highs) + self._band[1] < highs #shift because we take the high/low of the previous candle as reference
            sell_entry_signals = shift(lows) + self._band[0] > lows

        # lag>0 means the signal triggers at the close of the candle of lag times ago. 
        else:
            closes = self.train_data.close
            buy_entry_signals = shift(shift(highs) + self._band[1] < closes, self._lag, False)
            sell_entry_signals = shift(shift(lows) + self._band[0] > closes, self._lag, False)

        #return boolean recarray of the buy and sell signals if as_prices=False
        if not as_prices:
            return get_recarray([buy_entry_signals, sell_entry_signals], names=["buy", "sell"])

        # Calculate an approximation of the entry price at the candle where the signal is activated
        if self._lag == 0:
            buy_prices = where(buy_entry_signals, shift(highs) + self._band[1], NaN)
            sell_prices = where(sell_entry_signals, shift(lows) + self._band[0], NaN)
        else:
            buy_prices = where(buy_entry_signals, self.train_data.open, NaN)
            sell_prices = where(sell_entry_signals, self.train_data.open, NaN)

        return get_recarray([buy_prices, sell_prices], names=["buy", "sell"])
        