from typing import Union
from inspect import signature
from collections import namedtuple
from numpy import recarray, append, delete, s_

from trade.metadata import EntrySignal, ExitSignal

OHLCbounds = ("open", "high", "low", "close")


class Hyperparameter(
    namedtuple(
        "Hyperparameter", ("name", "value_type", "bounds", "fixed")
    )
):
    """A strategy hyperparameter's specification in form of a namedtuple.

    Args:
        name (str): The name of the hyperparameter. Note that a strategy using a
            hyperparameter with name "x" must have the @property x and @x.setter
        value_type (str): The type of the hyperparameter. Could be "numeric",
            "categoric" or "boolean".
        bounds (Union[list, tuple]): If value_type="numeric" this should be the
            lower and upper bound on the parameter. If value_type="categoric"
            this list represent all allowed options on the parameter.
        fixed (bool): If True the string is passed, the hyperparameter's value
            cannot be changed. Default False

    Notes:
        A raw namedtuple is very memory efficient as it packs the attributes
        in a struct to get rid of the __dict__ of attributes in particular it
        does not copy the string for the keys on each instance.
        By deriving a namedtuple class just to introduce the __init__ method we
        would also reintroduce the __dict__ on the instance. By telling the
        Python interpreter that this subclass uses static __slots__ instead of
        dynamic attributes. Furthermore we don't need any additional slot in the
        subclass so we set __slots__ to the empty tuple.
    """
    __slots__ = ()

    def __new__(cls, name, value_type, bounds=None, fixed=False):
        _allowed_types = ["numeric", "categoric", "boolean", "interval"]
        if value_type not in _allowed_types:
            raise ValueError(f"Value type should be one of {_allowed_types}")

        if bounds is not None or value_type != "boolean":
            if not isinstance(bounds, (list, tuple)):
                raise ValueError(
                    f"Bounds should be list or tuple. Given {type(bounds).__name__}")
            elif value_type in ["numeric", "interval"] and len(bounds) != 2:
                raise ValueError(
                    f"Bounds should have 2 dimensions. Given {len(bounds)}")
            elif value_type == "categoric" and len(bounds) == 0:
                raise ValueError(
                    "Bounds should have at least 1 category. Given 0")
        else:
            bounds = [True, False]

        return super(Hyperparameter, cls).__new__(cls, name, value_type, bounds, fixed)

    def _check_bounds(
        self,
        value: Union[int, float, str, bool, list, tuple],
        init: bool = False
    ):
        # Check value type
        if self.value_type == "numeric" and not isinstance(value, (int, float)):
            ValueError(
                f"Hyperparameter {self.name} needs int or float value. Given {type(value).__name__}")
        elif self.value_type == "boolean" and not isinstance(value, bool):
            ValueError(
                f"Hyperparameter {self.name} needs bool value. Given {type(value).__name__}")
        elif self.value_type == "interval" and not isinstance(value, (tuple, list)):
            ValueError(
                f"Hyperparameter {self.name} needs tuple or list value. Given {type(value).__name__}")
        # categoric value are allowed any

        if self.fixed and not init:
            raise ValueError(
                f"Hyperparameter {self.name} is fixed. Unable to change")

        # No bounds and is not fixed, we're allowed to change hyperparameter
        if self.bounds is None:
            return

        # Numeric type should be betwen range
        if self.value_type == "numeric" and not (self.bounds[0] <= value <= self.bounds[1]):
            raise ValueError(
                f"Hyperparameter {self.name} should be between {self.bounds}. Given {value}")
        # Interval type should be inside the wider interval
        if self.value_type == "interval" and (not (self.bounds[0] <= value[0]) or not (value[1] <= self.bounds[1])):
            raise ValueError(
                f"Hyperparameter {self.name} should be within {self.bounds}. Given {value}")
        # Boolean or categoric types should be in allowed values
        elif self.value_type in ["categoric", "boolean"] and value not in self.bounds:
            raise ValueError(
                f"Hyperparameter {self.name} should be between {self.bounds}. Given {value}")


