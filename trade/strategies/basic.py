from trade.strategies.abstract import Hyperparameter, TradingStrategy
from numpy import recarray


class BandPriceStrategy(TradingStrategy):
    config_buy_band = Hyperparameter("buy_band", "interval", (0, 1000))
    config_sell_band = Hyperparameter("sell_band", "interval", (0, 1000))

    def __init__(self, buy_band: tuple[float], sell_band: tuple[float]):
        super().__init__()
        # Check if hyperparameters met the criteria
        self.config_buy_band._check_bounds(buy_band, init=True)
        self.config_sell_band._check_bounds(sell_band, init=True)

        self._buy_band = buy_band
        self._sell_band = sell_band

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

    def generate_entry_signal(self, datum: recarray):
        if self._buy_band[0] <= datum.close <= self._buy_band[1]:
            return 0  # buy
        elif self._sell_band[0] <= datum.close <= self._sell_band[1]:
            return 1  # sell
        else:
            return -1  # neutral
