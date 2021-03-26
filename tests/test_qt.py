import pytest
from pytestqt.qtbot import QtBot
from typing import Optional, cast, Type
from unittest import mock
from qtpy.QtCore import Qt, QVariant, QAbstractListModel, QObject, QPersistentModelIndex, QLocale
from qtpy.QtWidgets import QDialogButtonBox, QStyleOptionViewItem, QComboBox, QWidget
from PyQt5.QtTest import QAbstractItemModelTester
from accwidgets.qt import (AbstractListModel, AbstractTableModel, AbstractTableDialog,
                           PersistentEditorTableView, BooleanPropertyColumnDelegate, BooleanButton,
                           AbstractComboBoxColumnDelegate, _STYLED_ITEM_DELEGATE_INDEX, exec_app_interruptable)


@pytest.fixture
def abstract_table_dialog_impl():
    with mock.patch.multiple(AbstractTableDialog, __abstractmethods__=set()):
        yield AbstractTableDialog


@pytest.fixture
def concrete_list_model_impl() -> Type[QAbstractListModel]:
    class TestListModel(AbstractListModel, QAbstractListModel):

        def __init__(self, data, parent: Optional[QObject] = None):
            AbstractListModel.__init__(self, data)
            QAbstractListModel.__init__(self, parent)

        def create_row(self):
            return 1

    return TestListModel


def get_table_model_class(column_count: int = 1):

    class TestTableModel(AbstractTableModel):

        def columnCount(self, parent=None, *args, **kwargs):
            return column_count

        def column_name(self, section: int) -> str:
            return "Column"

        def create_row(self):
            return 1

        def set_cell_data(self, *args, **kwargs):
            return True

        def get_cell_data(self, *args, **kwargs):
            return 1
    return TestTableModel


@pytest.fixture
def concrete_table_model_impl():
    return get_table_model_class()


@pytest.mark.parametrize("delegate_row,delegate_col", [
    (None, None),
    (0, None),
    (1, None),
    (None, 0),
    (None, 1),
])
@pytest.mark.parametrize("preserve_rows,preserve_cols,,expected_editors", [
    ([], [], [[False, False], [False, False]]),
    ([0], [], [[True, True], [False, False]]),
    ([1], [], [[False, False], [True, True]]),
    ([0, 1], [], [[True, True], [True, True]]),
    ([], [0], [[True, False], [True, False]]),
    ([], [1], [[False, True], [False, True]]),
    ([], [0, 1], [[True, True], [True, True]]),
    ([0], [0], [[True, True], [True, False]]),
    ([0], [1], [[True, True], [False, True]]),
    ([0], [0, 1], [[True, True], [True, True]]),
    ([1], [0], [[True, False], [True, True]]),
    ([1], [1], [[False, True], [True, True]]),
    ([1], [0, 1], [[True, True], [True, True]]),
    ([0, 1], [0], [[True, True], [True, True]]),
    ([0, 1], [1], [[True, True], [True, True]]),
    ([0, 1], [0, 1], [[True, True], [True, True]]),
])
def test_persistent_table_updates_editors_on_new_delegate(qtbot: QtBot, preserve_rows, preserve_cols, delegate_row, delegate_col, expected_editors):

    def assign_new_delegate(widget: PersistentEditorTableView):
        if delegate_row is None and delegate_col is None:
            widget.setItemDelegate(BooleanPropertyColumnDelegate())
        elif delegate_row is not None:
            widget.setItemDelegateForRow(delegate_row, BooleanPropertyColumnDelegate())
        else:
            widget.setItemDelegateForColumn(delegate_col, BooleanPropertyColumnDelegate())

    def set_persistent_editors(widget: PersistentEditorTableView):
        for i in preserve_rows:
            widget.set_persistent_editor_for_row(i)
        for i in preserve_cols:
            widget.set_persistent_editor_for_column(i)

    widget = PersistentEditorTableView()
    qtbot.add_widget(widget)
    model_class = get_table_model_class(2)
    model = model_class([0, 1])
    widget.setModel(model)
    index00 = model.createIndex(0, 0)
    index01 = model.createIndex(0, 1)
    index10 = model.createIndex(1, 0)
    index11 = model.createIndex(1, 1)
    assert not widget.isPersistentEditorOpen(index00)
    assert not widget.isPersistentEditorOpen(index01)
    assert not widget.isPersistentEditorOpen(index10)
    assert not widget.isPersistentEditorOpen(index11)
    # Check that regular implementation actually closes the persistent editors
    if expected_editors[0][0]:
        widget.openPersistentEditor(index00)
    if expected_editors[0][1]:
        widget.openPersistentEditor(index01)
    if expected_editors[1][0]:
        widget.openPersistentEditor(index10)
    if expected_editors[1][1]:
        widget.openPersistentEditor(index11)
    assert widget.isPersistentEditorOpen(index00) == expected_editors[0][0]
    assert widget.isPersistentEditorOpen(index01) == expected_editors[0][1]
    assert widget.isPersistentEditorOpen(index10) == expected_editors[1][0]
    assert widget.isPersistentEditorOpen(index11) == expected_editors[1][1]
    assign_new_delegate(widget)
    assert not widget.isPersistentEditorOpen(index00)
    assert not widget.isPersistentEditorOpen(index01)
    assert not widget.isPersistentEditorOpen(index10)
    assert not widget.isPersistentEditorOpen(index11)
    # Check that our implementation preserves persistence
    set_persistent_editors(widget)
    assert widget.isPersistentEditorOpen(index00) == expected_editors[0][0]
    assert widget.isPersistentEditorOpen(index01) == expected_editors[0][1]
    assert widget.isPersistentEditorOpen(index10) == expected_editors[1][0]
    assert widget.isPersistentEditorOpen(index11) == expected_editors[1][1]
    assign_new_delegate(widget)
    assert widget.isPersistentEditorOpen(index00) == expected_editors[0][0]
    assert widget.isPersistentEditorOpen(index01) == expected_editors[0][1]
    assert widget.isPersistentEditorOpen(index10) == expected_editors[1][0]
    assert widget.isPersistentEditorOpen(index11) == expected_editors[1][1]


