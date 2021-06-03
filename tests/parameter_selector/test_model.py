import asyncio

import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt, QVariant, QModelIndex
from qtpy.QtWidgets import QListView
from qtpy.QtGui import QFont
from accwidgets.parameter_selector._model import (get_ccda, SearchResultsModel, SearchProxyModel, ExtendableProxyModel,
                                                  look_up_ccda)
from ..async_shim import AsyncMock


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.fixture(scope="function")
async def root_model():
    root = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    data = [
        ("dev1", [("prop1", [])]),
        ("dev2", [("prop2", ["field2"])]),
        ("dev3", [("prop3.1", ["field3.1.1"]), ("prop3.2", ["field3.2.1", "field3.2.2"])]),
    ]
    # Prevent creating tasks to load mode
    with mock.patch.object(root, "canFetchMore", return_value=False):
        root.set_data(mocked_iterator, data)
    return root


def make_italic_font() -> QFont:
    font = QFont()
    font.setItalic(True)
    return font


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("data", [
    None,
    [],
    [("dev", [])],
])
async def test_root_model_set_data_resets_model(qtbot: QtBot, data):
    model = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    with qtbot.wait_signal(model.modelReset):
        model.set_data(mocked_iterator, data)
        assert model._data == (data or [])


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("data", [
    None,
    [],
    [("dev", [])],
])
async def test_root_model_set_data_cancels_active_requests(data):
    model = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    with mock.patch.object(model, "cancel_active_requests") as cancel_active_requests:
        model.set_data(mocked_iterator, data)
        cancel_active_requests.assert_called_once_with()


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("data", [
    None,
    [],
    [("dev", [])],
])
async def test_root_model_set_data_updates_rows_with_first_batch(data):
    model = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    with mock.patch.object(model, "_trigger_row_update") as trigger_row_update:
        model.set_data(mocked_iterator, data)
        trigger_row_update.assert_called_once_with(new_data=data, loading=False)


