from unittest.mock import Mock

import pytest
from qtpy import QtWidgets
# qtpy.QTest incomplete: https://github.com/spyder-ide/qtpy/issues/197
from PyQt5 import QtTest
from qtpy.QtCore import Qt

import accwidgets.graph as accgraph


@pytest.mark.parametrize("orientation, layout", [
    (Qt.Horizontal, QtWidgets.QHBoxLayout),
    (Qt.Vertical, QtWidgets.QVBoxLayout),
])
def test_bar_layout(qtbot,
                    empty_testing_window,
                    orientation,
                    layout):
    qtbot.addWidget(empty_testing_window)
    bar = accgraph.EditingButtonBar(orientation)
    empty_testing_window.layout().addWidget(bar)
    assert isinstance(bar.layout(), layout)


@pytest.mark.parametrize("signal, button", [
    ("sig_send", "send_button"),
    ("sig_enable_selection_mode", "edit_button"),
])
def test_bar_signals(qtbot, empty_testing_window, signal, button):
    """
    Test if the right signals are emitted on an edit button press
    """
    qtbot.addWidget(empty_testing_window)
    bar = accgraph.EditingButtonBar()
    empty_testing_window.layout().addWidget(bar)

    signal = getattr(bar, signal)
    button = getattr(bar, button)

    spy = QtTest.QSignalSpy(signal)
    assert len(spy) == 0
    # Multiple button presses for buttons which can be toggled
    button.click()
    assert len(spy) == 1
    button.click()
    assert len(spy) == 2


@pytest.mark.parametrize("plots", [
    [Mock()],
    [Mock(), Mock()],
])
def test_plot_connection(qtbot, empty_testing_window, plots):
    """
    Check if the editable toggle button press is properly forwareded
    to the connected plots.
    """
    qtbot.addWidget(empty_testing_window)
    bar = accgraph.EditingButtonBar()
    empty_testing_window.layout().addWidget(bar)
    for plot in plots:
        bar.connect(plot)
        # Get rid of calls from setting up the connection
        plot.reset_mock()
    # Enable point selection
    bar.edit_button.click()
    for plot in plots:
        assert len(plot.set_selection_mode.mock_calls) == 1
        assert len(plot.send_all_editables_state.mock_calls) == 0
        plot.set_selection_mode.assert_called_with(True)
    # Disable point selection
    bar.edit_button.click()
    for plot in plots:
        assert len(plot.set_selection_mode.mock_calls) == 2
        assert len(plot.send_all_editables_state.mock_calls) == 0
        plot.set_selection_mode.assert_called_with(False)
    # Click send button
    bar.send_button.click()
    for plot in plots:
        assert len(plot.set_selection_mode.mock_calls) == 2
        assert len(plot.send_all_editables_state.mock_calls) == 1
        plot.send_all_editables_state.assert_called_once()


def test_disconnect(qtbot, empty_testing_window):
    """
    Check if disconnecting a single plot is possible without any side effects
    """
    plots = [Mock(), Mock()]
    qtbot.addWidget(empty_testing_window)
    bar = accgraph.EditingButtonBar()
    empty_testing_window.layout().addWidget(bar)

    for plot in plots:
        bar.connect(plot)
        # Get rid of calls from setting up the connection
        plot.reset_mock()

    # Enable point selection
    bar.edit_button.click()
    bar.send_button.click()
    for plot in plots:
        assert len(plot.set_selection_mode.mock_calls) == 1
        assert len(plot.send_all_editables_state.mock_calls) == 1
    bar.disconnect(plots[0])

    bar.edit_button.click()
    bar.send_button.click()

    assert len(plots[1].set_selection_mode.mock_calls) == 2
    assert len(plots[1].send_all_editables_state.mock_calls) == 2

    assert len(plots[0].set_selection_mode.mock_calls) == 1
    assert len(plots[0].send_all_editables_state.mock_calls) == 1
