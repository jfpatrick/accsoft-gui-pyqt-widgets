import pytest
import urllib3.exceptions
from typing import Dict, List
from unittest import mock
from pyccda import AsyncAPI
from accwidgets.cycle_selector import CycleSelectorModel, CycleSelectorConnectionError
from ..async_shim import AsyncMock


@pytest.fixture
def mock_fetch(event_loop):

    def wrapper(returned_selectors: Dict[str, Dict[str, List[str]]]):

        def make_sel_iter_side_effect(sel_objects):
            sel_iter = iter(sel_objects)

            def side_effect():
                try:
                    return next(sel_iter)
                except StopIteration:
                    raise StopAsyncIteration

            return side_effect

        objects = []
        for domain, groups in returned_selectors.items():
            domain_obj = mock.MagicMock()
            objects.append(domain_obj)
            domain_obj.name = domain
            domain_obj.selector_groups = []
            for group, lines in groups.items():
                group_obj = mock.MagicMock()
                domain_obj.selector_groups.append(group_obj)
                group_obj.name = group
                group_obj.selector_values = []
                for line in lines:
                    line_obj = mock.MagicMock()
                    group_obj.selector_values.append(line_obj)
                    line_obj.name = line

        pagination_iter = AsyncMock()
        pagination_iter.__anext__ = AsyncMock(side_effect=make_sel_iter_side_effect(objects))
        selector_pages = AsyncMock()
        selector_pages.__aiter__ = mock.MagicMock(return_value=pagination_iter)
        ccda = mock.MagicMock(spec=AsyncAPI)
        ccda.SelectorDomain.search = AsyncMock(return_value=selector_pages)
        return ccda

    return wrapper


def test_model_init_with_default_ccda_api():
    model = CycleSelectorModel()
    assert isinstance(model._ccda, AsyncAPI)


def test_model_init_with_custom_ccda_api():
    api = AsyncAPI()
    model = CycleSelectorModel(ccda=api)
    assert model._ccda is api


@pytest.mark.parametrize("error_type", [TypeError, ValueError, urllib3.exceptions.HTTPError, urllib3.exceptions.SSLError])
def test_model_fetch_throws_on_pyccda_error(event_loop, error_type):
    api_mock = mock.MagicMock()
    search_mock = AsyncMock(side_effect=error_type("Test error"))
    api_mock.SelectorDomain.search = search_mock
    model = CycleSelectorModel(ccda=api_mock)
    with pytest.raises(CycleSelectorConnectionError, match="Test error"):
        event_loop.run_until_complete(model.fetch())


def test_model_fetch_succeeds(event_loop, mock_fetch):
    dict_repr = {
        "SPS": {
            "PARTY": ["ION", "PROTON", "ALL"],
            "USER": ["LHC", "ALL"],
        },
        "LHC": {
            "USER": ["ALL", "MD1"],
        },
    }
    api_mock = mock_fetch(dict_repr)
    model = CycleSelectorModel(ccda=api_mock)
    res = event_loop.run_until_complete(model.fetch())
    assert res == dict_repr
