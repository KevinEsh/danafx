from metadata import EntrySignal, ExitSignal, AssetState
from typing import Union


class AssetStateMachine:
    """Define the state machine and its transitions
    """

    def __init__(self, symbol: str, init_state: AssetState = AssetState.NULL_POSITION) -> None:
        self.symbol = symbol
        self._state = init_state

    def transition(self, signal: Union[EntrySignal, ExitSignal]):
        # Looking for buy/sell entries when there is no positions
        if self._state == AssetState.NULL_POSITION:

            if signal == EntrySignal.NEUTRAL.value:
                return
            if signal in [EntrySignal.BUY.value, EntrySignal.SELL.value]:
                self._state = AssetState.WAITING_POSITION
                return
            else:
                raise ValueError(f"Entry {signal=} not recognized")

        elif self._state == AssetState.WAITING_POSITION:
            if signal == EntrySignal.BUY.value:
                self._state = AssetState.LONG_POSITION
                return
            elif signal == EntrySignal.SELL.value:
                self._state = AssetState.SHORT_POSITION
                return
            elif signal == EntrySignal.NEUTRAL.value:
                return
            else:
                raise ValueError(f"Entry {signal=} not recognized")

        # Looking for buy/sell entries when there is no positions
        elif self._state in [AssetState.LONG_POSITION, AssetState.SHORT_POSITION]:
            # Strategic exit is raised by touching a Take-Profit
            if signal == ExitSignal.EXIT.value:
                self._state = AssetState.NULL_POSITION
                return
            elif signal == ExitSignal.HOLD.value:
                return
            else:
                raise ValueError(f"Exit {signal=} not recognized")

    def is_entry(self, signal: EntrySignal) -> bool:
        if signal in [EntrySignal.BUY.value, EntrySignal.SELL.value]:
            return True
        return False

    def is_exit(self, signal: ExitSignal) -> bool:
        if signal == ExitSignal.EXIT.value:
            return True
        return False

    @ property
    def no_position(self) -> bool:
        return self._state == AssetState.NULL_POSITION

    @ property
    def awaiting_position(self) -> bool:
        return self._state == AssetState.WAITING_POSITION

    @ property
    def on_long(self) -> bool:
        return self._state == AssetState.LONG_POSITION

    @ property
    def on_short(self) -> bool:
        return self._state == AssetState.SHORT_POSITION


if __name__ == "__main__":
    s = AssetStateMachine()
