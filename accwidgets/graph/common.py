from typing import Optional, List, TypeVar, Generic


_STATE = TypeVar("_STATE")
"""Generic State used for the history class."""


class History(Generic[_STATE]):

    MAX_ROLLBACK = 50
    """Maximum amount of possible rollbacks, this is used so the history
    does not grow uncontrolled."""

    def __init__(self):
        """
        Utility class that allows object's state to be easily undo- and
        redoable by saving the history of state changes.
        """
        self._states: List[_STATE] = []
        self._current: int = -1

    @property
    def current_state(self) -> Optional[_STATE]:
        """Get the most recent state the history index is pointing to."""
        try:
            return self._states[self._current]
        except IndexError:
            return None

    @property
    def undoable(self) -> bool:
        """Is a undo currently possible?"""
        return self._current >= 0

    @property
    def redoable(self) -> bool:
        """Is a redo currently possible?"""
        return self._current < len(self._states) - 1

    def save_state(self, state: _STATE) -> None:
        """
        Save the given state to the history. States that have been undone
        before this state will be thrown away.

        Args:
            state: state which should be saved in this history
        """
        self._states = self._states[:self._current + 1]
        self._states.append(state)
        if len(self._states) > History.MAX_ROLLBACK:
            self._states.pop(0)
        else:
            self._current += 1

    def undo(self) -> Optional[_STATE]:
        """Go back to the last state in the history.

        Returns:
            The current state before the undo operation
        """
        if not self.undoable:
            return None
        undone = self._states[self._current]
        self._current -= 1
        return undone

    def redo(self) -> Optional[_STATE]:
        """Redo the last editing step if possible.

        Returns:
            The current state before the redo operation
        """
        if not self.redoable:
            return None
        redone = self._states[self._current]
        self._current += 1
        return redone
