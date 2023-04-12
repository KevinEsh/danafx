import numpy as np
from collections import namedtuple
from inspect import signature
from typing import Union

from trade.metadata import EntrySignal, ExitSignal


class Hyperparameter(
    namedtuple(
        "Hyperparameter", ("name", "value_type", "bounds", "fixed")
    )
):
    """A strategy hyperparameter's specification in form of a namedtuple.

    Args:
        name (str): The name of the hyperparameter. Note that a strategy using a hyperparameter with name "x" must have the @property x and @x.setter
        value_type (str): The type of the hyperparameter. Could be "numeric", "categoric" or "boolean".
        bounds (Union[list, tuple]): If value_type="numeric" this should be the lower and upper bound on the parameter. If value_type="categoric" this list represent all allowed options on the parameter.
        fixed (bool): If True the string is passed, the hyperparameter's value
        cannot be changed. Default False
    """

    # A raw namedtuple is very memory efficient as it packs the attributes
    # in a struct to get rid of the __dict__ of attributes in particular it
    # does not copy the string for the keys on each instance.
    # By deriving a namedtuple class just to introduce the __init__ method we
    # would also reintroduce the __dict__ on the instance. By telling the
    # Python interpreter that this subclass uses static __slots__ instead of
    # dynamic attributes. Furthermore we don't need any additional slot in the
    # subclass so we set __slots__ to the empty tuple.
    __slots__ = ()

    def __new__(cls, name, value_type, bounds=None, fixed=False):
        _allowed_types = ["numeric", "categoric", "boolean"]
        if value_type not in _allowed_types:
            raise ValueError(f"Value type should be one of {_allowed_types}")

        if bounds is not None or value_type != "boolean":
            if not isinstance(bounds, (list, tuple)):
                raise ValueError(f"Bounds should be list or tuple. Given {type(bounds).__name__}")
            elif value_type == "numeric" and len(bounds) != 2:
                raise ValueError(f"Bounds should have 2 dimensions. Given {len(bounds)}")
            elif value_type == "categoric" and len(bounds) == 0:
                raise ValueError("Bounds should have at least 1 category. Given 0")
        else:
            bounds = [True, False]

        return super(Hyperparameter, cls).__new__(cls, name, value_type, bounds, fixed)

    def _check_bounds(self, value: Union[int, float, str, bool]):
        if self.fixed:
            raise ValueError(f"Hyperparameter {self.name} is fixed. Unable to change")

        # No bounds and is not fixed, we're allowed to change hyperparameter
        if self.bounds is None:
            return

        # Numeric type should be betwen range
        if self.value_type == "numeric" and not (self.bounds[0] <= value <= self.bounds[1]):
            raise ValueError(f"Hyperparameter {self.name} should be between {self.bounds}. Given {value}")
        # Boolean or categoric types should be in allowed values
        elif self.value_type in ["categoric", "boolean"] and value not in self.bounds:
            raise ValueError(f"Hyperparameter {self.name} should be between {self.bounds}. Given {value}")


class TradingStrategy:
    def __init__(self):
        self.last_entry_signals = [None]  # TODO: jugar con la cantidad de signals
        self.last_exit_signals = [None]  # TODO: jugar con la cantidad de signals
        self.position = None
        self.data = None

    def update_data(self, new_data: np.ndarray):
        # Define how the data should be updated. This new_data is only to update prediction
        ...

    def generate_entry_signal(self, datum: np.ndarray):
        # Define your entry signal generation logic on this method
        ...

    def validate_entry_signal(self, entry_signal: int) -> bool:
        # Define your entry signal validation logic on this method
        if entry_signal in [1, 0, -1]:  # EntrySignal._value2member_map_:
            return True
        return False

    def get_entry_signal(self, datum: np.ndarray):
        # Generate new signal and append it to the last signals queue.
        entry_signal = self.generate_entry_signal(datum)

        # If last signals in queue are all the same, return equivalent trade signal. If not, return neutral signal
        if self.validate_entry_signal(entry_signal):
            self.last_entry_signals.append(entry_signal)
            self.last_entry_signals.pop(0)

            if all(signal == 1 for signal in self.last_entry_signals):
                return EntrySignal.BUY
            elif all(signal == -1 for signal in self.last_entry_signals):
                return EntrySignal.SELL
        return EntrySignal.NEUTRAL

    def generate_exit_signal(self, datum: np.ndarray):
        # Define your entry signal generation logic on this method
        ...

    def validate_exit_signal(self, exit_signal: int) -> bool:
        # Define your exit signal validation logic on this method
        if exit_signal in [1, 0]:  # ExitSignal._value2member_map_:
            return True
        return False

    def get_exit_signal(self, datum: np.ndarray):
        # Generate new signal and append it to the last signals queue.
        exit_signal = self.generate_exit_signal(datum)

        # If last signals in queue are all the same, return equivalent trade signal. If not, return neutral signal
        if self.validate_exit_signal(exit_signal):
            self.last_exit_signals.append(exit_signal)
            self.last_exit_signals.pop(0)

            if all(signal == 1 for signal in self.last_exit_signals):
                return ExitSignal.EXIT
        return ExitSignal.HOLD

    def get_params(self):
        init_params = signature(self.__init__).parameters
        params = {}
        for name in init_params.keys():
            if name == "self":
                continue
            params[name] = getattr(self, name)
        return params

    def __repr__(self):
        params = self.get_params()
        str_params = ", ".join(f"{name}={value:.3g}" for name, value in params.items())
        return f"{self.__class__.__name__}({str_params})"