class TradingStrategy:
    def __init__(self):
        self.min_bars = None
        self.position = None
        self.train_data = None
        self.train_labels = None
        self.compound_mode = False
        # TODO: jugar con la cantidad de signals
        self.last_entry_signals = [None]
        # TODO: jugar con la cantidad de signals
        self.last_exit_signals = [None]

    def fit(self, train_data: recarray, train_labels: recarray = None) -> None:
        self.train_data = train_data
        self.train_labels = train_labels

    def update_data(self, new_data: recarray) -> None:
        # Define how the data should be updated. This new_data is only to update prediction
        # Compare if latest candlestick is the same. If true, update queue.
        if not self.is_new_data(new_data):
            return
        # Append new data to the train array then delete a release memory from oldest one
        new_rows = new_data.shape[0]
        self.train_data = append(self.train_data, new_data, axis=0)
        self.train_data = delete(
            self.train_data, s_[:new_rows], axis=0).view(recarray)

    def generate_entry_signal(self, candle: recarray):
        # Define your entry signal generation logic on this method
        return EntrySignal.NEUTRAL.value  # return neutral by default

    def validate_entry_signal(self, entry_signal: int):
        # Define your entry signal validation logic on this method
        if entry_signal not in EntrySignal._value2member_map_:
            raise ValueError(f"{entry_signal=} not recognized")

    def get_entry_signal(self, candle: recarray):
        # Generate new signal and append it to the last signals queue.
        entry_signal = self.generate_entry_signal(candle)
        self.validate_entry_signal(entry_signal)

        self.last_entry_signals.append(entry_signal)
        self.last_entry_signals.pop(0)

        # If last signals in queue are all the same, return equivalent trade signal.
        # If not, return neutral signal
        if all(signal == EntrySignal.BUY.value for signal in self.last_entry_signals):
            return EntrySignal.BUY

        elif all(signal == EntrySignal.SELL.value for signal in self.last_entry_signals):
            return EntrySignal.SELL

        return EntrySignal.NEUTRAL

    def generate_exit_signal(self, candle: recarray):
        # Define your entry signal generation logic on this method
        return ExitSignal.HOLD.value  # return hold signal by default

    def validate_exit_signal(self, exit_signal: int):
        # Define your exit signal validation logic on this method
        if exit_signal not in ExitSignal._value2member_map_:
            raise ValueError(f"{exit_signal=} not recognized")

    def get_exit_signal(self, candle: recarray):
        # Generate new signal and append it to the last signals queue.
        exit_signal = self.generate_exit_signal(candle)
        self.validate_exit_signal(exit_signal)

        self.last_exit_signals.append(exit_signal)
        self.last_exit_signals.pop(0)

        # If last signals in queue are all the same, return equivalent trade signal.
        # If not, return neutral signal
        if all(signal == ExitSignal.EXIT.value for signal in self.last_exit_signals):
            return ExitSignal.EXIT
        return ExitSignal.HOLD

    def is_new_data(self, new_data: recarray) -> bool:
        # TODO: improve this method
        if new_data.time[0] > self.train_data.time[-1]:
            return True
        return False

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
        str_params = ", ".join(
            f"{name}={value:.3g}" for name, value in params.items())
        return f"{self.__class__.__name__}({str_params})"


class CompoundTradingStrategy(TradingStrategy):
    """A trading strategy that combines multiple entry strategies and optionally, exit strategies.

    Args:
        entry_strategies (list[TradingStrategy]):
            A list of TradingStrategy objects used to generate entry signals.
        exit_strategies (list[TradingStrategy], optional):
            A list of TradingStrategy objects used to generate exit signals. If not specified,
            the default exit strategy of the superclass is used.

    Methods:
        fit(train_data: recarray, train_labels: recarray = None)
            Fits each of the entry strategies on the provided training data and labels.
        get_entry_signal() -> EntrySignal
            Returns a BUY, SELL, or NEUTRAL entry signal based on the signals generated
            by the entry strategies.
        get_exit_signal() -> ExitSignal
            Returns an EXIT or NEUTRAL exit signal based on the signals generated by the
            exit strategies, or the default exit strategy of the superclass if exit_strategies
            is not specified.
    """

    def __init__(
        self,
        entry_strategies: list[TradingStrategy],
        exit_strategies: list[TradingStrategy] = None
    ):
        super().__init__()
        self.entry_strategies = entry_strategies
        self.exit_strategies = exit_strategies

        # The minimum amount of bars is the maximum of all strategies
        min_bars_entry = max(stgy.min_bars for stgy in entry_strategies)
        min_bars_exit = max(stgy.min_bars for stgy in exit_strategies) \
            if exit_strategies else 0
        self.min_bars = max(min_bars_entry, min_bars_exit)

        # Set all strategies to compound mode
        for stgy in entry_strategies:
            stgy.compound_mode = True

        if exit_strategies:
            for stgy in exit_strategies:
                stgy.compound_mode = True

    def fit(self, train_data: recarray, train_labels: recarray = None):
        """Fits each of the strategies on the provided training data and labels.

        Args:
            train_data (recarray): _description_
            train_labels (recarray, optional): _description_. Defaults to None.
        """
        for stgy in self.entry_strategies:
            stgy.fit(train_data, train_labels)

    def get_entry_signal(self):
        entry_signals = [stgy.get_entry_signal()
                         for stgy in self.entry_strategies]

        # Signals should be either all BUY or all SELL in a compound strategy
        if all(signal == EntrySignal.BUY for signal in entry_signals):
            return EntrySignal.BUY
        elif all(signal == EntrySignal.SELL for signal in entry_signals):
            return EntrySignal.SELL
        else:
            return EntrySignal.NEUTRAL

    def get_exit_signal(self):
        if not self.exit_strategies:
            return super().get_exit_signal()

        exit_signals = [stgy.get_exit_signal()
                        for stgy in self.exit_strategies]

        # Signals should be either all BUY or all SELL in a compound strategy
        if all(signal == ExitSignal.EXIT for signal in exit_signals):
            return ExitSignal.EXIT
        else:
            return ExitSignal.NEUTRAL

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
