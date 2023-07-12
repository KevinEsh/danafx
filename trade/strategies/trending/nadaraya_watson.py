import numpy as np
from datatools.custom import addpop, get_recarray, shift, find_supreme
from datatools.technical import crossingover, crossingunder, above, onband, below

from trade.metadata import CandleLike, EntrySignal
from trade.indicators import RBFK, RQK
from trade.strategies.abstract import Hyperparameter, TradingStrategy


class DualNadarayaKernelStrategy(TradingStrategy):
    config_window_rqk = Hyperparameter("window_rqk", "numeric", (1, 1000))
    config_window_rbfk = Hyperparameter("window_rbfk", "numeric", (1, 1000))
    config_alpha_rq = Hyperparameter("alpha_rq", "numeric", (0, 1e6))
    config_n_bars = Hyperparameter("n_bars", "numeric", (2, 5000))
    config_lag = Hyperparameter("lag", "numeric", (0, 1))
    config_band = Hyperparameter("band", "interval", (-1000, 1000))
    config_mode = Hyperparameter("mode", "categoric", ("oncross", "holded"))

    def __init__(
        self,
        window_rqk: int = 8,
        window_rbfk: int = 8,
        alpha_rq: float = 1,
        n_bars: int = 25,
        lag: int = 0,
        band: tuple = (0, 0),
        mode: str = "oncross",
    ):
        super().__init__()
        # Check if hyperparameters met the criteria
        # self.config_window_rqk._check_bounds(window_rqk, init=True)
        # self.config_window_rbfk._check_bounds(window_rbfk, init=True)
        # self.config_alpha_rq._check_bounds(alpha_rq, init=True)
        # self.config_n_bars._check_bounds(n_bars, init=True)
        # self.config_lag._check_bounds(lag, init=True)
        # self.config_band._check_bounds(band, init=True)
        # self.config_mode._check_bounds(mode, init=True)

        self.window_rqk = window_rqk
        self.window_rbfk = window_rbfk
        self.alpha_rq = alpha_rq
        self.n_bars = n_bars
        self.lag = lag
        self.band = band
        self.mode = mode

        # self._rqk_bars = get_stable_min_bars("RQK")
        # self._rbfk_bars = get_stable_min_bars("RBFK")
        # self.min_bars = max(self._rqk_bars, self._rbfk_bars) + lag

        self._rqk_bars = n_bars
        self._rbfk_bars = n_bars
        self.min_bars = n_bars + lag

    @property
    def window_rqk(self):
        return self._window_rqk

    @window_rqk.setter
    def window_rqk(self, window_rqk):
        self.config_window_rqk._check_bounds(window_rqk)
        self._window_rqk = window_rqk

    @property
    def window_rbfk(self):
        return self._window_rbfk

    @window_rbfk.setter
    def window_rbfk(self, window_rbfk):
        self.config_window_rbfk._check_bounds(window_rbfk)
        self._window_rbfk = window_rbfk

    @property
    def alpha_rq(self):
        return self._alpha_rq

    @alpha_rq.setter
    def alpha_rq(self, alpha_rq):
        self.config_alpha_rq._check_bounds(alpha_rq)
        self._alpha_rq = alpha_rq

    @property
    def n_bars(self):
        return self._n_bars

    @n_bars.setter
    def n_bars(self, n_bars):
        self.config_n_bars._check_bounds(n_bars)
        self._n_bars = n_bars

    @property
    def lag(self):
        return self._lag

    @lag.setter
    def lag(self, lag):
        self.config_lag._check_bounds(lag)
        self._lag = lag

    @property
    def band(self):
        return self._band

    @band.setter
    def band(self, band):
        self.config_band._check_bounds(band)
        self._band = band

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self.config_mode._check_bounds(mode)
        self._mode = mode

    def fit(
        self,
        train_data: CandleLike,
        train_labels: np.ndarray = None
    ) -> None:
        if not self.compound_mode:
            super().fit(train_data, train_labels)

        # Precalculate RQK & RBFK. This will save computational time
        self._rqk_queue = RQK(train_data.close, self._window_rqk, self._alpha_rq,
                              self._rqk_bars, dropna=True)
        self._rbfk_queue = RBFK(train_data.close, self._window_rbfk, self._rbfk_bars, dropna=True)

        # print(self._rqk_queue)
        # print(self._rbfk_queue)

        # Save minimal batch to compute indicator with current candle
        self._batch_rqk = self.train_data[-self._rqk_bars:]
        self._batch_rbfk = self.train_data[-self._rbfk_bars:]

        # signals = self.batch_signals()
        # print(signals)

    def update_data(self, new_candles: CandleLike) -> None:
        if not self.is_new_data(new_candles):
            return

        if not self.compound_mode:
            super().update_data(new_candles)

        # Update minimal batch
        self._batch_rqk = self.train_data[-self._rqk_bars:]
        self._batch_rbfk = self.train_data[-self._rbfk_bars:]

        # Then calculate new indicator values
        new_rqk = RQK(self._batch_rqk.close, self._window_rqk, self._alpha_rq,
                      self._rqk_bars, dropna=True)
        new_rbfk = RBFK(self._batch_rbfk.close, (self._window_rbfk - self._lag),
                        self._rbfk_bars, dropna=True)

        # Finally add them to the queue
        self._rqk_queue = addpop(self._rqk_queue, new_rqk)
        self._rbfk_queue = addpop(self._rbfk_queue, new_rbfk)
        # print(self._rqk_queue)
        # print(self._rbfk_queue)

    def generate_entry_signal(self, candle: CandleLike) -> int:
        # If lag = 0 that means we need to calculate indicators with current candle
        if self._lag == 0:
            batch_rqk = addpop(self._batch_rqk.close, candle.close)  # TODO: achis? esto borra datos del batch?
            batch_rbfk = addpop(self._batch_rbfk.close, candle.close)

            # Calculate indicator for current candle
            rqk = RQK(batch_rqk, self._window_rqk, self._alpha_rq,
                      self._rqk_bars)[-1]
            rbfk = RBFK(batch_rbfk, (self._window_rbfk - self._lag),
                        self._rqk_bars)[-1]

            line_rqk = [self._rqk_queue[-1], rqk]
            line_rbfk = [self._rbfk_queue[-1], rbfk]
        # else use cache stored values to make signal
        else:
            line_rqk = self._rqk_queue[-2-self._lag:]
            line_rbfk = self._rbfk_queue[-2-self._lag:]

        # print(
        #     f"[{line_rqk[0]=:.5f}, {line_rqk[1]=:.5f}][{line_rbfk[0]=:.5f}, {line_rbfk[1]=:.5f}]")

        # Detect tendency and return signal
        if self._mode == 'holded':
            if above(line_rbfk, line_rqk, self._band[1])[-1]:
                return EntrySignal.BUY
            elif below(line_rbfk, line_rqk, self._band[0])[-1]:
                return EntrySignal.SELL
        elif self._mode == 'oncross':
            if crossingover(line_rbfk, line_rqk, self._band[1])[-1]:
                return EntrySignal.BUY
            elif crossingunder(line_rbfk, line_rqk, self._band[0])[-1]:
                return EntrySignal.SELL 
        return EntrySignal.NEUTRAL

    def batch_entry_signals(self) -> np.recarray:
        # Precalculate RQK & RBFK. This will save computational time
        if self._lag == 0:
            raise NotImplementedError()

        kernels = self.get_kernels()
            
        if self._mode == 'oncross':
            buy_entry_indexes = shift(crossingover(kernels.rbf, kernels.rq, self.band[1]), self._lag, False)
            sell_entry_indexes = shift(crossingunder(kernels.rbf, kernels.rq, self.band[0]), self._lag, False)
        elif self._mode == 'holded':
            buy_entry_indexes = shift(above(kernels.rbf, kernels.rq, self.band[1]), self._lag, False)
            sell_entry_indexes = shift(below(kernels.rbf, kernels.rq, self.band[0]), self._lag, False)

        # Calculate an approximation of the entry price at the candle where the signal is activated
        if self._lag == 0:
            highs = self.train_data.high
            lows = self.train_data.low
            buy_entry_prices = np.where(buy_entry_indexes, highs, np.NaN)
            sell_entry_prices = np.where(sell_entry_indexes, lows, np.NaN)
        else:
            opens = self.train_data.open
            buy_entry_prices = np.where(buy_entry_indexes, opens, np.NaN)
            sell_entry_prices = np.where(sell_entry_indexes, opens, np.NaN)        
        
        return get_recarray([
            buy_entry_indexes, buy_entry_prices,
            sell_entry_indexes, sell_entry_prices], 
            names=['buy_index', 'buy_price', 'sell_index', 'sell_price'])

    def batch_exit_signals(self, entry_signals: np.recarray) -> np.recarray:
        if self._lag == 0:
            raise NotImplementedError()

        kernels = self.get_kernels()
        opens = self.train_data.open

        if self._mode == 'oncross':
            buy_exit_indexes = shift(crossingunder(kernels.rbf, kernels.rq, self.band[0]), self._lag, False)
            sell_exit_indexes = shift(crossingover(kernels.rbf, kernels.rq, self.band[1]), self._lag, False)
        elif self._mode == 'holded':
            buy_entry_indexes = shift(below(kernels.rbf, kernels.rq, self.band[0]), self._lag, False)
            sell_entry_indexes = shift(above(kernels.rbf, kernels.rq, self.band[1]), self._lag, False)
 
        buy_exit_indexes = np.full_like(entry_signals, np.NaN)
        buy_exit_prices = np.full_like(entry_signals, np.NaN)

        for entry_i in np.where(entry_signals.buy_index)[0]:
            # entry_price = entry_signals.buy_price[entry_i]
            # stop_level = entry_price - adj_stop
            # take_level = entry_price + adj_take

            valid_exits = buy_exit_indexes[entry_i:]
            exit_i = np.argmax(valid_exits) + entry_i if np.any(valid_exits) else None
        
            if exit_i is None:
                continue

            buy_exit_indexes[entry_i] = exit_i
            buy_exit_prices[entry_i] = opens[exit_i]


        
    def get_kernels(self) -> np.recarray:
        closes = self.train_data.close
        rq = RQK(closes, self._window_rqk, self._alpha_rq, self._rqk_bars)
        rbf = RBFK(closes, self._window_rbfk, self._rbfk_bars)
        return get_recarray([rq, rbf], names=["rq", "rbf"])
    
    def get_trendline(self):
        kernels = self.get_kernels()
        bullish = np.where(above(kernels.rbf, kernels.rq, self._band[1]), kernels.rq, np.NaN)
        neutral = np.where(onband(kernels.rbf, kernels.rq, self._band), kernels.rq, np.NaN)
        bearish = np.where(below(kernels.rbf, kernels.rq, self._band[0]), kernels.rq, np.NaN)
        return get_recarray([bullish, neutral, bearish], names=['bullish', 'neutral', 'bearish'])

        