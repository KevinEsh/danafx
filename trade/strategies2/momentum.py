from trade.strategies import Hyperparameter, TradingStrategy, OHLCbounds
from numpy import recarray, append

from talib import RSI
from talib.stream import RSI as _RSI


class RsiStrategy(TradingStrategy):
    config_window = Hyperparameter("window", "numeric", (2, 1000))
    config_buy_band = Hyperparameter("buy_band", "interval", (0, 100))
    config_sell_band = Hyperparameter("sell_band", "interval", (0, 100))
    config_source = Hyperparameter("source", "categoric", OHLCbounds)

    def __init__(
        self,
        window: int,
        buy_band: tuple[float],
        sell_band: tuple[float],
        source: str = "close"
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_window._check_bounds(window, init=True)
        self.config_buy_band._check_bounds(buy_band, init=True)
        self.config_sell_band._check_bounds(sell_band, init=True)
        self.config_source._check_bounds(source, init=True)

        self._window = window
        self._buy_band = buy_band
        self._sell_band = sell_band
        self._source = source
        self._min_candles = window + 80

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, window):
        self.config_window._check_bounds(window)
        self._window = window

    @property
    def buy_band(self):
        return self._buy_band

    @buy_band.setter
    def buy_band(self, buy_band):
        self.config_buy_band._check_bounds(buy_band)
        self._buy_band = buy_band

    @property
    def sell_band(self):
        return self._sell_band

    @sell_band.setter
    def sell_band(self, sell_band):
        self.config_sell_band._check_bounds(sell_band)
        self._sell_band = sell_band

    def fit(self, train_data: recarray):
        super().fit(train_data)
        self._last_candles = self.train_data.close[-self._min_candles:]
        self._prev_rsi = RSI(self._last_candles)[-1]

    def update_data(self, new_data: recarray) -> None:
        super().update_data(new_data)
        self._last_candles = self.train_data.close[-self._min_candles:]

    def generate_entry_signal(self, datum: recarray) -> int:
        # Calculate RSI for current candle
        # batch = np.append(self.train_data.close, datum.close)
        # rsi = RSI(batch, self._window)[-1]
        # print(f"{rsi=:.2f}")

        batch = append(self._last_candles, datum.close)
        rsi = _RSI(batch, self._window)
        print(f"{rsi=:.2f}")

        # Return signal based on sell/buy bands
        if self._buy_band[0] <= rsi <= self._buy_band[1]:
            return 0  # buy
        elif self._sell_band[0] <= rsi <= self._sell_band[1]:
            return 1  # sell
        else:
            return -1  # neutral
