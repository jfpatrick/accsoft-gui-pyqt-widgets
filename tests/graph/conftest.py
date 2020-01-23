"""Configuration File for pytest that introduces custom fixtures"""


import pytest

from tests.graph.mock_utils.widget_test_window import MinimalTestWindow


@pytest.fixture(autouse=False)
def minimal_test_window() -> MinimalTestWindow:
    """Fixture for creating a minimal Test Window."""
    window = MinimalTestWindow()
    window.show()
    return window
