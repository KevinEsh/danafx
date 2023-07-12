from abc import ABC, abstractmethod
import numpy as np  # np.recarray, append, delete, s_
from typing import Union
from inspect import signature
from collections import namedtuple

from trade.metadata import EntrySignal, ExitSignal, TradePosition, CandleLike
from datatools.custom import addpop_recarrays

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


class AbstractStrategy(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.min_bars = None
        # self.position = None
        self.train_data = None
        self.train_labels = None
        self.compound_mode = False

    def fit(self, train_data: np.recarray, train_labels: np.recarray = None) -> None:
        self.train_data = train_data
        self.train_labels = train_labels

    def is_new_data(self, new_data: np.recarray) -> bool:
        # TODO: improve this method
        if new_data.time[0] > self.train_data.time[-1]:
            return True
        return False

    def update_data(self, new_data: np.recarray) -> None:
        # Append new data to the train array then delete a release memory from oldest one
        self.train_data = addpop_recarrays(self.train_data, new_data)
        #TODO: self.train_labels = addpop(self.train_labels, new_labels)

    def get_params(self):
        init_params = signature(self.__init__).parameters
        params = {}
        for name in init_params.keys():
            if name == "self":
                continue
            params[name] = getattr(self, name)
        return params

    def __str__(self):
        params = self.get_params()
        str_params = ", ".join(
            f"{name}={value}" for name, value in params.items())
        return f"{self.__class__.__name__}({str_params})"

    def __repr__(self) -> str:
        return self.__str__()

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

    def fit(self, train_data: np.recarray, train_labels: np.recarray = None) -> None:
        self.train_data = train_data
        self.train_labels = train_labels

    def update_data(self, new_data: np.recarray) -> None:
        # Define how the data should be updated. This new_data is only to update prediction
        # Compare if latest candlestick is the same. If true, update queue.
        if not self.is_new_data(new_data):
            return
        # Append new data to the train array then delete a release memory from oldest one
        new_rows = new_data.shape[0]
        self.train_data = np.append(self.train_data, new_data, axis=0)
        self.train_data = np.delete(
            self.train_data, np.s_[:new_rows], axis=0).view(np.recarray)

    def generate_entry_signal(self, candle: np.recarray):
        # Define your entry signal generation logic on this method
        return EntrySignal.NEUTRAL  # return neutral by default

    def validate_entry_signal(self, entry_signal: int):
        # Define your entry signal validation logic on this method
        if entry_signal not in EntrySignal:
            raise ValueError(f"{entry_signal=} not recognized")

    def get_entry_signal(self, candle: np.recarray):
        # Generate new signal and append it to the last signals queue.
        entry_signal = self.generate_entry_signal(candle)
        self.validate_entry_signal(entry_signal)

        self.last_entry_signals.append(entry_signal)
        self.last_entry_signals.pop(0)

        # If last signals in queue are all the same, return equivalent trade signal.
        if all(signal == EntrySignal.BUY for signal in self.last_entry_signals):
            return EntrySignal.BUY

        elif all(signal == EntrySignal.SELL for signal in self.last_entry_signals):
            return EntrySignal.SELL

        return EntrySignal.NEUTRAL

    def generate_exit_signal(self, candle: np.recarray):
        # Define your entry signal generation logic on this method
        return ExitSignal.HOLD  # return hold signal by default

    def validate_exit_signal(self, exit_signal: int):
        # Define your exit signal validation logic on this method
        if exit_signal not in ExitSignal:
            raise ValueError(f"{exit_signal=} not recognized")

    def get_exit_signal(self, candle: np.recarray, position: TradePosition) -> ExitSignal:
        # Generate new signal and append it to the last signals queue.
        exit_signal = self.generate_exit_signal(candle, position)
        self.validate_exit_signal(exit_signal)

        self.last_exit_signals.append(exit_signal)
        self.last_exit_signals.pop(0)

        # If last signals in queue are all the same, return equivalent trade signal.
        # If not, return neutral signal
        if all(signal == ExitSignal.EXIT for signal in self.last_exit_signals):
            return ExitSignal.EXIT
        return ExitSignal.HOLD

    def is_new_data(self, new_data: np.recarray) -> bool:
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

    def __str__(self):
        params = self.get_params()
        str_params = ", ".join(
            f"{name}={value}" for name, value in params.items())
        return f"{self.__class__.__name__}({str_params})"


class EntryTradingStrategy(AbstractStrategy):
    def __init__(self):
        super().__init__()
        # TODO: jugar con la cantidad de signals
        self.last_entry_signals = [None]

    def generate_entry_signal(self, candle: np.recarray):
        # Define your entry signal generation logic on this method
        return EntrySignal.NEUTRAL  # return neutral by default

    def validate_entry_signal(self, entry_signal: int):
        # Define your entry signal validation logic on this method
        if entry_signal not in EntrySignal:
            raise ValueError(f"{entry_signal=} not recognized")

    def get_entry_signal(self, candle: np.recarray):
        # Generate new signal and append it to the last signals queue.
        entry_signal = self.generate_entry_signal(candle)
        self.validate_entry_signal(entry_signal)

        self.last_entry_signals.append(entry_signal)
        self.last_entry_signals.pop(0)

        # If last signals in queue are all the same, return equivalent trade signal.
        if all(signal == EntrySignal.BUY for signal in self.last_entry_signals):
            return EntrySignal.BUY

        elif all(signal == EntrySignal.SELL for signal in self.last_entry_signals):
            return EntrySignal.SELL

        return EntrySignal.NEUTRAL


class ExitTradingStrategy(AbstractStrategy):
    def __init__(self):
        super().__init__()
        self.last_exit_signals = [None]

    @abstractmethod
    def generate_exit_signal(self, candle: np.recarray, position: TradePosition):
        # Define your entry signal generation logic on this method
        return ExitSignal.HOLD  # return hold signal by default

    def validate_exit_signal(self, exit_signal: int):
        # Define your exit signal validation logic on this method
        if exit_signal not in ExitSignal:
            raise ValueError(f"{exit_signal=} not recognized")

    def get_exit_signal(self, candle: np.recarray, position: TradePosition):
        # Generate new signal and append it to the last signals queue.
        exit_signal = self.generate_exit_signal(candle, position)
        self.validate_exit_signal(exit_signal)

        self.last_exit_signals.append(exit_signal)
        self.last_exit_signals.pop(0)

        # If last signals in queue are all the same, return equivalent trade signal.
        # If not, return neutral signal
        if all(signal == ExitSignal.EXIT for signal in self.last_exit_signals):
            return ExitSignal.EXIT
        return ExitSignal.HOLD


class CompoundTradingStrategy(TradingStrategy):
    """A trading strategy that combines multiple entry strategies and optionally, exit strategies.

    Args:
        entry_strategy (list[TradingStrategy]):
            A list of TradingStrategy objects used to generate entry signals.
        exit_strategies (list[TradingStrategy], optional):
            A list of TradingStrategy objects used to generate exit signals. If not specified,
            the default exit strategy of the superclass is used.

    Methods:
        fit(train_data: np.recarray, train_labels: np.recarray = None)
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
        entry_strategy: TradingStrategy = None,
        exit_strategy: TradingStrategy = None
    ):
        super().__init__()
        self.entry_strategy = entry_strategy
        self.exit_strategy = exit_strategy

        # The minimum amount of bars is the maximum of all strategies
        min_bars_entry = recursive_min_bars(entry_strategy)
        min_bars_exit = recursive_min_bars(exit_strategy)
        self.min_bars = max(min_bars_entry, min_bars_exit)


    def fit(self, train_data: np.recarray, train_labels: np.recarray = None):
        """Fits each of the strategies on the provided training data and labels.

        Args:
            train_data (np.recarray): _description_
            train_labels (np.recarray, optional): _description_. Defaults to None.
        """
        # Set all strategies to compound mode
        super().fit(train_data, train_labels)
        recursive_set_compound_mode(self.entry_strategy)
        recursive_set_compound_mode(self.exit_strategy)
        # recursive_fit(self.entry_strategy, train_data, train_labels)
        # recursive_fit(self.exit_strategy, train_data, train_labels)

    def get_entry_signal(self):
        if self.exit_strategy is None:
            raise ValueError("No EntryStrategy was set")
        return recursive_get_entry_signal(self.entry_strategy)

    def get_exit_signal(self):
        if self.exit_strategy is None:
            raise ValueError("No ExitStrategy was set")
            # return ExitSignal.HOLD
        return recursive_get_exit_signal(self.exit_strategy)
    
    def __str__(self):
        entry_strategy = str(self.entry_strategy)
        exit_strategy = str(self.exit_strategy)
        return f"{self.__class__.__name__}({entry_strategy=}, {exit_strategy=})"

def Priority(*args):
    return ('priority', list(args))


def And(*args):
    return ('and', list(args))


def Or(*args):
    return ('or', list(args))


def recursive_set_compound_mode(tree):
    if isinstance(tree, (TradingStrategy, ExitTradingStrategy, EntryTradingStrategy)):  # the node is a strategy
        tree.compound_mode = True
        return

    for stgy in tree[1]:
        recursive_set_compound_mode(stgy)


def recursive_min_bars(tree):
    if isinstance(tree, (TradingStrategy, ExitTradingStrategy, EntryTradingStrategy)):  # the node is a strategy
        return tree.min_bars
    # Return the maximum of all min_bars downstream
    return max(recursive_min_bars(stgy) for stgy in tree[1])


def recursive_fit(tree, train_data, train_labels = None):
    if isinstance(tree, (TradingStrategy, ExitTradingStrategy, EntryTradingStrategy)):  # the node is a strategy
        tree.fit(train_data, train_labels)
        return
    
    for stgy in tree[1]:
        # print(train_data)
        # print(stgy, train_data, train_labels)
        recursive_fit(stgy, train_data, train_labels)


def recursive_get_entry_signal(tree):
    if isinstance(tree, (TradingStrategy, ExitTradingStrategy, EntryTradingStrategy)):  # the node is a strategy
        return tree.get_entry_signal()

    operator, strategies = tree

    # The first strategy to get a entry signal
    if operator == 'priority':
        for stgy in strategies:
            signal = recursive_get_entry_signal(stgy)
            if signal != EntrySignal.NEUTRAL:
                return signal
        return EntrySignal.NEUTRAL

    signals = [recursive_get_entry_signal(stgy) for stgy in strategies]

    # Any of the signals could be BUY or SELL.
    if operator == 'or':
        if all(signal in (EntrySignal.BUY, EntrySignal.NEUTRAL) for signal in signals):
            return EntrySignal.BUY
        elif all(signal in (EntrySignal.SELL, EntrySignal.NEUTRAL) for signal in signals):
            return EntrySignal.SELL
        else:
            return EntrySignal.NEUTRAL

    # Signals should be either all BUY or all SELL
    elif operator == 'and':
        if all(signal == EntrySignal.BUY for signal in signals):
            return EntrySignal.BUY
        elif all(signal == EntrySignal.SELL for signal in signals):
            return EntrySignal.SELL
        else:
            return EntrySignal.NEUTRAL


def recursive_get_exit_signal(tree):
    if isinstance(tree, (TradingStrategy, ExitTradingStrategy, EntryTradingStrategy)):  # the node is a strategy
        return tree.get_exit_signal()

    operator, strategies = tree

    # The first strategy to get a entry signal
    if operator == 'priority':
        for stgy in strategies:
            signal = recursive_get_exit_signal(stgy)
            if signal != ExitSignal.HOLD:
                return signal
        return ExitSignal.HOLD

    signals = [recursive_get_exit_signal(stgy) for stgy in strategies]

    # Any of the signals could be BUY or SELL.
    if operator == 'or':
        if any(signal == ExitSignal.EXIT for signal in signals):
            return ExitSignal.EXIT
        else:
            return ExitSignal.HOLD

    # Signals should be either all BUY or all SELL
    elif operator == 'and':
        if all(signal == ExitSignal.EXIT for signal in signals):
            return ExitSignal.EXIT
        else:
            return ExitSignal.HOLD


def recursive_batch_signals(tree):
    if isinstance(tree, (TradingStrategy, ExitTradingStrategy, EntryTradingStrategy)):  # the node is a strategy
        return tree.batch_signals()

    operator, strategies = tree

    # Calculate all buy/sell signals from the tree logic
    signals = [recursive_batch_signals(stgy) for stgy in strategies]
    batch_buy = np.array([signal.buy for signal in signals])
    batch_sell = np.array([signal.sell for signal in signals])

    if operator == 'priority':
        # Calculate priority number where the signal was triggered
        buy_argmax = np.argmax(batch_buy, axis=0)
        sell_argmax = np.argmax(batch_sell, axis=0)

        # if buy signal has greater priority than sells, buy signal remains
        buy_signals = buy_argmax < sell_argmax
        sell_signals = buy_argmax > sell_argmax

        # Sometimes no signal is generated. Above code has to be corrected by below
        zero_buy = np.all(~batch_buy, axis=0)
        zero_sell = np.all(~batch_sell, axis=0)

        buy_signals[zero_sell & ~zero_buy] = True
        sell_signals[zero_buy & ~zero_sell] = True

    elif operator == 'or':
        buy_signals = np.any(batch_buy, axis=0)
        sell_signals = np.any(batch_sell, axis=0)

    elif operator == 'and':
        buy_signals = np.all(batch_buy, axis=0)
        sell_signals = np.all(batch_sell, axis=0)

    return np.rec.array((buy_signals, sell_signals), dtype=[('buy', bool), ('sell', bool)])


class TrailingStopStrategy(AbstractStrategy):
    def __init__(self):
        super().__init__()
        self._rr_ratio = 0

    def calculate_stop_levels(
        self,
        candle: CandleLike,
        signal: EntrySignal = None,
    ) -> float:
        # Calculate new stop level based on whether we are in a long or short position
        adjustment, candle = self.get_adjustment(candle)

        if signal == EntrySignal.BUY:
            stop_loss = candle.close - adjustment
            take_profit = candle.close + self._rr_ratio * adjustment if self._rr_ratio else 0
        elif signal == EntrySignal.SELL:
            stop_loss = candle.close + adjustment
            take_profit = candle.close - self._rr_ratio * adjustment if self._rr_ratio else 0
        else:
            raise ValueError("No valid signal provided")
    
        return stop_loss, take_profit
    
    def calculate_stop_levels_2(
        self,
        candle: CandleLike,
        signal: EntrySignal = None,
    ) -> float:
        # Calculate new stop level based on whether we are in a long or short position
        adjustment, candle = self.get_adjustment(candle)

        if signal == EntrySignal.BUY:
            stop_loss = candle.close - adjustment
            take_profit = candle.close + self._rr_ratio * adjustment if self._rr_ratio else 0
        elif signal == EntrySignal.SELL:
            stop_loss = candle.close + adjustment
            take_profit = candle.close - self._rr_ratio * adjustment if self._rr_ratio else 0
        else:
            raise ValueError("No valid signal provided")

        return stop_loss, take_profit

    @abstractmethod
    def get_adjustment(
        self,
        candle: CandleLike,
        position: TradePosition,
    ) -> float:
        ...

    # @abstractmethod
    # def batch_adju