def test_persistent_table_updates_editors_on_new_model(qtbot: QtBot):

    widget = PersistentEditorTableView()
    qtbot.add_widget(widget)
    model_class = get_table_model_class(2)
    editable_flag = Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsSelectable
    not_editable_flag = Qt.ItemIsSelectable

    class FlagModel(model_class):  # type: ignore  # mypy does not like this subclassing

        def __init__(self, data):
            super().__init__(data)
            self.dummy_flags = [
                [not_editable_flag, editable_flag],
                [editable_flag, not_editable_flag],
            ]

        def flags(self, index):
            return self.dummy_flags[index.row()][index.column()]

    initial_model = FlagModel([0, 1])
    widget.setModel(initial_model)
    index00 = initial_model.createIndex(0, 0)
    index01 = initial_model.createIndex(0, 1)
    index10 = initial_model.createIndex(1, 0)
    index11 = initial_model.createIndex(1, 1)
    assert not widget.isPersistentEditorOpen(index00)
    assert not widget.isPersistentEditorOpen(index01)
    assert not widget.isPersistentEditorOpen(index10)
    assert not widget.isPersistentEditorOpen(index11)
    widget.set_persistent_editor_for_column(0)
    widget.set_persistent_editor_for_column(1)
    assert not widget.isPersistentEditorOpen(index00)
    assert widget.isPersistentEditorOpen(index01)
    assert widget.isPersistentEditorOpen(index10)
    assert not widget.isPersistentEditorOpen(index11)
    # Modify model and see when table detects the change
    initial_model.dummy_flags[0][0] = editable_flag
    assert not widget.isPersistentEditorOpen(index00)
    initial_model.dataChanged.emit(index00, index00, [Qt.DisplayRole])
    assert widget.isPersistentEditorOpen(index00)

    new_model = FlagModel([0, 1])
    new_model.dummy_flags = [
        [editable_flag, not_editable_flag],
        [not_editable_flag, editable_flag],
    ]
    widget.setModel(new_model)
    init_index00 = index00
    index00 = new_model.createIndex(0, 0)
    index01 = new_model.createIndex(0, 1)
    index10 = new_model.createIndex(1, 0)
    index11 = new_model.createIndex(1, 1)
    assert widget.isPersistentEditorOpen(index00)
    assert not widget.isPersistentEditorOpen(index01)
    assert not widget.isPersistentEditorOpen(index10)
    assert widget.isPersistentEditorOpen(index11)

    # Check that new model can affect persistence
    new_model.dummy_flags[0][0] = not_editable_flag
    assert widget.isPersistentEditorOpen(index00)
    new_model.dataChanged.emit(index00, index00, [Qt.DisplayRole])
    assert not widget.isPersistentEditorOpen(index00)

    # Check that old model does not affect the persistence
    initial_model.dummy_flags[0][0] = editable_flag
    assert not widget.isPersistentEditorOpen(index00)
    initial_model.dataChanged.emit(init_index00, init_index00, [Qt.DisplayRole])
    assert not widget.isPersistentEditorOpen(index00)


