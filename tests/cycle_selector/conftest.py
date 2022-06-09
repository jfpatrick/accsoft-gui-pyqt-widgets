import pytest
from unittest import mock
from typing import Dict, List
from accwidgets.cycle_selector import CycleSelector
from ..async_shim import AsyncMock


@pytest.fixture
def populate_widget_menus(event_loop):

    def wrapper(widget: CycleSelector, data_tree: Dict[str, Dict[str, List[str]]]):
        with mock.patch("accwidgets.cycle_selector._model.CycleSelectorModel.fetch", new_callable=AsyncMock) as fetch:
            fetch.return_value = data_tree
            fetch.assert_not_awaited()
            event_loop.run_until_complete(widget._fetch_data())
            fetch.assert_awaited_once()

    return wrapper
