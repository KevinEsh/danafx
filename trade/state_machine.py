from trade.metadata import EntrySignal, ExitSignal, AssetState
from typing import Union


class AssetStateMachine:
    """Define the state machine and its transitions
    """

    def __init__(self, init_state: AssetState = AssetState.NULL_POSITION) -> None:
        self._state = init_state

    def next(self):
        # looking for buy/sell entries when there is no positions
        if self._state == AssetState.NULL_POSITION:
            self._state = AssetState.WAITING_POSITION
        # An entry was found, wait until the order is taken by the broker
        elif self._state == AssetState.WAITING_POSITION:
            self._state = AssetState.ON_POSITION
        # looking for buy/sell exits when there is a position placed
        elif self._state == AssetState.ON_POSITION:
            self._state = AssetState.NULL_POSITION
        return

    def is_entry(self, signal: EntrySignal) -> bool:
        if signal in [EntrySignal.BUY, EntrySignal.SELL]:
            return True
        return False

    def is_exit(self, signal: ExitSignal) -> bool:
        if signal == ExitSignal.EXIT:
            return True
        return False

    @ property
    def null_position(self) -> bool:
        return self._state == AssetState.NULL_POSITION

    @ property
    def awaiting_position(self) -> bool:
        return self._state == AssetState.WAITING_POSITION

    @ property
    def on_position(self) -> bool:
        return self._state == AssetState.ON_POSITION


if __name__ == "__main__":
    s = AssetStateMachine()