def test_persistent_table_no_editors_with_no_model(qtbot: QtBot):
    widget = PersistentEditorTableView()
    qtbot.add_widget(widget)
    assert widget.model() is None
    model_class = get_table_model_class(2)
    model = model_class([0])
    index00 = model.createIndex(0, 0)
    assert not widget.isPersistentEditorOpen(index00)
    widget.set_persistent_editor_for_column(0)
    assert not widget.isPersistentEditorOpen(index00)


def test_persistent_table_ignores_exotic_roles(qtbot: QtBot):
    widget = PersistentEditorTableView()
    qtbot.add_widget(widget)
    model_class = get_table_model_class(2)

    editable_flag = Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsSelectable
    not_editable_flag = Qt.ItemIsSelectable

    class FlagModel(model_class):  # type: ignore  # mypy does not like this subclassing

        def __init__(self, data):
            super().__init__(data)
            self.dummy_flags = [
                [not_editable_flag, editable_flag],
                [editable_flag, not_editable_flag],
            ]

        def flags(self, index):
            return self.dummy_flags[index.row()][index.column()]

    model = FlagModel([0, 1])
    widget.setModel(model)
    index00 = model.createIndex(0, 0)
    index01 = model.createIndex(0, 1)
    index10 = model.createIndex(1, 0)
    index11 = model.createIndex(1, 1)
    assert not widget.isPersistentEditorOpen(index00)
    assert not widget.isPersistentEditorOpen(index01)
    assert not widget.isPersistentEditorOpen(index10)
    assert not widget.isPersistentEditorOpen(index11)
    widget.set_persistent_editor_for_column(0)
    widget.set_persistent_editor_for_column(1)
    assert not widget.isPersistentEditorOpen(index00)
    assert widget.isPersistentEditorOpen(index01)
    assert widget.isPersistentEditorOpen(index10)
    assert not widget.isPersistentEditorOpen(index11)
    # Modify model but make sure exotic flag does not affect it
    model.dummy_flags[0][0] = editable_flag
    assert not widget.isPersistentEditorOpen(index00)
    model.dataChanged.emit(index00, index00, [Qt.ToolTipRole])
    assert not widget.isPersistentEditorOpen(index00)


@pytest.mark.parametrize("superclass,displays_warning", [
    (QAbstractListModel, False),
    (QObject, True),
    (object, True),
])
def test_abstract_list_model_warns_on_bad_base_class(superclass, displays_warning, recwarn):
    class TestClass(AbstractListModel, superclass):
        def __init__(self):
            AbstractListModel.__init__(self, data=[1, 2, 3])
            superclass.__init__(self)

        def create_row(self):
            return 1

    import warnings
    warnings.filterwarnings("default", category=RuntimeWarning, message="AbstractListModel must be subclassed together with QAbstractItemModel "
                                                                        "or its derivative, otherwise it may break if assumed API is not present.")
    TestClass()
    if displays_warning:
        assert len(recwarn) == 1
    else:
        assert len(recwarn) == 0


def test_concrete_list_model_common(concrete_list_model_impl):
    model = concrete_list_model_impl([1, 2, 3])
    _ = QAbstractItemModelTester(model)


@pytest.mark.parametrize("data", [
    [],
    [1],
    [1, 2, 3],
])
def test_abstract_list_model_row_count(concrete_list_model_impl, data):
    assert concrete_list_model_impl(data).rowCount() == len(data)


def test_abstract_list_model_append_row(concrete_list_model_impl):
    initial_data = [1, 2, 3]
    model = concrete_list_model_impl([*initial_data])
    assert model.raw_data == initial_data
    with mock.patch.object(model, "create_row", return_value=99):
        model.append_row()
    assert model.raw_data == [*initial_data, 99]


def test_abstract_list_model_remove_row(concrete_list_model_impl):
    initial_data = [1, 2, 3]
    model = concrete_list_model_impl([*initial_data])
    assert model.raw_data == initial_data
    model.remove_row_at_index(model.createIndex(len(initial_data) - 1, 0))
    expected_data = initial_data[:-1]
    assert model.raw_data == expected_data
    model.remove_row_at_index(model.createIndex(0, 0))
    expected_data.pop(0)
    assert model.raw_data == expected_data


