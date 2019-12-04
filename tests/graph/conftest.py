"""Configuration File for pytest that introduces custom fixtures"""

import warnings

import pytest
from typing import Generator

from accwidgets import graph as accgraph
from tests.graph.mock_utils.widget_test_window import MinimalTestWindow


@pytest.fixture(autouse=False)
def minimal_test_window() -> MinimalTestWindow:
    """Fixture for creating """
    window = MinimalTestWindow()
    window.show()
    return window


@pytest.fixture(autouse=False)
def warn_always() -> Generator:
    """
    Fixture for enabling warnings to always be emitted.
    After the test is done, the warning filters will be reset, so filters
    are not carried over into other tests.
    """
    warnings.simplefilter("always", accgraph.InvalidDataStructureWarning)
    yield  # Run actual test
    warnings.resetwarnings()
