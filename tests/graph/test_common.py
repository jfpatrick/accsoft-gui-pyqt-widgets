from accwidgets.graph.common import History


def test_empty_his():
    """Tests, that editing is properly propagated to the update source"""
    his = History[int]()
    assert not his.undoable
    assert not his.redoable
    his.save_state(state=0)
    assert his.undoable
    assert not his.redoable


def test_simple_undo_and_redo():
    """Undo and redo a bunch of states"""
    his = History[int]()
    states = list(range(1, 50))
    for i in states:
        his.save_state(state=i)
        assert his._states == list(range(1, i + 1))
    for i in reversed(states):
        his.undo() == i
        # History is preserved for redo
        assert his._states == states
    # No more undos are possible
    assert his.undo() is None
    for i in states:
        his.redo() == i
        assert his._states == states
    # No more redos are possible
    assert his.redo() is None


def test_exceed_max_rollbacks():
    """Amount of state exceeds the maximum amount of saved states"""
    his = History[int]()
    states = list(range(1, 60))
    for i in states:
        his.save_state(state=i)
    for _ in range(1, 50):
        his.undo() is not None
    his.undo() is None


def test_fork():
    """
    Tested scenario:
    17 - 18 - 19 - 20
               \
               21 - 22 - 23
    """
    his = History[int]()
    states = list(range(1, 20))
    for i in states:
        his.save_state(state=i)
    assert his._states == states
    assert his.undo() is not None
    truncated_states = list(range(1, 19))
    # The old state is still available
    assert his._states == states
    his.save_state(state=21)
    his.save_state(state=22)
    his.save_state(state=23)
    assert his._states == truncated_states + [21, 22, 23]