@pytest.mark.parametrize("action_type", [
    AbstractListModel.ChangeType.UPDATE_ITEM,
    AbstractListModel.ChangeType.ADD_ROW,
    AbstractListModel.ChangeType.REMOVE_ROW,
])
@pytest.mark.parametrize("start_row", [-1, 0, 1])
@pytest.mark.parametrize("start_col", [-1, 0, 1])
@pytest.mark.parametrize("end_row", [-1, 0, 1])
@pytest.mark.parametrize("end_col", [-1, 0, 1])
def test_abstract_list_model_notify_data_emits_signal(qtbot: QtBot, concrete_list_model_impl, action_type, start_col, start_row, end_col, end_row):
    model = concrete_list_model_impl([])
    start = model.createIndex(start_row, start_col)
    end = model.createIndex(end_row, end_col)
    with qtbot.wait_signal(model.dataChanged) as blocker:
        model.notify_change(start=start, end=end, action_type=action_type)
    assert len(blocker.args) >= 2
    actual_start = blocker.args[0]
    actual_end = blocker.args[1]
    assert actual_start.row() == start_row
    assert actual_start.column() == start_col
    assert actual_end.row() == end_row
    assert actual_end.column() == end_col


@pytest.mark.parametrize("row,col,valid_idx,role,result", [
    (0, 0, True, Qt.DisplayRole, 99),
    (0, 0, True, Qt.EditRole, 99),
    (0, 0, True, Qt.ToolTipRole, QVariant()),
    (0, 1, True, Qt.DisplayRole, 99),  # Col should not matter here, it's 1D list
    (0, 1, True, Qt.EditRole, 99),
    (0, 1, True, Qt.ToolTipRole, QVariant()),
    (1, 0, True, Qt.DisplayRole, QVariant()),
    (1, 0, True, Qt.EditRole, QVariant()),
    (1, 0, True, Qt.ToolTipRole, QVariant()),
    (-1, 0, False, Qt.DisplayRole, QVariant()),
    (-1, 0, False, Qt.EditRole, QVariant()),
    (-1, 0, False, Qt.ToolTipRole, QVariant()),
    (0, -1, False, Qt.DisplayRole, QVariant()),
    (0, -1, False, Qt.EditRole, QVariant()),
    (0, -1, False, Qt.ToolTipRole, QVariant()),
])
def test_abstract_list_model_data_ignores_wrong_input(concrete_list_model_impl, row, col, valid_idx, role, result):
    model = concrete_list_model_impl([99])
    index = model.createIndex(row, col)
    assert index.isValid() == valid_idx
    assert model.data(index, role) == result


@pytest.mark.parametrize("row,col,valid_idx,role,should_succeed", [
    (0, 0, True, Qt.EditRole, True),
    (-1, 0, False, Qt.EditRole, False),
    (0, -1, False, Qt.EditRole, False),
    (-1, -1, False, Qt.EditRole, False),
    (1, 0, True, Qt.EditRole, False),
    (0, 1, True, Qt.EditRole, True),
    (1, 1, True, Qt.EditRole, False),
    (0, 0, True, Qt.DisplayRole, False),
    (-1, 0, False, Qt.DisplayRole, False),
    (0, -1, False, Qt.DisplayRole, False),
    (-1, -1, False, Qt.DisplayRole, False),
    (1, 0, True, Qt.DisplayRole, False),
    (0, 1, True, Qt.DisplayRole, False),
    (1, 1, True, Qt.DisplayRole, False),
    (0, 0, True, Qt.ToolTipRole, False),
    (-1, 0, False, Qt.ToolTipRole, False),
    (0, -1, False, Qt.ToolTipRole, False),
    (-1, -1, False, Qt.ToolTipRole, False),
    (1, 0, True, Qt.ToolTipRole, False),
    (0, 1, True, Qt.ToolTipRole, False),
    (1, 1, True, Qt.ToolTipRole, False),
])
def test_abstract_list_model_set_data_on_proper_index(concrete_list_model_impl, row, col, role, valid_idx, should_succeed):
    model = concrete_list_model_impl([99])
    index = model.createIndex(row, col)
    assert index.isValid() == valid_idx
    with mock.patch.object(model, "notify_change") as notify_change:
        actual_result = model.setData(index, 101, role)
        if should_succeed:
            notify_change.assert_called_once_with(start=index,
                                                  end=index,
                                                  action_type=AbstractListModel.ChangeType.UPDATE_ITEM)
            assert actual_result is True
            assert model.raw_data == [101]
        else:
            notify_change.assert_not_called()
            assert actual_result is False
            assert model.raw_data == [99]


def test_abstract_list_model_raw_data(concrete_list_model_impl):
    assert concrete_list_model_impl([1, 2, 3]).raw_data == [1, 2, 3]