@pytest.mark.parametrize("can_fetch_more,should_request", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("data", [
    None,
    [],
    [("dev", [])],
])
def test_root_model_set_data_requests_next_batch(data, can_fetch_more, should_request):
    model = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    with mock.patch.object(model, "canFetchMore", return_value=can_fetch_more):
        with mock.patch.object(model, "fetchMore") as fetchMore:
            model.set_data(mocked_iterator, data)
            if should_request:
                fetchMore.assert_called_once_with(QModelIndex())
            else:
                fetchMore.assert_not_called()


@pytest.mark.parametrize("active_task", [None, mock.MagicMock()])
@pytest.mark.parametrize("is_loading", [True, False])
def test_root_model_cancel_active_requests(active_task, is_loading):
    model = SearchResultsModel()
    model._active_task = active_task
    model._is_loading = is_loading
    assert model.is_loading == is_loading
    model.cancel_active_requests()
    if active_task:
        active_task.cancel.assert_called()
    assert model.is_loading is False


@pytest.mark.parametrize("is_loading,iter_exists,iter_exhausted,expect_positive", [
    (True, True, True, False),
    (False, True, True, False),
    (True, False, True, False),
    (False, False, True, False),
    (True, True, False, False),
    (False, True, False, True),
    (True, False, False, False),
    (False, False, False, False),
])
def test_root_model_can_fetch_more(is_loading, iter_exhausted, iter_exists, expect_positive):
    model = SearchResultsModel()
    model._iter_exhausted = iter_exhausted
    model._is_loading = is_loading
    model._iter = mock.MagicMock() if iter_exists else None
    assert model.canFetchMore(QModelIndex()) == expect_positive


@pytest.mark.asyncio
@pytest.mark.parametrize("is_loading,expect_task_created", [
    (True, False),
    (False, True),
])
async def test_root_model_fetch_more(is_loading, expect_task_created):
    model = SearchResultsModel()
    model._is_loading = is_loading
    with mock.patch.object(model, "_do_fetch_more", new_callable=AsyncMock) as do_fetch_more:
        model.fetchMore(QModelIndex())
        do_fetch_more.assert_not_called()
        if expect_task_created:
            assert model._active_task is not None
            await model._active_task
            do_fetch_more.assert_called_once_with()
        else:
            assert model._active_task is None


@pytest.mark.parametrize("role,valid_idx,expect_return_full_data", [
    (Qt.DisplayRole, True, True),
    (Qt.DisplayRole, False, False),
    (Qt.EditRole, True, False),
    (Qt.EditRole, False, False),
    (Qt.FontRole, True, False),
    (Qt.FontRole, False, False),
])
def test_root_model_data_always_returns_full_collection(role, valid_idx, expect_return_full_data):
    specific_data = mock.MagicMock()
    model = SearchResultsModel()
    model._data = specific_data
    index = mock.MagicMock()
    index.isValid.return_value = valid_idx
    res = model.data(index, role)
    if expect_return_full_data:
        assert res is specific_data
    else:
        assert res == QVariant()


@pytest.mark.parametrize("row,column,expected_flags", [
    (0, 0, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (1, 0, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (-1, 0, Qt.ItemNeverHasChildren),
    (0, -1, Qt.ItemNeverHasChildren),
    (-1, -1, Qt.ItemNeverHasChildren),
])
def test_root_model_flags(row, column, expected_flags):
    model = SearchResultsModel()
    index = model.createIndex(row, column)
    assert model.flags(index) == expected_flags


@pytest.mark.parametrize("initial_val,new_val,expected_val,expect_emit_signal", [
    (True, True, True, False),
    (True, False, False, True),
    (False, True, True, True),
    (False, False, False, False),
])
def test_root_model_set_loading(qtbot: QtBot, initial_val, new_val, expected_val, expect_emit_signal):
    model = SearchResultsModel()
    model._is_loading = initial_val
    assert model.is_loading == initial_val
    with qtbot.wait_signal(model.loading_state_changed, raising=False, timeout=100) as blocker:
        model._set_loading(new_val)
    assert model.is_loading == expected_val
    assert blocker.signal_triggered == expect_emit_signal
    if expect_emit_signal:
        assert blocker.args == [expected_val]


@pytest.mark.asyncio
@pytest.mark.parametrize("iter_exists,expect_trigger_rows,expect_request_next_batch", [
    (True, True, True),
    (False, False, False),
])
async def test_root_model_do_fetch_more_no_iter_noop(iter_exists, expect_request_next_batch,
                                                     expect_trigger_rows):
    model = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    async_mock = AsyncMock()
    async_mock.return_value = []
    mocked_iterator.__anext__ = async_mock
    assert model._iter is None
    if iter_exists:
        model._iter = mocked_iterator
    with mock.patch.object(model, "_trigger_row_update") as trigger_row_update:
        await model._do_fetch_more()
        if expect_trigger_rows:
            trigger_row_update.assert_called()
        else:
            trigger_row_update.assert_not_called()
        if expect_request_next_batch:
            async_mock.assert_called_once()
        else:
            async_mock.assert_not_called()


@pytest.mark.asyncio
async def test_root_model_do_fetch_more_updates_rows_with_loading_cell():
    model = SearchResultsModel()

    def side_effect():
        assert model.is_loading is True
        return []

    mocked_iterator = mock.MagicMock()
    async_mock = AsyncMock()
    async_mock.side_effect = side_effect
    mocked_iterator.__anext__ = async_mock
    model._iter = mocked_iterator
    assert model.is_loading is False
    await model._do_fetch_more()
    assert model.is_loading is False


@pytest.mark.asyncio
@pytest.mark.parametrize("batches,expected_data", [
    (
        [
            [],
            [],
        ],
        [
            [],
            [],
        ],
    ),
    (
        [
            [("dev1", [])],
            [("dev2", [("prop", ["field"])])],
        ],
        [
            [("dev1", [])],
            [("dev1", []), ("dev2", [("prop", ["field"])])],
        ],
    ),

])
async def test_root_model_do_fetch_more_success(batches, expected_data):
    model = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    async_mock = AsyncMock()
    mocked_iterator.__anext__ = async_mock
    model._iter = mocked_iterator
    assert model._data == []
    for next_batch, expected_aggregated_data in zip(batches, expected_data):
        async_mock.return_value = next_batch
        await model._do_fetch_more()
        assert model._data == expected_aggregated_data


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_data", [
    [],
    [("dev1", [])],
    [("dev1", []), ("dev2", [("prop", ["field"])])],
])
async def test_root_model_do_fetch_more_iter_exhausted(initial_data):
    model = SearchResultsModel()
    mocked_iterator = mock.MagicMock()
    async_mock = AsyncMock()
    async_mock.side_effect = StopAsyncIteration
    mocked_iterator.__anext__ = async_mock
    model._iter = mocked_iterator
    with mock.patch.object(model, "fetchMore"):
        model.set_data(mocked_iterator, initial_data)
    assert model._data == initial_data
    assert model._iter_exhausted is False
    assert model._iter is not None
    await model._do_fetch_more()
    assert model._data == initial_data
    assert model._iter_exhausted is True
    assert model._iter is not None


def test_proxy_model_default_selected_idx():
    model = SearchProxyModel()
    assert model.selected_idx == -1


@pytest.mark.parametrize("row,role,expected_data", [
    (-1, Qt.DisplayRole, QVariant()),
    (-1, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, Qt.EditRole, QVariant()),
    (-1, Qt.FontRole, QVariant()),
    (0, Qt.DisplayRole, "dev1"),
    (0, SearchProxyModel._LIST_ROLE, [("prop1", [])]),
    (0, Qt.EditRole, QVariant()),
    (0, Qt.FontRole, QVariant()),
    (1, Qt.DisplayRole, "dev2"),
    (1, SearchProxyModel._LIST_ROLE, [("prop2", ["field2"])]),
    (1, Qt.EditRole, QVariant()),
    (1, Qt.FontRole, QVariant()),
    (2, Qt.DisplayRole, "dev3"),
    (2, SearchProxyModel._LIST_ROLE, [("prop3.1", ["field3.1.1"]), ("prop3.2", ["field3.2.1", "field3.2.2"])]),
    (2, Qt.EditRole, QVariant()),
    (2, Qt.FontRole, QVariant()),
])
def test_proxy_model_data_from_first_child(root_model, row, role, expected_data):
    proxy = SearchProxyModel()
    proxy.setSourceModel(root_model)
    index = proxy.createIndex(row, 0)
    assert index.data(role) == expected_data


@pytest.mark.parametrize("selected_dev,row,role,expected_data", [
    (-1, -1, Qt.DisplayRole, QVariant()),
    (-1, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, -1, Qt.EditRole, QVariant()),
    (-1, -1, Qt.FontRole, QVariant()),
    (-1, 0, Qt.DisplayRole, QVariant()),
    (-1, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, 0, Qt.EditRole, QVariant()),
    (-1, 0, Qt.FontRole, QVariant()),
    (-1, 1, Qt.DisplayRole, QVariant()),
    (-1, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, 1, Qt.EditRole, QVariant()),
    (-1, 1, Qt.FontRole, QVariant()),
    (-1, 2, Qt.DisplayRole, QVariant()),
    (-1, 2, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, 2, Qt.EditRole, QVariant()),
    (-1, 2, Qt.FontRole, QVariant()),
    (0, -1, Qt.DisplayRole, QVariant()),
    (0, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, -1, Qt.EditRole, QVariant()),
    (0, -1, Qt.FontRole, QVariant()),
    (0, 0, Qt.DisplayRole, "prop1"),
    (0, 0, SearchProxyModel._LIST_ROLE, []),
    (0, 0, Qt.EditRole, QVariant()),
    (0, 0, Qt.FontRole, QVariant()),
    (0, 1, Qt.DisplayRole, QVariant()),
    (0, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, 1, Qt.EditRole, QVariant()),
    (0, 1, Qt.FontRole, QVariant()),
    (1, -1, Qt.DisplayRole, QVariant()),
    (1, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (1, -1, Qt.EditRole, QVariant()),
    (1, -1, Qt.FontRole, QVariant()),
    (1, 0, Qt.DisplayRole, "prop2"),
    (1, 0, SearchProxyModel._LIST_ROLE, ["field2"]),
    (1, 0, Qt.EditRole, QVariant()),
    (1, 0, Qt.FontRole, QVariant()),
    (1, 1, Qt.DisplayRole, QVariant()),
    (1, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (1, 1, Qt.EditRole, QVariant()),
    (1, 1, Qt.FontRole, QVariant()),
    (2, -1, Qt.DisplayRole, QVariant()),
    (2, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, -1, Qt.EditRole, QVariant()),
    (2, -1, Qt.FontRole, QVariant()),
    (2, 0, Qt.DisplayRole, "prop3.1"),
    (2, 0, SearchProxyModel._LIST_ROLE, ["field3.1.1"]),
    (2, 0, Qt.EditRole, QVariant()),
    (2, 0, Qt.FontRole, QVariant()),
    (2, 1, Qt.DisplayRole, "prop3.2"),
    (2, 1, SearchProxyModel._LIST_ROLE, ["field3.2.1", "field3.2.2"]),
    (2, 1, Qt.EditRole, QVariant()),
    (2, 1, Qt.FontRole, QVariant()),
    (2, 2, Qt.DisplayRole, QVariant()),
    (2, 2, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 2, Qt.EditRole, QVariant()),
    (2, 2, Qt.FontRole, QVariant()),
])
def test_proxy_model_data_from_second_child(root_model, selected_dev, row, role, expected_data):
    dev_proxy = SearchProxyModel()
    dev_proxy.setSourceModel(root_model)
    dev_proxy.update_selection(selected_dev)
    prop_proxy = SearchProxyModel()
    prop_proxy.setSourceModel(dev_proxy)
    index = prop_proxy.createIndex(row, 0)
    assert index.data(role) == expected_data


@pytest.mark.parametrize("selected_dev,selected_prop,row,role,expected_data", [
    (-1, 0, -1, Qt.DisplayRole, QVariant()),
    (-1, 0, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, 0, -1, Qt.EditRole, QVariant()),
    (-1, 0, 0, Qt.DisplayRole, QVariant()),
    (-1, 0, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, 0, 0, Qt.EditRole, QVariant()),
    (-1, 0, 1, Qt.DisplayRole, QVariant()),
    (-1, 0, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, 0, 1, Qt.EditRole, QVariant()),
    (-1, 0, 2, Qt.DisplayRole, QVariant()),
    (-1, 0, 2, SearchProxyModel._LIST_ROLE, QVariant()),
    (-1, 0, 2, Qt.EditRole, QVariant()),
    (0, 0, -1, Qt.DisplayRole, QVariant()),
    (0, 0, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, 0, -1, Qt.EditRole, QVariant()),
    (0, 0, 0, Qt.DisplayRole, QVariant()),
    (0, 0, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, 0, 0, Qt.EditRole, QVariant()),
    (0, 0, 1, Qt.DisplayRole, QVariant()),
    (0, 0, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, 0, 1, Qt.EditRole, QVariant()),
    (0, -1, -1, Qt.DisplayRole, QVariant()),
    (0, -1, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, -1, -1, Qt.EditRole, QVariant()),
    (0, -1, 0, Qt.DisplayRole, QVariant()),
    (0, -1, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, -1, 0, Qt.EditRole, QVariant()),
    (0, -1, 1, Qt.DisplayRole, QVariant()),
    (0, -1, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (0, -1, 1, Qt.EditRole, QVariant()),
    (1, 0, -1, Qt.DisplayRole, QVariant()),
    (1, 0, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (1, 0, -1, Qt.EditRole, QVariant()),
    (1, 0, 0, Qt.DisplayRole, "field2"),
    (1, 0, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (1, 0, 0, Qt.EditRole, QVariant()),
    (1, 0, 1, Qt.DisplayRole, QVariant()),
    (1, 0, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (1, 0, 1, Qt.EditRole, QVariant()),
    (1, -1, -1, Qt.DisplayRole, QVariant()),
    (1, -1, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (1, -1, -1, Qt.EditRole, QVariant()),
    (1, -1, 0, Qt.DisplayRole, QVariant()),
    (1, -1, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (1, -1, 0, Qt.EditRole, QVariant()),
    (1, -1, 1, Qt.DisplayRole, QVariant()),
    (1, -1, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 0, -1, Qt.DisplayRole, QVariant()),
    (2, 0, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 0, -1, Qt.EditRole, QVariant()),
    (2, 0, 0, Qt.DisplayRole, "field3.1.1"),
    (2, 0, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 0, 0, Qt.EditRole, QVariant()),
    (2, 0, 1, Qt.DisplayRole, QVariant()),
    (2, 0, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 0, 1, Qt.EditRole, QVariant()),
    (2, 0, 2, Qt.DisplayRole, QVariant()),
    (2, 0, 2, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 0, 2, Qt.EditRole, QVariant()),
    (2, -1, -1, Qt.DisplayRole, QVariant()),
    (2, -1, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, -1, -1, Qt.EditRole, QVariant()),
    (2, -1, 0, Qt.DisplayRole, QVariant()),
    (2, -1, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, -1, 0, Qt.EditRole, QVariant()),
    (2, -1, 1, Qt.DisplayRole, QVariant()),
    (2, -1, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, -1, 1, Qt.EditRole, QVariant()),
    (2, -1, 2, Qt.DisplayRole, QVariant()),
    (2, -1, 2, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, -1, 2, Qt.EditRole, QVariant()),
    (2, 1, -1, Qt.DisplayRole, QVariant()),
    (2, 1, -1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 1, -1, Qt.EditRole, QVariant()),
    (2, 1, 0, Qt.DisplayRole, "field3.2.1"),
    (2, 1, 0, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 1, 0, Qt.EditRole, QVariant()),
    (2, 1, 1, Qt.DisplayRole, "field3.2.2"),
    (2, 1, 1, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 1, 1, Qt.EditRole, QVariant()),
    (2, 1, 2, Qt.DisplayRole, QVariant()),
    (2, 1, 2, SearchProxyModel._LIST_ROLE, QVariant()),
    (2, 1, 2, Qt.EditRole, QVariant()),
])
def test_proxy_model_data_from_leaf(root_model, selected_dev, selected_prop, row, role, expected_data):
    dev_proxy = SearchProxyModel()
    dev_proxy.setSourceModel(root_model)
    dev_proxy.update_selection(selected_dev)
    prop_proxy = SearchProxyModel()
    prop_proxy.setSourceModel(dev_proxy)
    prop_proxy.update_selection(selected_prop)
    field_proxy = SearchProxyModel()
    field_proxy.setSourceModel(prop_proxy)
    index = field_proxy.createIndex(row, 0)
    assert index.data(role) == expected_data


@pytest.mark.parametrize("selected_dev,selected_prop,expected_count", [
    (-1, 0, 0),
    (0, -1, 0),
    (0, 0, 0),
    (0, 1, 0),
    (1, 0, 1),
    (2, 0, 1),
    (2, 1, 2),
])
def test_proxy_model_row_count_from_leaf(root_model, selected_dev, selected_prop, expected_count):
    dev_proxy = SearchProxyModel()
    dev_proxy.setSourceModel(root_model)
    dev_proxy.update_selection(selected_dev)
    prop_proxy = SearchProxyModel()
    prop_proxy.setSourceModel(dev_proxy)
    prop_proxy.update_selection(selected_prop)
    field_proxy = SearchProxyModel()
    field_proxy.setSourceModel(prop_proxy)
    assert field_proxy.rowCount() == expected_count


def test_proxy_model_row_count_from_first_child(root_model):
    dev_proxy = SearchProxyModel()
    dev_proxy.setSourceModel(root_model)
    assert dev_proxy.rowCount() == 3


@pytest.mark.parametrize("selected_dev,expected_count", [
    (-1, 0),
    (0, 1),
    (1, 1),
    (2, 2),
])
def test_proxy_model_row_count_from_second_child(root_model, selected_dev, expected_count):
    dev_proxy = SearchProxyModel()
    dev_proxy.setSourceModel(root_model)
    dev_proxy.update_selection(selected_dev)
    prop_proxy = SearchProxyModel()
    prop_proxy.setSourceModel(dev_proxy)
    assert prop_proxy.rowCount() == expected_count


@pytest.mark.parametrize("old_model_type", [SearchResultsModel, SearchProxyModel])
@pytest.mark.parametrize("new_model_type", [SearchResultsModel, SearchProxyModel])
def test_proxy_model_set_source_model_disconnects_old(old_model_type, new_model_type):
    old = old_model_type()
    new = new_model_type()
    model = SearchProxyModel()
    model.setSourceModel(old)
    try:
        assert old.receivers(old.selection_changed) > 0
    except AttributeError:
        assert old.receivers(old.modelReset) > 0
    model.setSourceModel(new)
    assert old.receivers(old.modelReset) == 0
    try:
        assert old.receivers(old.selection_changed) == 0
    except AttributeError:
        pass


@pytest.mark.parametrize("src_model_type", [SearchResultsModel, SearchProxyModel])
def test_proxy_model_set_source_model_connects_new(src_model_type):
    src = src_model_type()
    assert src.receivers(src.modelReset) == 0
    try:
        assert src.receivers(src.selection_changed) == 0
    except AttributeError:
        pass
    model = SearchProxyModel()
    model.setSourceModel(src)
    try:
        assert src.receivers(src.selection_changed) > 0
    except AttributeError:
        assert src.receivers(src.modelReset) > 0


@pytest.mark.parametrize("src_model_type", [SearchResultsModel, SearchProxyModel])
def test_proxy_model_set_source_model_resets(qtbot: QtBot, src_model_type):
    src = src_model_type()
    model = SearchProxyModel()
    with qtbot.wait_signal(model.modelReset):
        model.setSourceModel(src)


@pytest.mark.parametrize("initial_idx,row,row_count,expect_emits_signal,expected_new_idx", [
    (-1, 0, 0, False, -1),
    (-1, 0, 1, True, 0),
    (-1, 99, 0, False, -1),
    (-1, 99, 1, False, -1),
    (-1, 99, 105, True, 99),
    (0, 0, 0, False, 0),
    (0, 0, 1, True, 0),
    (0, 99, 0, False, 0),
    (0, 99, 1, False, 0),
    (0, 99, 105, True, 99),
    (100, 0, 0, False, 100),
    (100, 0, 1, True, 0),
    (100, 99, 0, False, 100),
    (100, 99, 1, False, 100),
    (100, 99, 105, True, 99),
])
@pytest.mark.parametrize("create_index", [True, False])
def test_proxy_model_update_selection(qtbot: QtBot, create_index, initial_idx, row, row_count,
                                      expect_emits_signal, expected_new_idx):
    model = SearchProxyModel()
    if create_index:
        idx = model.createIndex(row, 0)
    else:
        idx = row
    model.selected_idx = initial_idx
    with qtbot.wait_signal(model.selection_changed, raising=False, timeout=100) as blocker:
        with mock.patch.object(model, "rowCount", return_value=row_count):
            model.update_selection(idx)
    assert blocker.signal_triggered == expect_emits_signal
    assert model.selected_idx == expected_new_idx


def test_proxy_model_reset_selected_idx_resets_model(qtbot: QtBot):
    model = SearchProxyModel()
    with qtbot.wait_signal(model.modelReset):
        model.reset_selected_idx()


@pytest.mark.parametrize("orig_idx", [-1, 0, 1])
@pytest.mark.parametrize("row_cnt,expected_final_idx", [
    (0, -1),
    (1, 0),
    (2, 0),
])
def test_proxy_model_reset_selected_idx_updates_index(orig_idx, row_cnt, expected_final_idx):
    model = SearchProxyModel()
    model.selected_idx = orig_idx
    with mock.patch.object(model, "rowCount", return_value=row_cnt):
        model.reset_selected_idx()
    assert model.selected_idx == expected_final_idx


@pytest.mark.parametrize("initial_selected_idx", [-1, 0, 1])
def test_proxy_model_install_connects_view(qtbot: QtBot, initial_selected_idx):
    model = SearchProxyModel()
    model.selected_idx = initial_selected_idx
    view = QListView()
    qtbot.add_widget(view)
    assert model.receivers(model.selection_changed) == 0
    assert view.selectionModel() is None
    with mock.patch.object(view, "scrollTo") as scrollTo:
        model.install(view)
        scrollTo.assert_called_once()
    assert view.selectionModel() is not None
    assert model.receivers(model.selection_changed) == 1
    assert view.model() is model
    assert view.selectionModel().currentIndex().row() == initial_selected_idx


def test_view_selection_model_does_not_loop(qtbot: QtBot):
    model = SearchProxyModel()
    view = QListView()
    qtbot.add_widget(view)
    model.install(view)
    # QSignalBlocker must be installed in logic to avoid loop between currentRowChanged and selection_changed signals
    with qtbot.wait_signal(view.selectionModel().currentRowChanged, timeout=100, raising=False) as blocker:
        model.selection_changed.emit()
    assert not blocker.signal_triggered


@pytest.mark.parametrize("parent_model_class,parent_returns,expected_result", [
    (None, None, False),
    (SearchProxyModel, None, False),
    (SearchResultsModel, False, False),
    (SearchResultsModel, True, True),
])
def test_extendable_model_can_fetch_more(parent_model_class, parent_returns, expected_result):
    model = ExtendableProxyModel()
    if parent_model_class is not None:
        parent_model = parent_model_class()
        if parent_returns is not None:
            parent_model.canFetchMore = mock.Mock(return_value=parent_returns)
        model.setSourceModel(parent_model)
    assert model.canFetchMore(QModelIndex()) == expected_result


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("parent_model_class", [
    None,
    SearchProxyModel,
    SearchResultsModel,
])
async def test_extendable_model_fetch_more(parent_model_class):
    model = ExtendableProxyModel()
    if parent_model_class is not None:
        parent_model = parent_model_class()
        model.setSourceModel(parent_model)
    model.fetchMore(QModelIndex())


@pytest.mark.parametrize("real_count,is_loading_value,expected_count", [
    (0, False, 0),
    (0, True, 1),
    (0, None, 0),
    (14, False, 14),
    (14, True, 15),
    (14, None, 14),
])
@mock.patch("accwidgets.parameter_selector._model.SearchProxyModel.rowCount")
@mock.patch("accwidgets.parameter_selector._model.SearchResultsModel.is_loading", new_callable=mock.PropertyMock)
def test_extendable_model_row_count(is_loading, rowCount, real_count, is_loading_value, expected_count):
    rowCount.return_value = real_count
    model = ExtendableProxyModel()
    if is_loading_value is not None:
        is_loading.return_value = is_loading_value
        src = SearchResultsModel()
        model.setSourceModel(src)
    assert model.rowCount() == expected_count


@pytest.mark.parametrize("row,role,is_loading_value,expected_res", [
    (-1, Qt.DisplayRole, False, None),
    (-1, Qt.FontRole, False, None),
    (-1, Qt.ToolTipRole, False, None),
    (0, Qt.DisplayRole, False, "dev1"),
    (0, Qt.FontRole, False, None),
    (0, Qt.ToolTipRole, False, None),
    (1, Qt.DisplayRole, False, "dev2"),
    (1, Qt.FontRole, False, None),
    (1, Qt.ToolTipRole, False, None),
    (2, Qt.DisplayRole, False, "dev3"),
    (2, Qt.FontRole, False, None),
    (2, Qt.ToolTipRole, False, None),
    (3, Qt.DisplayRole, False, None),
    (3, Qt.FontRole, False, None),
    (3, Qt.ToolTipRole, False, None),
    (4, Qt.DisplayRole, False, None),
    (4, Qt.FontRole, False, None),
    (4, Qt.ToolTipRole, False, None),
    (-1, Qt.DisplayRole, True, None),
    (-1, Qt.FontRole, True, None),
    (-1, Qt.ToolTipRole, True, None),
    (0, Qt.DisplayRole, True, "dev1"),
    (0, Qt.FontRole, True, None),
    (0, Qt.ToolTipRole, True, None),
    (1, Qt.DisplayRole, True, "dev2"),
    (1, Qt.FontRole, True, None),
    (1, Qt.ToolTipRole, True, None),
    (2, Qt.DisplayRole, True, "dev3"),
    (2, Qt.FontRole, True, None),
    (2, Qt.ToolTipRole, True, None),
    (3, Qt.DisplayRole, True, "Loading more..."),
    (3, Qt.FontRole, True, make_italic_font),
    (3, Qt.ToolTipRole, True, None),
    (4, Qt.DisplayRole, True, None),
    (4, Qt.FontRole, True, None),
    (4, Qt.ToolTipRole, True, None),
    (-1, Qt.DisplayRole, None, None),
    (-1, Qt.FontRole, None, None),
    (-1, Qt.ToolTipRole, None, None),
    (0, Qt.DisplayRole, None, None),
    (0, Qt.FontRole, None, None),
    (0, Qt.ToolTipRole, None, None),
    (1, Qt.DisplayRole, None, None),
    (1, Qt.FontRole, None, None),
    (1, Qt.ToolTipRole, None, None),
    (2, Qt.DisplayRole, None, None),
    (2, Qt.FontRole, None, None),
    (2, Qt.ToolTipRole, None, None),
    (3, Qt.DisplayRole, None, None),
    (3, Qt.FontRole, None, None),
    (3, Qt.ToolTipRole, None, None),
    (4, Qt.DisplayRole, None, None),
    (4, Qt.FontRole, None, None),
    (4, Qt.ToolTipRole, None, None),
])
@mock.patch("accwidgets.parameter_selector._model.SearchResultsModel.is_loading", new_callable=mock.PropertyMock)
def test_extendable_model_data(is_loading, root_model, row, role, expected_res, is_loading_value):
    model = ExtendableProxyModel()
    if is_loading_value is not None:
        is_loading.return_value = is_loading_value
        model.setSourceModel(root_model)
    index = model.createIndex(row, 0)
    if callable(expected_res):
        expected_res = expected_res()
    assert index.data(role) == expected_res


@pytest.mark.parametrize("row,is_loading_value,expected_res", [
    (-1, False, Qt.ItemNeverHasChildren),
    (-1, True, Qt.ItemNeverHasChildren),
    (0, False, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (0, True, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (1, False, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (1, True, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (2, False, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (2, True, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (3, False, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (3, True, Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (4, False, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
    (4, True, Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren),
])
@mock.patch("accwidgets.parameter_selector._model.SearchResultsModel.is_loading", new_callable=mock.PropertyMock)
def test_extendable_model_flags(is_loading, root_model, row, is_loading_value, expected_res):
    model = ExtendableProxyModel()
    if is_loading_value is not None:
        is_loading.return_value = is_loading_value
        model.setSourceModel(root_model)
    index = model.createIndex(row, 0)
    assert index.flags() == expected_res


@pytest.fixture
def get_ccda_mock(monkeypatch):
    # Using monkeypatch. For some reason, @mock.patch does not work here
    import accwidgets.parameter_selector._model as model
    get_ccda_res = mock.MagicMock()
    monkeypatch.setattr(model, "_ccda", get_ccda_res)
    pagination_iter = AsyncMock()
    device_pages = mock.MagicMock()
    get_ccda_res.Device.search = AsyncMock(return_value=device_pages)
    device_pages.__aiter__ = mock.MagicMock(return_value=pagination_iter)
    return pagination_iter, get_ccda_res


def make_dev_iter_side_effect(*returned_devices):
    device_iter = iter(returned_devices)

    def side_effect():
        try:
            return next(device_iter)
        except StopIteration:
            raise StopAsyncIteration

    return side_effect


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("device_name", ["dev1", "dev2"])
async def test_look_up_ccda_calls_api(device_name, get_ccda_mock):
    pagination_iter, get_ccda_res = get_ccda_mock
    pagination_iter.__anext__ = AsyncMock(side_effect=StopAsyncIteration)
    await look_up_ccda(device_name)
    get_ccda_res.Device.search.assert_called_once_with(f'name=="*{device_name}*"')


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
async def test_look_up_ccda_empty(get_ccda_mock):
    pagination_iter, _ = get_ccda_mock
    pagination_iter.__anext__ = AsyncMock(side_effect=StopAsyncIteration)
    results = await look_up_ccda("test_device")
    assert isinstance(results, tuple)
    assert len(results) == 2
    assert results[0] is not None
    assert results[1] == []


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("returned_device_names,expected_first_bach_names", [
    (["dev1"], ["dev1"]),
    (["dev1", "dev2"], ["dev1", "dev2"]),
    (["dev1", "dev2", "dev3", "dev4", "dev5", "dev6"], ["dev1", "dev2", "dev3", "dev4", "dev5"]),
])
@pytest.mark.parametrize("returned_device_props_empty", [True, False])
async def test_look_up_ccda_exhausted_on_non_first_batch(get_ccda_mock, expected_first_bach_names, returned_device_names,
                                                         returned_device_props_empty):
    pagination_iter, _ = get_ccda_mock

    if returned_device_props_empty:
        class_props = []
        expected_props = []
    else:
        field1 = mock.MagicMock()
        field1.name = "field1"
        field2 = mock.MagicMock()
        field2.name = "field2"
        prop1 = mock.MagicMock(data_fields=[field1, field2])
        prop1.name = "prop1"
        prop2 = mock.MagicMock(data_fields=[])
        prop2.name = "prop2"
        class_props = [prop1, prop2]
        expected_props = [("prop1", ["field1", "field2"]), ("prop2", [])]

    returned_devices = []
    for name in returned_device_names:
        class_mock = mock.MagicMock(device_class_properties=class_props)
        device_mock = mock.MagicMock(device_class=AsyncMock(return_value=class_mock))
        device_mock.name = name
        returned_devices.append(device_mock)

    pagination_iter.__anext__ = AsyncMock(side_effect=make_dev_iter_side_effect(*returned_devices))
    results = await look_up_ccda("test_device")
    assert isinstance(results, tuple)
    assert len(results) == 2
    assert results[0] is not None
    assert results[1] == [(name, expected_props) for name in expected_first_bach_names]


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("field_names,expected_field_names", [
    (["field1", "field2", "field3"], ["field1", "field2", "field3"]),
    (["field3", "field1", "field2"], ["field1", "field2", "field3"]),
    (["field3", "field2", "field1"], ["field1", "field2", "field3"]),
    (["field3", "Field2", "field1"], ["Field2", "field1", "field3"]),
])
async def test_look_up_ccda_fields_are_ordered(field_names, expected_field_names, get_ccda_mock):
    pagination_iter, _ = get_ccda_mock

    prop = mock.MagicMock()
    prop.name = "prop1"
    prop.data_fields = []
    for name in field_names:
        field = mock.MagicMock()
        field.name = name
        prop.data_fields.append(field)

    class_mock = mock.MagicMock(device_class_properties=[prop])
    device_mock = mock.MagicMock(device_class=AsyncMock(return_value=class_mock))
    device_mock.name = "test_device"

    pagination_iter.__anext__ = AsyncMock(side_effect=make_dev_iter_side_effect(device_mock))
    results = await look_up_ccda("test_device")
    assert isinstance(results, tuple)
    assert len(results) == 2
    assert results[1] == [("test_device", [("prop1", expected_field_names)])]


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("prop_names,expected_prop_names", [
    (["prop1", "prop2", "prop3"], ["prop1", "prop2", "prop3"]),
    (["prop3", "prop1", "prop2"], ["prop1", "prop2", "prop3"]),
    (["prop3", "prop2", "prop1"], ["prop1", "prop2", "prop3"]),
    (["prop3", "Prop2", "prop1"], ["Prop2", "prop1", "prop3"]),
])
async def test_look_up_ccda_props_are_ordered(prop_names, expected_prop_names, get_ccda_mock):
    pagination_iter, _ = get_ccda_mock

    props = []
    for name in prop_names:
        prop = mock.MagicMock(data_fields=[])
        prop.name = name
        props.append(prop)

    class_mock = mock.MagicMock(device_class_properties=props)
    device_mock = mock.MagicMock(device_class=AsyncMock(return_value=class_mock))
    device_mock.name = "test_device"

    pagination_iter.__anext__ = AsyncMock(side_effect=make_dev_iter_side_effect(device_mock))
    results = await look_up_ccda("test_device")
    assert isinstance(results, tuple)
    assert len(results) == 2
    assert results[1] == [("test_device", [(name, []) for name in expected_prop_names])]


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("device_names,expected_device_batches", [
    (["dev1"], [["dev1"]]),
    (["dev1", "dev2", "dev3", "dev4", "dev5"], [["dev1", "dev2", "dev3", "dev4", "dev5"]]),
    (["dev1", "dev2", "dev3", "dev4", "dev5", "dev6"], [["dev1", "dev2", "dev3", "dev4", "dev5"], ["dev6"]]),
    (["dev1", "dev2", "dev3", "dev4", "dev5", "dev6", "dev7", "dev8", "dev9", "dev10", "dev11"],
     [["dev1", "dev2", "dev3", "dev4", "dev5"], ["dev6", "dev7", "dev8", "dev9", "dev10"],
      ["dev11"]]),
])
async def test_look_up_ccda_iter_is_yieldable(get_ccda_mock, device_names, expected_device_batches):
    pagination_iter, _ = get_ccda_mock

    returned_devices = []
    for name in device_names:
        class_mock = mock.MagicMock(device_class_properties=[])
        device_mock = mock.MagicMock(device_class=AsyncMock(return_value=class_mock))
        device_mock.name = name
        returned_devices.append(device_mock)

    pagination_iter.__anext__ = AsyncMock(side_effect=make_dev_iter_side_effect(*returned_devices))
    results = await look_up_ccda("test_device")
    assert isinstance(results, tuple)
    assert len(results) == 2
    results_iter = iter(expected_device_batches)
    assert results[1] == [(name, []) for name in next(results_iter)]

    try:
        next_expected_batch = next(results_iter)
    except StopIteration:
        next_results = await results[0].__anext__()
        assert next_results == []
    else:
        next_results = await results[0].__anext__()
        assert next_results == [(name, []) for name in next_expected_batch]


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("error_type", [TypeError, ValueError])
async def test_look_up_ccda_does_not_catch_api_exceptions(get_ccda_mock, error_type):
    pagination_iter, _ = get_ccda_mock

    pagination_iter.__anext__ = AsyncMock(side_effect=error_type)
    with pytest.raises(error_type):
        await look_up_ccda("test_device")


def test_get_ccda_is_singleton():
    obj1 = get_ccda()
    obj2 = get_ccda()
    assert obj1 is obj2
