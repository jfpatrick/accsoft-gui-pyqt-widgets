"""Configuration File for pytest that introduces custom fixtures"""


import pytest
from pytestqt.qtbot import QtBot
from accwidgets.graph import ExPlotWidgetConfig, EditablePlotWidget
from tests.graph.mock_utils.widget_test_window import MinimalTestWindow


@pytest.fixture
def minimal_test_window(qtbot: QtBot) -> MinimalTestWindow:
    """Fixture for creating a minimal Test Window."""
    window = MinimalTestWindow(plot=ExPlotWidgetConfig())
    qtbot.add_widget(window)
    with qtbot.wait_exposed(window):
        window.show()
    return window


@pytest.fixture
def empty_testing_window(qtbot: QtBot) -> MinimalTestWindow:
    """Fixture for creating a minimal Test Window."""
    window = MinimalTestWindow()
    qtbot.add_widget(window)
    with qtbot.wait_exposed(window):
        window.show()
    return window


@pytest.fixture
def editable_testing_window(qtbot: QtBot) -> MinimalTestWindow:
    """Fixture for creating a minimal Test Window."""
    window = MinimalTestWindow(plot=EditablePlotWidget())
    qtbot.add_widget(window)
    with qtbot.wait_exposed(window):
        window.show()
    return window