def test_concrete_table_model_common(concrete_table_model_impl):
    model = concrete_table_model_impl([1, 2, 3])
    _ = QAbstractItemModelTester(model)


@pytest.mark.parametrize("action_type,expected_end_col", [
    (AbstractTableModel.ChangeType.ADD_ROW, 1),
    (AbstractTableModel.ChangeType.UPDATE_ITEM, 0),
    (AbstractTableModel.ChangeType.REMOVE_ROW, 0),
])
def test_abstract_table_model_notify_change_swaps_indexes(qtbot: QtBot, concrete_table_model_impl, action_type, expected_end_col):
    model = concrete_table_model_impl([[0, 1], [2, 3]])
    with mock.patch.object(model, "columnCount", return_value=2):
        start = model.createIndex(0, 0)
        end = model.createIndex(0, 0)
        with qtbot.wait_signal(model.dataChanged) as blocker:
            model.notify_change(start=start, end=end, action_type=action_type)
        assert len(blocker.args) >= 2
        actual_start = blocker.args[0]
        actual_end = blocker.args[1]
        assert actual_start.row() == start.row()
        assert actual_start.column() == start.column()
        assert actual_end.row() == end.row()
        assert actual_end.column() == expected_end_col


@pytest.mark.parametrize("row", [-1, 0, 1, 2])
@pytest.mark.parametrize("col", [-1, 0, 1, 2])
def test_abstract_table_model_flags(concrete_table_model_impl, row, col):
    model = concrete_table_model_impl([])
    index = model.createIndex(row, col)
    assert model.flags(index) == Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable


def test_abstract_table_model_raw_data(concrete_table_model_impl):
    assert concrete_table_model_impl([(1, 1), (2, 2), (3, 3)]).raw_data == [(1, 1), (2, 2), (3, 3)]


@pytest.mark.parametrize("role,orientation,section,expected_label", [
    (Qt.DisplayRole, Qt.Horizontal, 0, "real_section_name"),
    (Qt.DisplayRole, Qt.Horizontal, 1, ""),
    (Qt.DisplayRole, Qt.Vertical, 0, " 1 "),
    (Qt.DisplayRole, Qt.Vertical, 1, " 2 "),
    (Qt.DisplayRole, Qt.Vertical, 2, " 3 "),
    (Qt.DisplayRole, Qt.Vertical, 3, ""),
    (Qt.EditRole, Qt.Horizontal, 0, None),
    (Qt.EditRole, Qt.Horizontal, 1, None),
    (Qt.EditRole, Qt.Vertical, 0, None),
    (Qt.EditRole, Qt.Vertical, 1, None),
    (Qt.EditRole, Qt.Vertical, 2, None),
    (Qt.EditRole, Qt.Vertical, 3, None),
    (Qt.ToolTipRole, Qt.Horizontal, 0, None),
    (Qt.ToolTipRole, Qt.Horizontal, 1, None),
    (Qt.ToolTipRole, Qt.Vertical, 0, None),
    (Qt.ToolTipRole, Qt.Vertical, 1, None),
    (Qt.ToolTipRole, Qt.Vertical, 2, None),
    (Qt.ToolTipRole, Qt.Vertical, 3, None),
])
def test_abstract_table_model_header_data(concrete_table_model_impl, role, orientation, section, expected_label):
    model = concrete_table_model_impl([1, 2, 3])
    with mock.patch.object(model, "column_name", return_value="real_section_name"):
        with mock.patch.object(model, "columnCount", return_value=1):
            actual_label = model.headerData(section, orientation, role)
            assert actual_label == expected_label


@pytest.mark.parametrize("row,column,role,expected_success", [
    (0, 0, Qt.DisplayRole, True),
    (0, 1, Qt.DisplayRole, True),
    (-1, 0, Qt.DisplayRole, False),
    (4, 0, Qt.DisplayRole, False),
    (0, 0, Qt.EditRole, True),
    (0, 1, Qt.EditRole, True),
    (-1, 0, Qt.EditRole, False),
    (4, 0, Qt.EditRole, False),
    (0, 0, Qt.ToolTipRole, False),
    (0, 1, Qt.ToolTipRole, False),
    (-1, 0, Qt.ToolTipRole, False),
    (4, 0, Qt.ToolTipRole, False),
])
def test_abstract_table_model_data(concrete_table_model_impl, row, column, role, expected_success):
    data = [1, 2, 3]
    model = concrete_table_model_impl(data)
    with mock.patch.object(model, "columnCount", return_value=1):
        with mock.patch.object(model, "get_cell_data", return_value="mocked_return") as get_cell_data:
            index = model.createIndex(row, column)
            actual_data = model.data(index, role)
            if expected_success:
                get_cell_data.assert_called_once_with(index=index, row=data[row])
                assert actual_data == "mocked_return"
            else:
                get_cell_data.assert_not_called()
                assert actual_data == QVariant()


