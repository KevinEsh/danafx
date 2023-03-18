from metadata import EntrySignal, ExitSignal, AssetState
from typing import Union


class TradingStateMachine:
    """Define the state machine and its transitions
    """

    def __init__(self, symbol: str, init_state: AssetState = AssetState.NULL_POSITION) -> None:
        self.symbol = symbol
        self.state = init_state

    def transition(self, signal: Union[EntrySignal, ExitSignal]) -> None:
        # Looking for buy/sell entries when there is no positions
        if self.state == AssetState.NULL_POSITION:

            if signal == EntrySignal.BUY:
                # self.place_order("buy")
                self.state = AssetState.LONG_POSITION
                return
            elif signal == EntrySignal.SELL:
                # self.place_order("sell")
                self.state = AssetState.SHORT_POSITION
                return
            elif signal == EntrySignal.NEUTRAL:
                return
            else:
                raise ValueError(f"Entry {signal=} not recognized")

        # Looking for buy/sell entries when there is no positions
        elif self.state == AssetState.LONG_POSITION:
            # Strategic exit is raised by touching a Take-Profit
            if signal in [ExitSignal.STRATEGIC_EXIT, ExitSignal.EARLY_EXIT]:
                self.state = AssetState.NULL_POSITION
                return
            elif signal == ExitSignal.HOLD:
                return
            else:
                raise ValueError(f"Exit {signal=} not recognized")

        elif self.state == AssetState.SHORT_POSITION:
            # Early exit is raised when the algorithm detect high volatity
            if signal in [ExitSignal.STRATEGIC_EXIT, ExitSignal.EARLY_EXIT]:
                self.state = AssetState.NULL_POSITION
                return
            elif signal == ExitSignal.HOLD:
                return
            else:
                raise ValueError(f"Exit {signal=} not recognized")