class CompoundTradingStrategy(TradingStrategy):
    def __init__(self, strategies):
        self.strategies = strategies

    def get_entry_signal(self):
        entry_signals = [stg.get_entry_signal() for stg in self.strategies]

        # Signals should be either all BUY or all SELL in a compound strategy
        if all(signal == EntrySignal.BUY for signal in entry_signals):
            return EntrySignal.BUY
        elif all(signal == EntrySignal.SELL for signal in entry_signals):
            return EntrySignal.SELL
        else:
            return EntrySignal.NEUTRAL


class MovingAverageStrategy(TradingStrategy):
    config_short_window = Hyperparameter("short_window", "numeric", (1, 200))
    config_long_window = Hyperparameter("long_window", "numeric", (1, 200))

    def __init__(self, short_window: int, long_window: int):
        super().__init__()
        self._short_window = short_window
        self._long_window = long_window

    def generate_entry_signal(self, datum: np.ndarray) -> int:
        # Calculate short and long moving averages
        mav_short = (self.data.close[(1 - self.short_window):].sum() + datum.close) / self.short_window
        mav_long = (self.data.close[(1 - self.long_window):].sum() + datum.close) / self.long_window

        print(f"{mav_short=:.5f} {mav_long=:.5f}")

        # Detect crossover
        if mav_short > mav_long:
            return 1  # buy
        elif mav_short < mav_long:
            return -1  # sell
        else:
            return 0  # neutral

    def generate_exit_signal(self, candle: np.ndarray) -> int:
        order_type = self.position.type
        open_price = self.position.price_open
        p = 1

        print(f"{open_price=} {candle.close=}")

        if order_type == 0 and (open_price + 0.0001 * p <= candle.close):
            return 1
        elif order_type == 1 and (open_price - 0.0001 * p >= candle.close):
            return 1

        return 0

    @property
    def short_window(self):
        return self._short_window

    @short_window.setter
    def short_window(self, short_window):
        self.config_short_window._check_bounds(short_window)
        self._short_window = short_window
        return

    @property
    def long_window(self):
        return self._long_window

    @long_window.setter
    def long_window(self, long_window):
        self.config_long_window._check_bounds(long_window)
        self._long_window = long_window
        return
        # Calculate short and long moving averages
        # mav_short = (self.data.close[(1 - self.short_window):].sum() + datum.close) / self.short_window
        # mav_long = (self.data.close[(1 - self.long_window):].sum() + datum.close) / self.long_window

        # Detect crossover
        # if mav_short > mav_long:
        #     return 1  # buy
        # elif mav_short < mav_long:
        #     return -1  # sell
        # else:
        #     return 0  # neutral

        # # Function to update trailing stop if needed
        # def update_trailing_stop(order, trailing_stop_pips, pip_size):
        #     # Convert trailing_stop_pips into pips
        #     trailing_stop_pips = trailing_stop_pips * pip_size
        #     # Determine if Red or Green
        #     # A Green Position will have a take_profit > stop_loss
        #     if order[12] > order[11]:
        #         # If Green, new_stop_loss = current_price - trailing_stop_pips
        #         new_stop_loss = order[13] - trailing_stop_pips
        #         # Test to see if new_stop_loss > current_stop_loss
        #         if new_stop_loss > order[11]:
        #             print("Update Stop Loss")
        #             # Create updated values for order
        #             order_number = order[0]
        #             symbol = order[16]
        #             # New take_profit will be the difference between new_stop_loss and old_stop_loss added to take profit
        #             new_take_profit = order[12] + new_stop_loss - order[11]
        #             print(new_take_profit)
        #             # Send order to modify_position
        #             broker.modify_position(order_number=order_number, symbol=symbol, new_stop_loss=new_stop_loss,
        #                                    new_take_profit=new_take_profit)
        #     elif order[12] < order[11]:
        #         # If Red, new_stop_loss = current_price + trailing_stop_pips
        #         new_stop_loss = order[13] + trailing_stop_pips
        #         # Test to see if new_stop_loss < current_stop_loss
        #         if new_stop_loss < order[11]:
        #             print("Update Stop Loss")
        #             # Create updated values for order
        #             order_number = order[0]
        #             symbol = order[16]
        #             # New take_profit will be the difference between new_stop_loss and old_stop_loss subtracted from old take_profit
        #             new_take_profit = order[12] - new_stop_loss + order[11]
        #             print(new_take_profit)
        #             # Send order to modify_position
        #             broker.modify_position(order_number=order_number, symbol=symbol, new_stop_loss=new_stop_loss,
        #                                    new_take_profit=new_take_profit)