@pytest.mark.parametrize("register_change", [True, False])
@pytest.mark.parametrize("row,column,role,expected_setter_eval", [
    (0, 0, Qt.DisplayRole, False),
    (0, 1, Qt.DisplayRole, False),
    (-1, 0, Qt.DisplayRole, False),
    (4, 0, Qt.DisplayRole, False),
    (0, 0, Qt.EditRole, True),
    (0, 1, Qt.EditRole, True),
    (-1, 0, Qt.EditRole, False),
    (0, 0, Qt.ToolTipRole, False),
    (0, 1, Qt.ToolTipRole, False),
    (-1, 0, Qt.ToolTipRole, False),
])
def test_abstract_table_model_set_data(concrete_table_model_impl, row, column, role, expected_setter_eval, register_change):
    data = [1, 2, 3]
    model = concrete_table_model_impl(data)
    with mock.patch.object(model, "columnCount", return_value=1):
        with mock.patch.object(model, "notify_change") as notify_change:
            with mock.patch.object(model, "set_cell_data", return_value=register_change) as set_cell_data:
                index = model.createIndex(row, column)
                actual_success = model.setData(index, "test_val", role)
                expected_success = expected_setter_eval and register_change
                assert actual_success == expected_success
                if expected_setter_eval:
                    set_cell_data.assert_called_once_with(index=index, row=data[row], value="test_val")
                else:
                    set_cell_data.assert_not_called()
                if expected_success:
                    notify_change.assert_called_once_with(start=index,
                                                          end=index,
                                                          action_type=AbstractListModel.ChangeType.UPDATE_ITEM)
                else:
                    notify_change.assert_not_called()


@mock.patch("qtpy.QtWidgets.QMessageBox.warning")
def test_abstract_table_dialog_warning_on_invalid_data(mocked_warning, abstract_table_dialog_impl, concrete_table_model_impl, qtbot: QtBot):
    model = concrete_table_model_impl([])
    dialog = abstract_table_dialog_impl(table_model=model)
    qtbot.add_widget(dialog)
    dialog.show()

    with mock.patch.object(dialog.table.model(), "validate", side_effect=ValueError("test")):
        dialog.buttons.button(QDialogButtonBox.Ok).click()
        mocked_warning.assert_called_with(dialog, "Invalid data", "test")


@pytest.mark.parametrize("exc_type", [
    TypeError,
    Warning,
    RuntimeWarning,
    RuntimeError,
    AttributeError,
    EnvironmentError,
    ImportError,
    ModuleNotFoundError,
    SyntaxError,
    IndexError,
    OSError,
    ZeroDivisionError,
])
@mock.patch("qtpy.QtWidgets.QMessageBox.warning")
def test_abstract_table_dialog_crashes_on_invalid_exception_in_validate(mocked_warning, abstract_table_dialog_impl, concrete_table_model_impl, exc_type, qtbot: QtBot):
    model = concrete_table_model_impl([])
    with mock.patch.object(model, "columnCount", return_value=1):
        dialog = abstract_table_dialog_impl(table_model=model)
        qtbot.add_widget(dialog)
        dialog.show()

        with mock.patch.object(dialog.table.model(), "validate", side_effect=exc_type("test")):
            dialog.buttons.button(QDialogButtonBox.Ok).click()
            mocked_warning.assert_called_with(dialog, "Unexpected error", "test")


def test_abstract_table_dialog_disabled_buttons(qtbot: QtBot, abstract_table_dialog_impl, concrete_table_model_impl):
    data = [1, 2, 3]
    model = concrete_table_model_impl([*data])
    dialog = abstract_table_dialog_impl(table_model=model)
    qtbot.add_widget(dialog)
    dialog.show()
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False
    assert model.rowCount() == len(data)
    dialog.add_btn.click()
    assert model.rowCount() == (len(data) + 1)
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False
    for i in reversed(range(len(data) + 1)):
        assert model.rowCount() == (i + 1)
        dialog.table.selectRow(i)
        assert dialog.add_btn.isEnabled() is True
        assert dialog.remove_btn.isEnabled() is True
        dialog.remove_btn.click()
        assert model.rowCount() == i
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False


