import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt, QVariant
from qtpy.QtWidgets import QListView
from accwidgets.parameter_selector._model import get_ccda, SearchResultsModel, SearchProxyModel


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.fixture(scope="function")
async def root_model():
    root = SearchResultsModel()
    data = [
        ("dev1", [("prop1", [])]),
        ("dev2", [("prop2", ["field2"])]),
        ("dev3", [("prop3.1", ["field3.1.1"]), ("prop3.2", ["field3.2.1", "field3.2.2"])]),
    ]
    root.set_data(data)
    return root


@pytest.mark.asyncio  # Needed to run underlying event loop, otherwise internal "create_task" call will fail
@pytest.mark.parametrize("data", [
    [],
    [("dev", [])],
])
async def test_root_model_set_data_resets_model(qtbot: QtBot, data):
    model = SearchResultsModel()
    with qtbot.wait_signal(model.modelReset):
        model.set_data(data)


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


@pytest.mark.skip
def test_proxy_model_row_count_from_leaf():
    pass


@pytest.mark.skip
def test_proxy_model_row_count_from_first_child():
    pass


@pytest.mark.skip
def test_proxy_model_row_count_from_second_child():
    pass


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


def test_get_ccda_is_singleton():
    obj1 = get_ccda()
    obj2 = get_ccda()
    assert obj1 is obj2