@pytest.mark.parametrize("button,should_call", [
    (QDialogButtonBox.Ok, True),
    (QDialogButtonBox.Cancel, False),
])
def test_abstract_table_dialog_before_save(qtbot: QtBot, abstract_table_dialog_impl, concrete_table_model_impl, button, should_call):
    model = concrete_table_model_impl([1, 2, 3])
    dialog = abstract_table_dialog_impl(table_model=model)
    qtbot.add_widget(dialog)
    with mock.patch.object(dialog, "on_save") as on_save:
        dialog.show()
        on_save.assert_not_called()
        dialog.buttons.button(button).click()
        if should_call:
            on_save.assert_called_once()
        else:
            on_save.assert_not_called()


def test_abstract_table_dialog_append(qtbot: QtBot, abstract_table_dialog_impl, concrete_table_model_impl):
    initial_data = [1, 2, 3]
    model = concrete_table_model_impl([*initial_data])
    dialog = abstract_table_dialog_impl(table_model=model)
    qtbot.add_widget(dialog)
    dialog.show()
    assert model.raw_data == initial_data
    with mock.patch.object(model, "create_row", return_value=99):
        dialog.add_btn.click()
    assert model.raw_data == [*initial_data, 99]


def test_abstract_table_dialog_remove(qtbot: QtBot, abstract_table_dialog_impl, concrete_table_model_impl):
    initial_data = [1, 2, 3]
    model = concrete_table_model_impl([*initial_data])
    dialog = abstract_table_dialog_impl(table_model=model)
    qtbot.add_widget(dialog)
    dialog.show()
    assert model.raw_data == initial_data
    dialog.table.selectRow(len(initial_data) - 1)
    dialog.remove_btn.click()
    expected_data = initial_data[:-1]
    assert model.raw_data == expected_data
    dialog.table.selectRow(0)
    dialog.remove_btn.click()
    expected_data.pop(0)
    assert model.raw_data == expected_data


@pytest.fixture
def combobox_delegate_impl():
    class TestDelegate(AbstractComboBoxColumnDelegate):
        def configure_editor(self, *args, **kwargs):
            pass
    return TestDelegate


def test_combobox_delegate_create_editor(qtbot, concrete_list_model_impl, combobox_delegate_impl):
    model = concrete_list_model_impl([])
    delegate = combobox_delegate_impl()

    def configure(editor, _):
        editor.addItems(["One", "Two"])

    widget = QWidget()
    qtbot.add_widget(widget)

    with mock.patch.object(delegate, "configure_editor", side_effect=configure):
        editor = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(3, 5))
        assert isinstance(editor, QComboBox)
        index = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX)
        assert isinstance(index, QPersistentModelIndex)
        assert index.row() == 3
        assert index.column() == 5
        assert cast(QComboBox, editor).count() == 2
        assert cast(QComboBox, editor).itemText(0) == "One"
        assert cast(QComboBox, editor).itemText(1) == "Two"


@pytest.mark.parametrize("row, expected_text", [
    (0, "UNDEFINED"),
    (1, "One"),
    (2, "Two"),
])
def test_combobox_delegate_set_editor_data_succeeds(qtbot, concrete_list_model_impl, combobox_delegate_impl, row, expected_text):
    model = concrete_list_model_impl([0, 1, 2])
    delegate = combobox_delegate_impl()

    def configure(editor: QComboBox, _):
        editor.addItem("One", 1)
        editor.addItem("Two", 2)
        editor.setEditable(True)
        editor.setEditText("UNDEFINED")

    widget = QWidget()
    qtbot.add_widget(widget)

    with mock.patch.object(delegate, "configure_editor", side_effect=configure):
        editor = cast(QComboBox, delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(0, 0)))
    assert editor.currentText() == "UNDEFINED"
    delegate.setEditorData(editor, model.createIndex(row, 0))
    assert editor.currentText() == expected_text


@pytest.mark.parametrize("chosen_idx,expected_raw_data", [
    (0, [1]),
    (1, [2]),
])
def test_combobox_delegate_set_model_data(qtbot, concrete_list_model_impl, combobox_delegate_impl, chosen_idx, expected_raw_data):
    model = concrete_list_model_impl([0])
    delegate = combobox_delegate_impl()

    def configure(editor: QComboBox, _):
        editor.addItem("One", 1)
        editor.addItem("Two", 2)
        editor.setEditable(True)
        editor.setEditText("UNDEFINED")

    widget = QWidget()
    qtbot.add_widget(widget)

    with mock.patch.object(delegate, "configure_editor", side_effect=configure):
        editor = cast(QComboBox, delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(0, 0)))
    assert editor.currentText() == "UNDEFINED"
    assert model.raw_data == [0]
    editor.setCurrentIndex(chosen_idx)
    editor.activated.emit(editor.currentIndex())  # Manually emitting, as activated is designed to fire only on user interaction
    assert model.raw_data == expected_raw_data


def test_boolean_button_value_getter(qtbot: QtBot):
    widget = BooleanButton()
    qtbot.add_widget(widget)
    assert widget.value is False
    assert widget._checkbox.isChecked() is False
    with qtbot.wait_signal(widget.value_changed, timeout=100, raising=False) as blocker:
        widget.value = True
    assert blocker.signal_triggered is False
    with qtbot.wait_signal(widget.value_changed, timeout=100, raising=False) as blocker:
        assert widget.value is True
    assert blocker.signal_triggered is False
    assert widget._checkbox.isChecked() is True
    with qtbot.wait_signal(widget.value_changed, timeout=100, raising=False) as blocker:
        widget.value = False
    assert blocker.signal_triggered is False
    assert widget.value is False
    assert widget._checkbox.isChecked() is False


def test_boolean_button_toggle(qtbot: QtBot):
    widget = BooleanButton()
    qtbot.add_widget(widget)
    assert widget.value is False
    assert widget._checkbox.isChecked() is False
    with qtbot.wait_signal(widget.value_changed) as blocker:
        widget.click()
    assert blocker.signal_triggered is True
    assert widget._checkbox.isChecked() is True
    assert widget.value is True
    with qtbot.wait_signal(widget.value_changed) as blocker:
        widget.click()
    assert blocker.signal_triggered is True
    assert widget._checkbox.isChecked() is False
    assert widget.value is False


def test_boolean_delegate_create_editor_has_index(qtbot, concrete_list_model_impl):
    model = concrete_list_model_impl([True, False])
    delegate = BooleanPropertyColumnDelegate()

    widget = QWidget()
    qtbot.add_widget(widget)

    editor = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(3, 5))
    assert isinstance(editor, BooleanButton)
    index = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX)
    assert isinstance(index, QPersistentModelIndex)
    assert index.row() == 3
    assert index.column() == 5


def test_boolean_delegate_set_editor_data_succeeds(qtbot, concrete_list_model_impl):
    model = concrete_list_model_impl([True, False])
    delegate = BooleanPropertyColumnDelegate()

    widget = QWidget()
    qtbot.add_widget(widget)

    editor: BooleanButton = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(0, 0))
    delegate.setEditorData(editor, model.createIndex(0, 0))
    assert editor.value is True
    index = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX)
    assert isinstance(index, QPersistentModelIndex)
    assert index.row() == 0
    assert index.column() == 0

    delegate.setEditorData(editor, model.createIndex(1, 0))
    assert editor.value is False
    index = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX)
    assert isinstance(index, QPersistentModelIndex)
    assert index.row() == 1
    assert index.column() == 0


def test_boolean_delegate_reacts_to_button_press(qtbot, concrete_list_model_impl):
    model = concrete_list_model_impl([True, False])
    delegate = BooleanPropertyColumnDelegate()

    widget = QWidget()
    qtbot.add_widget(widget)

    editor: BooleanButton = delegate.createEditor(widget, QStyleOptionViewItem(), model.createIndex(0, 0))
    assert editor.value is False
    delegate.setEditorData(editor, model.createIndex(0, 0))
    assert editor.value is True
    assert model.raw_data == [True, False]
    editor.click()
    assert editor.value is False
    assert model.raw_data == [False, False]
    editor.click()
    assert editor.value is True
    assert model.raw_data == [True, False]
    delegate.setEditorData(editor, model.createIndex(1, 0))
    assert editor.value is False
    assert model.raw_data == [True, False]
    editor.click()
    assert editor.value is True
    assert model.raw_data == [True, True]
    editor.click()
    assert editor.value is False
    assert model.raw_data == [True, False]


@pytest.mark.parametrize("locale", [QLocale.system(), QLocale("de")])
@pytest.mark.parametrize("value", [True, False, None, 1, "string"])
def test_boolean_delegate_display_text_empty(locale, value):
    delegate = BooleanPropertyColumnDelegate()
    assert delegate.displayText(value, locale) == ""


@pytest.mark.parametrize("return_code", [0, 1, 2, 505])
def test_exec_app_interruptable(return_code):
    app = mock.MagicMock()
    app.exec_.return_value = return_code
    with mock.patch("accwidgets.qt.attach_sigint") as attach_sigint:
        res = exec_app_interruptable(app)
        assert res == return_code
        attach_sigint.assert_called_once_with(app)
        app.exec_.assert_called_once()
