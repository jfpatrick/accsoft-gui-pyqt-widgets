import sys
from asyncio import CancelledError
from typing import List
from unittest import mock

import pytest
from PyQt5.QtTest import QAbstractItemModelTester
from pytestqt.qtbot import QtBot
from qtpy.QtCore import QVariant, Qt
from qtpy.QtWidgets import QStyleOptionViewItem, QAction, QPushButton, QDialogButtonBox, QFormLayout

from accwidgets.property_edit.designer.designer_extensions import (
    FieldsDialog,
    EnumEditorTableModel,
    FieldEditorTableModel,
    PropertyFieldExtension,
    EnumTableData,
    NumericFieldDialog,
)
from accwidgets.property_edit.propedit import PropertyEdit, PropertyEditField, _pack_designer_fields
from ..async_shim import AsyncMock


@pytest.fixture
def some_fields():
    return [
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.STRING, editable=True),
    ]


def mock_property_edit(config: List[PropertyEditField]) -> mock.MagicMock:
    property_edit = mock.MagicMock(spec=PropertyEdit)
    # Because designer always expects JSON, we need to "pack" it.
    # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
    property_edit.fields = _pack_designer_fields(config)
    return property_edit


@pytest.fixture
def some_enum_config():
    return [EnumTableData(label="label1", value=1),
            EnumTableData(label="label2", value=2),
            EnumTableData(label="label3", value=3)]


@pytest.mark.parametrize("editable", [True, False])
def test_field_editor_table_model_flags(editable):
    data = [
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.INTEGER, editable=editable),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.REAL, editable=editable),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.BOOLEAN, editable=editable),
        PropertyEditField(field="f4", type=PropertyEdit.ValueType.STRING, editable=editable),
        PropertyEditField(field="f5", type=PropertyEdit.ValueType.ENUM, editable=editable, user_data={"options": [("label", 1)]}),
    ]
    expected_flags = [
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable],
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable],
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled],
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled],
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable],
    ]
    model = FieldEditorTableModel(data)
    for i, row in enumerate(expected_flags):
        for j, cell in enumerate(row):
            expected_flag = int(cell)
            actual_flag = int(model.flags(model.index(i, j)))
            assert actual_flag == expected_flag, f"Cell {i}, {j} does not correspond to flags {actual_flag} ({expected_flag} expected)"


@pytest.mark.parametrize("editable", [True, False])
def test_enum_editor_table_model_flags(editable):
    data = [("label1", 1), ("label2", 2), ("label3", 3)]
    expected_flags = [
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable],
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable],
        [Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable,
         Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable],
    ]
    model = EnumEditorTableModel(data)
    for i, row in enumerate(expected_flags):
        for j, cell in enumerate(row):
            expected_flag = int(cell)
            actual_flag = int(model.flags(model.index(i, j)))
            assert actual_flag == expected_flag, f"Cell {i}, {j} does not correspond to flags {actual_flag} ({expected_flag} expected)"


@pytest.mark.parametrize("fields, expected_string", [
    ([
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.BOOLEAN, editable=False),
    ], '[{"field": "f1", "type": 4, "rw": true}, {"field": "f2", "type": 3, "rw": false}]'),
])
@mock.patch("qtpy.QtDesigner.QDesignerFormWindowInterface.findFormWindow")
def test_dialog_updates_fields_as_JSON(find_form_mock, qtbot: QtBot, fields, expected_string):
    property_edit = mock_property_edit(fields)
    qtbot.add_widget(property_edit)
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    dialog.show()
    dialog._save()
    find_form_mock().cursor().setProperty.assert_called_with("fields", expected_string)


@mock.patch("accwidgets.property_edit.designer.designer_extensions.FieldsDialog.show")
@mock.patch("accwidgets.property_edit.designer.designer_extensions.FieldsDialog.open")
def test_edit_contents_opens_dialog(show_mock, open_mock, qtbot: QtBot):
    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields([])
        property_edit = PropertyEdit()
        qtbot.add_widget(property_edit)
        ext = PropertyFieldExtension(property_edit)
        assert len(ext.actions()) == 1
        act = ext.actions()[0]
        act.activate(QAction.Trigger)
        show_mock.assert_called_once()
        open_mock.assert_called_once()


@pytest.mark.parametrize("row, calls_parent, draws_control, expected_title", [
    (0, False, True, "Configure"),
    (1, False, True, "Configure"),
    (2, False, True, "Configure"),
    (3, False, True, "Configure (1 option)"),
    (4, False, True, "Configure (2 options)"),
])
def test_render_enum_configure_btn(qtbot: QtBot, calls_parent, draws_control, expected_title, row):
    config = [
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.ENUM, editable=True),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={}),
        PropertyEditField(field="f4", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": []}),
        PropertyEditField(field="f5", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": [(1, "test1")]}),
        PropertyEditField(field="f6", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": [(1, "test1"), (2, "test2")]}),
    ]

    property_edit = mock_property_edit(config)
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    dialog.show()
    dialog.table.selectRow(row)
    user_data_column = 4
    delegate = dialog.table.itemDelegateForColumn(user_data_column)
    index = dialog.table.model().createIndex(row, user_data_column)
    editor = delegate.createEditor(dialog.table, QStyleOptionViewItem(), index)
    assert isinstance(editor, QPushButton)
    delegate.setEditorData(editor, index)
    assert editor.text() == expected_title


@pytest.mark.parametrize("row, handles_single_click, handles_dbl_click, editor_options", [
    (0, True, True, []),
    (1, True, True, []),
    (2, True, True, []),
    (3, True, True, [[1, "test1"]]),
    (4, True, True, [[1, "test1"], [2, "test2"]]),
])
@mock.patch("accwidgets.property_edit.designer.designer_extensions.EnumOptionsDialog")
def test_enum_user_data_event(opt_dialog, qtbot: QtBot, row, handles_dbl_click, handles_single_click, editor_options):
    config = [
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.ENUM, editable=True),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={}),
        PropertyEditField(field="f4", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": []}),
        PropertyEditField(field="f5", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": [(1, "test1")]}),
        PropertyEditField(field="f6", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": [(1, "test1"), (2, "test2")]}),
    ]

    property_edit = mock_property_edit(config)
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    dialog.show()
    user_data_column = 4
    delegate = dialog.table.itemDelegateForColumn(user_data_column)
    index = dialog.table.model().createIndex(row, user_data_column)
    editor = delegate.createEditor(dialog.table, QStyleOptionViewItem(), index)
    assert isinstance(editor, QPushButton)
    editor.click()
    opt_dialog.assert_called_once_with(options=editor_options, on_save=mock.ANY, parent=mock.ANY)
    opt_dialog.return_value.exec_.assert_called_once()


@pytest.mark.parametrize("row, handles_single_click, handles_dbl_click, use_precision, editor_options", [
    (0, True, True, True, {}),
    (1, True, True, True, {}),
    (2, True, True, True, {"min": -0.1}),
    (3, True, True, True, {"max": 0.1}),
    (4, True, True, True, {"min": -0.1, "max": 0.1}),
    (5, True, True, True, {"units": "TST"}),
    (6, True, True, True, {"precision": 1}),
    (7, True, True, True, {"min": -0.1, "max": 0.1, "units": "TST", "precision": 1}),
    (8, True, True, False, {}),
    (9, True, True, False, {}),
    (10, True, True, False, {"min": -0.1}),
    (11, True, True, False, {"max": 0.1}),
    (12, True, True, False, {"min": -0.1, "max": 0.1}),
    (13, True, True, False, {"units": "TST"}),
    (14, True, True, False, {"min": -0.1, "max": 0.1, "units": "TST"}),
])
@mock.patch("accwidgets.property_edit.designer.designer_extensions.NumericFieldDialog")
def test_numeric_user_data_event(opt_dialog, qtbot: QtBot, row, handles_dbl_click, handles_single_click, use_precision, editor_options):
    config = [
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.REAL, editable=True),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.REAL, editable=True, user_data={}),
        PropertyEditField(field="f4", type=PropertyEdit.ValueType.REAL, editable=True, user_data={"min": -0.1}),
        PropertyEditField(field="f5", type=PropertyEdit.ValueType.REAL, editable=True, user_data={"max": 0.1}),
        PropertyEditField(field="f6", type=PropertyEdit.ValueType.REAL, editable=True, user_data={"min": -0.1, "max": 0.1}),
        PropertyEditField(field="f7", type=PropertyEdit.ValueType.REAL, editable=True, user_data={"units": "TST"}),
        PropertyEditField(field="f8", type=PropertyEdit.ValueType.REAL, editable=True, user_data={"precision": 1}),
        PropertyEditField(field="f9", type=PropertyEdit.ValueType.REAL, editable=True, user_data={"min": -0.1, "max": 0.1, "units": "TST", "precision": 1}),
        PropertyEditField(field="f10", type=PropertyEdit.ValueType.INTEGER, editable=True),
        PropertyEditField(field="f11", type=PropertyEdit.ValueType.INTEGER, editable=True, user_data={}),
        PropertyEditField(field="f12", type=PropertyEdit.ValueType.INTEGER, editable=True, user_data={"min": -0.1}),
        PropertyEditField(field="f13", type=PropertyEdit.ValueType.INTEGER, editable=True, user_data={"max": 0.1}),
        PropertyEditField(field="f14", type=PropertyEdit.ValueType.INTEGER, editable=True, user_data={"min": -0.1, "max": 0.1}),
        PropertyEditField(field="f15", type=PropertyEdit.ValueType.INTEGER, editable=True, user_data={"units": "TST"}),
        PropertyEditField(field="f16", type=PropertyEdit.ValueType.INTEGER, editable=True, user_data={"min": -0.1, "max": 0.1, "units": "TST"}),
    ]

    property_edit = mock_property_edit(config)
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    dialog.show()
    user_data_column = 4
    delegate = dialog.table.itemDelegateForColumn(user_data_column)
    index = dialog.table.model().createIndex(row, user_data_column)
    editor = delegate.createEditor(dialog.table, QStyleOptionViewItem(), index)
    assert isinstance(editor, QPushButton)
    editor.click()
    opt_dialog.assert_called_once_with(config=editor_options, on_save=mock.ANY, use_precision=use_precision, parent=mock.ANY)
    opt_dialog.return_value.exec_.assert_called_once()


@pytest.mark.parametrize("initial_fields, initial_enabled", [
    ([
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.STRING, editable=True),
    ], True),
    ([], False),
])
def test_field_dialog_disabled_buttons(qtbot: QtBot, initial_fields, initial_enabled):
    property_edit = mock_property_edit(initial_fields)
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    dialog.show()
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False
    assert dialog.all_rw.isEnabled() is initial_enabled
    assert dialog.all_ro.isEnabled() is initial_enabled
    dialog.add_btn.click()
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False
    assert dialog.all_rw.isEnabled() is True
    assert dialog.all_ro.isEnabled() is True
    dialog.table.selectRow(0)
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is True
    assert dialog.all_rw.isEnabled() is True
    assert dialog.all_ro.isEnabled() is True
    for _ in range(len(initial_fields) + 1):
        dialog.table.selectRow(0)
        dialog.remove_btn.click()
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False
    assert dialog.all_rw.isEnabled() is False
    assert dialog.all_ro.isEnabled() is False


@pytest.mark.parametrize("initial_animation_started", [True, False])
@pytest.mark.parametrize("loading,expect_animation_started,expected_page_idx", [
    (False, False, 0),
    (True, True, 1),
])
def test_field_dialog_update_ui_for_loading(qtbot: QtBot, loading, expect_animation_started, expected_page_idx,
                                            initial_animation_started):
    property_edit = mock_property_edit([])
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    if initial_animation_started:
        dialog.activity_indicator.startAnimation()
    dialog._update_ui_for_loading(loading)
    assert dialog.activity_indicator.animating == expect_animation_started
    assert dialog.stack.currentIndex() == expected_page_idx
    # Stop timers running inside animation so that consecutive tests don't break
    dialog.activity_indicator.stopAnimation()


@pytest.mark.parametrize("task_exists,should_cancel", [
    (True, True),
    (False, False),
])
def test_field_dialog_cancel_running_tasks(qtbot: QtBot, should_cancel, task_exists):
    property_edit = mock_property_edit([])
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    task_mock = mock.Mock()
    dialog._active_ccda_task = task_mock if task_exists else None
    dialog._cancel_running_tasks()
    if should_cancel:
        task_mock.cancel.assert_called_once_with()
    else:
        task_mock.cancel.assert_not_called()


@mock.patch("accwidgets.property_edit.designer.designer_extensions.FieldsDialog._cancel_running_tasks")
def test_field_dialog_stops_active_task_on_hide(cancel_running_tasks, qtbot: QtBot):
    property_edit = mock_property_edit([])
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    with qtbot.wait_exposed(dialog):
        dialog.show()
    cancel_running_tasks.assert_not_called()
    dialog.hide()
    cancel_running_tasks.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("param_name,expected_hint", [
    ("test/prop", 'Resolving "test/prop" property structure...'),
    ("rda3:///test/prop", 'Resolving "rda3:///test/prop" property structure...'),
])
async def test_field_dialog_populate_from_param_sets_in_progress_ui(qtbot: QtBot, param_name, expected_hint):

    class TestException(Exception):
        pass

    property_edit = mock_property_edit([])
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.resolve_from_param",
                    new_callable=AsyncMock,
                    side_effect=TestException) as resolve_from_param:
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        assert dialog.activity_indicator.hint == ""
        resolve_from_param.assert_not_called()
        with mock.patch.object(dialog, "_update_ui_for_loading") as update_ui_for_loading:
            with mock.patch.object(dialog, "_show_info"):  # Prevent error model dialog from blocking UI
                await dialog._populate_from_param(param_name)
                # The second call is expected to be a failure, because we purposefully throw an exception for early exit,
                # so it will re-render the UI to failure.
                assert update_ui_for_loading.call_args_list == [mock.call(True),
                                                                mock.call(False)]
                resolve_from_param.assert_called_once_with(param_name)
                assert dialog.activity_indicator.hint == expected_hint
                assert dialog._active_ccda_task is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("return_any_fields", [True, False])
async def test_field_dialog_populate_from_param_success_sets_ui(qtbot: QtBot, some_fields, return_any_fields):

    property_edit = mock_property_edit([])
    results = some_fields if return_any_fields else []
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.resolve_from_param",
                    new_callable=AsyncMock,
                    return_value=(results, set())) as resolve_from_param:
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        resolve_from_param.assert_not_called()
        with mock.patch.object(dialog, "_show_info") as show_info:  # Prevent error model dialog from blocking UI
            await dialog._populate_from_param("dev/prop")
            resolve_from_param.assert_called_once_with("dev/prop")
            assert dialog._table_model.raw_data == results
            assert dialog._active_ccda_task is not None
            assert not dialog.activity_indicator.animating
            assert dialog.stack.currentIndex() == 0
            show_info.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("skipped_items,expected_error", [
    (set(), None),
    ({"f2", "f1"}, "The following fields were not mapped, as their types are unsupported:\n\n- f1\n- f2"),
])
@pytest.mark.parametrize("return_any_fields", [True, False])
async def test_field_dialog_populate_from_param_success_notifies_skipped_items(qtbot: QtBot, some_fields,
                                                                               return_any_fields, skipped_items,
                                                                               expected_error):

    property_edit = mock_property_edit([])
    results = some_fields if return_any_fields else []
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.resolve_from_param",
                    new_callable=AsyncMock,
                    return_value=(results, skipped_items)) as resolve_from_param:
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        resolve_from_param.assert_not_called()
        with mock.patch("qtpy.QtWidgets.QMessageBox.information") as mocked_warning:
            await dialog._populate_from_param("dev/prop")
            if expected_error is None:
                mocked_warning.assert_not_called()
            else:
                mocked_warning.assert_called_once_with(dialog, "Some items were skipped", expected_error)


@pytest.mark.asyncio
@pytest.mark.parametrize("error,expected_message", [
    (TypeError, ""),
    (ValueError, ""),
    (ValueError("Some error"), "Some error"),
])
async def test_field_dialog_populate_from_param_sets_ui_on_error(qtbot: QtBot, expected_message, error):

    property_edit = mock_property_edit([])
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.resolve_from_param",
                    new_callable=AsyncMock,
                    side_effect=error) as resolve_from_param:
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        resolve_from_param.assert_not_called()
        with mock.patch("qtpy.QtWidgets.QMessageBox.warning") as mocked_warning:
            await dialog._populate_from_param("dev/prop")
            mocked_warning.assert_called_once_with(dialog, "Error occurred", expected_message)


@pytest.mark.asyncio
@pytest.mark.parametrize("prev_loading", [False, True])
async def test_field_dialog_populate_from_param_rolls_back_ui_on_cancel(qtbot: QtBot, prev_loading):

    property_edit = mock_property_edit([])
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.resolve_from_param",
                    new_callable=AsyncMock,
                    side_effect=CancelledError) as resolve_from_param:
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        dialog.activity_indicator = mock.MagicMock()  # prevent pixmap init, which causes C++ virtual method error
        dialog._update_ui_for_loading(prev_loading)
        with mock.patch.object(dialog, "_update_ui_for_loading") as update_ui_for_loading:
            with mock.patch.object(dialog, "_show_info") as show_info:  # Prevent error model dialog from blocking UI
                resolve_from_param.assert_not_called()
                await dialog._populate_from_param("dev/prop")
                resolve_from_param.assert_called_once()
                assert update_ui_for_loading.call_args_list == [mock.call(True),
                                                                mock.call(False)]
                show_info.assert_not_called()


@pytest.mark.parametrize("import_fails,expect_show_button", [
    (False, True),
    (True, False),
])
def test_field_dialog_hides_ccdb_button_when_parameter_selector_cant_be_imported(qtbot: QtBot, import_fails,
                                                                                 expect_show_button, monkeypatch):
    if import_fails:
        monkeypatch.setitem(sys.modules, "accwidgets.parameter_selector", None)
    property_edit = mock_property_edit([])
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    with qtbot.wait_exposed(dialog):
        dialog.show()
    assert dialog.ccdb_btn.isVisible() == expect_show_button


@pytest.mark.asyncio
@pytest.mark.parametrize("import_fails,expect_calls_inner", [
    (False, True),
    (True, False),
])
async def test_field_dialog_noop_ccda_resolve_when_function_cant_be_imported(qtbot: QtBot, import_fails,
                                                                             expect_calls_inner, monkeypatch):
    if import_fails:
        monkeypatch.setitem(sys.modules, "accwidgets.property_edit.designer.ccda_resolver", None)
    property_edit = mock_property_edit([])
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.resolve_from_param",
                    new_callable=AsyncMock,
                    side_effect=CancelledError) as resolve_from_param:  # Finish quickly with cancelled error
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        resolve_from_param.assert_not_called()
        await dialog._populate_from_param("dev/prop")
        if expect_calls_inner:
            resolve_from_param.assert_called_once_with("dev/prop")
        else:
            resolve_from_param.assert_not_called()


@pytest.mark.parametrize("editable", [True, False])
@pytest.mark.parametrize("value_type, user_data", [
    (PropertyEdit.ValueType.INTEGER, None),
    (PropertyEdit.ValueType.REAL, None),
    (PropertyEdit.ValueType.BOOLEAN, None),
    (PropertyEdit.ValueType.STRING, None),
    (PropertyEdit.ValueType.ENUM, {"options": [("label", 1)]}),
])
@pytest.mark.parametrize("num_fields", [0, 1, 3])
def test_fields_validate_succeeds(editable, value_type, user_data, num_fields):
    data = []
    for idx in range(num_fields):
        data.append(PropertyEditField(field=f"f{idx}", type=value_type, editable=editable, user_data=user_data))
    model = FieldEditorTableModel(data)
    model.validate()


@pytest.mark.parametrize("editable", [True, False])
@pytest.mark.parametrize("value_type, user_data", [
    (PropertyEdit.ValueType.INTEGER, None),
    (PropertyEdit.ValueType.REAL, None),
    (PropertyEdit.ValueType.BOOLEAN, None),
    (PropertyEdit.ValueType.STRING, None),
    (PropertyEdit.ValueType.ENUM, {"options": [("label", 1)]}),
])
@pytest.mark.parametrize("num_fields", [0, 1, 3])
def test_fields_model(editable, value_type, user_data, num_fields):
    data = []
    for idx in range(num_fields):
        data.append(PropertyEditField(field=f"f{idx}", type=value_type, editable=editable, user_data=user_data))
    model = FieldEditorTableModel(data)
    _ = QAbstractItemModelTester(model)


@pytest.mark.parametrize("data, error_msg", [
    ([PropertyEditField(field="", type=PropertyEdit.ValueType.INTEGER, editable=False)], 'Row #1 is lacking mandatory "Field name".'),
    ([PropertyEditField(field="f1", type=-1, editable=False)], 'Row #1 defines unknown "Field type".'),  # type: ignore  # Force allow faulty type
    ([PropertyEditField(field="f1", type=PropertyEdit.ValueType.ENUM, editable=False)], 'Row #1 must define enum options via "User data".'),
    ([PropertyEditField(field="f1", type=PropertyEdit.ValueType.ENUM, editable=False, user_data={})], 'Row #1 must define enum options via "User data".'),
    ([PropertyEditField(field="f1", type=PropertyEdit.ValueType.ENUM, editable=False, user_data={"options": None})], 'Row #1 must define enum options via "User data".'),
    ([PropertyEditField(field="f1", type=PropertyEdit.ValueType.ENUM, editable=False, user_data={"options": []})], 'Row #1 must define enum options via "User data".'),
    ([PropertyEditField(field="f1", type=PropertyEdit.ValueType.REAL, editable=True, user_data={"precision": 0})], "Row #1 has 0 precision for REAL type. Use INTEGER instead."),
    ([PropertyEditField(field="f1", type=PropertyEdit.ValueType.REAL, editable=False, user_data={"precision": 0})], "Row #1 has 0 precision for REAL type. Use INTEGER instead."),
    ([
     PropertyEditField(field="", type=PropertyEdit.ValueType.INTEGER, editable=False),
     PropertyEditField(field="", type=PropertyEdit.ValueType.INTEGER, editable=False),
     ], 'Row #1 is lacking mandatory "Field name".'),
    ([
     PropertyEditField(field="test", type=PropertyEdit.ValueType.INTEGER, editable=False),
     PropertyEditField(field="test", type=PropertyEdit.ValueType.INTEGER, editable=False),
     ], 'Field "test" is used more than once.'),
])
def test_fields_validate_fails(data, error_msg):
    model = FieldEditorTableModel(data)
    with pytest.raises(ValueError, match=error_msg):
        model.validate()


@pytest.mark.parametrize("data", [
    [],
    [EnumTableData(label="label1", value=0)],
    [EnumTableData(label="label1", value=-1)],
    [EnumTableData(label="label1", value=999)],
    [EnumTableData(label="label1", value=0), EnumTableData(label="label2", value=1)],
])
def test_enum_config_validate_succeeds(data):
    model = EnumEditorTableModel(data=data)
    model.validate()


@pytest.mark.parametrize("initial_config, expected_value", [
    ([], 0),
    ([EnumTableData(label="label1", value=0)], 1),
    ([EnumTableData(label="label1", value=0), EnumTableData(label="label2", value=1)], 2),
    ([EnumTableData(label="label1", value=10), EnumTableData(label="label2", value=1)], 11),
])
def test_enum_default_value_increases(initial_config, expected_value):
    model = EnumEditorTableModel(data=initial_config)
    model.append_row()
    last_value = model.raw_data[-1].value
    assert last_value == expected_value


@pytest.mark.parametrize("data", [
    [],
    [EnumTableData(label="label1", value=0)],
    [EnumTableData(label="label1", value=-1)],
    [EnumTableData(label="label1", value=999)],
    [EnumTableData(label="label1", value=0), EnumTableData(label="label2", value=1)],
])
def test_enum_model(data):
    model = EnumEditorTableModel(data=data)
    _ = QAbstractItemModelTester(model)


@pytest.mark.parametrize("data, error_msg", [
    ([EnumTableData(label="", value=0)], r'Row #1 is lacking "Label".'),
    ([EnumTableData(label="label1", value=0), EnumTableData(label="", value=1)], r'Row #2 is lacking "Label".'),
    ([EnumTableData(label=None, value=0)], r'Row #1 is lacking "Label".'),  # type: ignore  # Pretend we do not care about type hints
    ([EnumTableData(label="label1", value=0), EnumTableData(label="label2", value=0)], r'Enum value "0" is being used more than once.'),
    ([EnumTableData(label="label1", value=0), EnumTableData(label="label1", value=1)], r'Label value "label1" is being used more than once.'),
    ([EnumTableData(label="label1", value=0), EnumTableData(label="label1", value=0)], r'(Enum value "0" is being used more than once.)|(Label value "label1" is being used more than once.)'),
    ([EnumTableData(label="label1", value=0), EnumTableData(label=None, value=0)], r'(Row #2 is lacking "Label".)|(Enum value "0" is being used more than once.)'),  # type: ignore  # Pretend we do not care about type hints
])
def test_enum_config_validate_fails(data, error_msg):
    model = EnumEditorTableModel(data=data)
    with pytest.raises(ValueError, match=error_msg):
        model.validate()


@pytest.mark.parametrize("initial_data", [
    {},
    {"min": 1},
    {"max": 4},
    {"min": -2, "max": 5},
    {"max": -2, "min": 5},
    {"units": "TST"},
    {"precision": 3},
    {"units": "TST", "precision": 3},
    {"units": "TST", "precision": 3, "min": -2, "max": 5},
    {"units": "TST", "min": -2, "max": 5},
])
@pytest.mark.parametrize("use_precision,chk_prec,prec_val,chk_unit,unit_val,chk_min,min_val,chk_max,max_val,expected_error", [
    (False, None, None, False, "", True, 0, True, -1, "Min value cannot be greater than max"),
    (False, None, None, False, "", True, 10, True, 2, "Min value cannot be greater than max"),
    (True, False, 0, False, "", True, 0, True, -1, "Min value cannot be greater than max"),
    (True, False, 0, False, "", True, 10, True, 2, "Min value cannot be greater than max"),
    (True, False, 0, False, "", True, 0.0, True, -0.1, "Min value cannot be greater than max"),
    (True, False, 0, False, "", True, 10, True, 2.5, "Min value cannot be greater than max"),
    (True, False, 1, False, "", True, 0, True, -1, "Min value cannot be greater than max"),
    (True, False, 1, False, "", True, 10, True, 2, "Min value cannot be greater than max"),
    (True, False, 1, False, "", True, 0.0, True, -0.1, "Min value cannot be greater than max"),
    (True, False, 1, False, "", True, 10, True, 2.5, "Min value cannot be greater than max"),
])
@mock.patch("accwidgets.property_edit.designer.designer_extensions.QMessageBox")
def test_numeric_dialog_save_fails(QMessageBox, qtbot: QtBot, initial_data, use_precision, chk_prec, chk_max, chk_min, chk_unit,
                                   prec_val, unit_val, min_val, max_val, expected_error):
    widget = NumericFieldDialog(config=initial_data, use_precision=use_precision, on_save=mock.Mock())
    qtbot.add_widget(widget)
    if use_precision:
        widget.chkbx_precision.setChecked(chk_prec)
        widget.precision_spinbox.setValue(prec_val)
    widget.chkbx_max.setChecked(chk_max)
    widget.max_spinbox.setValue(max_val)
    widget.chkbx_min.setChecked(chk_min)
    widget.min_spinbox.setValue(min_val)
    widget.chkbx_units.setChecked(chk_unit)
    widget.units_line.setText(unit_val)
    QMessageBox.warning.assert_not_called()
    widget.buttons.button(QDialogButtonBox.Ok).click()
    QMessageBox.warning.assert_called_with(mock.ANY, "Invalid data", expected_error)


@pytest.mark.parametrize("initial_data", [
    {},
    {"min": 1},
    {"max": 4},
    {"min": -2, "max": 5},
    {"max": -2, "min": 5},
    {"units": "TST"},
    {"precision": 3},
    {"units": "TST", "precision": 3},
    {"units": "TST", "precision": 3, "min": -2, "max": 5},
    {"units": "TST", "min": -2, "max": 5},
])
@pytest.mark.parametrize("use_precision,chk_prec,prec_val,chk_unit,unit_val,chk_min,min_val,chk_max,max_val,expected_res", [
    (False, None, None, False, "", False, 0, False, 0, {}),
    (False, None, None, True, "", False, 0, False, 0, {}),
    (False, None, None, True, "TST", False, 0, False, 0, {"units": "TST"}),
    (False, None, None, False, "", True, 5, False, 0, {"min": 5}),
    (False, None, None, False, "", True, -5, False, 0, {"min": -5}),
    (False, None, None, False, "", True, 0, False, 0, {"min": 0}),
    (False, None, None, False, "", False, 0, True, 0, {"max": 0}),
    (False, None, None, False, "", False, 0, True, 5, {"max": 5}),
    (False, None, None, False, "", False, 0, True, -5, {"max": -5}),
    (False, None, None, False, "", True, 5, True, 10, {"min": 5, "max": 10}),
    (False, None, None, False, "", True, 5, True, 5, {"min": 5, "max": 5}),
    (False, None, None, False, "", True, -5, True, 5, {"min": -5, "max": 5}),
    (False, None, None, True, "TST", True, -5, True, 5, {"units": "TST", "min": -5, "max": 5}),
    (True, False, 1, False, "", False, 0, False, 0, {}),
    (True, False, 1, True, "", False, 0, False, 0, {}),
    (True, False, 1, True, "TST", False, 0, False, 0, {"units": "TST"}),
    (True, True, 3, False, "", False, 0, False, 0, {"precision": 3}),
    (True, False, 1, False, "", True, 5, False, 0, {"min": 5}),
    (True, False, 1, False, "", True, -5, False, 0, {"min": -5}),
    (True, False, 1, False, "", True, 0, False, 0, {"min": 0}),
    (True, False, 1, False, "", False, 0, True, 0, {"max": 0}),
    (True, False, 1, False, "", False, 0, True, 5, {"max": 5}),
    (True, False, 1, False, "", False, 0, True, -5, {"max": -5}),
    (True, False, 1, False, "", True, 5, True, 10, {"min": 5, "max": 10}),
    (True, False, 1, False, "", True, 5, True, 5, {"min": 5, "max": 5}),
    (True, False, 1, False, "", True, -5, True, 5, {"min": -5, "max": 5}),
    (True, True, 3, False, "", True, -5, True, 5, {"precision": 3, "min": -5, "max": 5}),
    (True, False, 1, True, "TST", True, -5, True, 5, {"units": "TST", "min": -5, "max": 5}),
    (True, True, 3, True, "TST", True, -5, True, 5, {"precision": 3, "units": "TST", "min": -5, "max": 5}),
])
def test_numeric_dialog_save_succeeds(qtbot: QtBot, initial_data, use_precision, chk_prec, chk_max, chk_min, chk_unit,
                                      prec_val, unit_val, min_val, max_val, expected_res):
    on_save = mock.Mock()
    widget = NumericFieldDialog(config=initial_data, use_precision=use_precision, on_save=on_save)
    qtbot.add_widget(widget)
    if use_precision:
        widget.chkbx_precision.setChecked(chk_prec)
        widget.precision_spinbox.setValue(prec_val)
    widget.chkbx_max.setChecked(chk_max)
    widget.max_spinbox.setValue(max_val)
    widget.chkbx_min.setChecked(chk_min)
    widget.min_spinbox.setValue(min_val)
    widget.chkbx_units.setChecked(chk_unit)
    widget.units_line.setText(unit_val)
    on_save.assert_not_called()
    widget.buttons.button(QDialogButtonBox.Ok).click()
    on_save.assert_called_with(expected_res)


@pytest.mark.parametrize(
    "use_precision,initial_data,expect_chk_prec,expect_chk_max,expect_chk_min,expect_chk_unit,"
    "expected_prec_val,expected_unit_val,expected_min_val,expected_max_val",
    [
        (False, {}, False, False, False, False, None, "", 0, 0),
        (False, {"min": -2}, False, False, True, False, None, "", -2, 0),
        (False, {"min": 0}, False, False, True, False, None, "", 0, 0),
        (False, {"max": 2}, False, True, False, False, None, "", 0, 2),
        (False, {"max": 0}, False, True, False, False, None, "", 0, 0),
        (False, {"units": "TST"}, False, False, False, True, None, "TST", 0, 0),
        (False, {"max": 2, "min": -2}, False, True, True, False, None, "", -2, 2),
        (False, {"max": 0, "min": 0}, False, True, True, False, None, "", 0, 0),
        (False, {"units": "TST", "min": -2}, False, False, True, True, None, "TST", -2, 0),
        (False, {"units": "TST", "max": 2}, False, True, False, True, None, "TST", 0, 2),
        (False, {"units": "TST", "max": 2, "min": -2}, False, True, True, True, None, "TST", -2, 2),
        (True, {}, False, False, False, False, 1, "", 0, 0),
        (True, {"min": -2}, False, False, True, False, 1, "", -2, 0),
        (True, {"min": 0}, False, False, True, False, 1, "", 0, 0),
        (True, {"max": 2}, False, True, False, False, 1, "", 0, 2),
        (True, {"max": 0}, False, True, False, False, 1, "", 0, 0),
        (True, {"units": "TST"}, False, False, False, True, 1, "TST", 0, 0),
        (True, {"precision": 3}, True, False, False, False, 3, "", 0, 0),
        (True, {"max": 2, "min": -2}, False, True, True, False, 1, "", -2, 2),
        (True, {"max": 2, "precision": 3}, True, True, False, False, 3, "", 0, 2),
        (True, {"precision": 3, "min": -2}, True, False, True, False, 3, "", -2, 0),
        (True, {"max": 0, "min": 0}, False, True, True, False, 1, "", 0, 0),
        (True, {"precision": 3, "units": "TST"}, True, False, False, True, 3, "TST", 0, 0),
        (True, {"units": "TST", "min": -2}, False, False, True, True, 1, "TST", -2, 0),
        (True, {"units": "TST", "max": 2}, False, True, False, True, 1, "TST", 0, 2),
        (True, {"max": 2, "min": -2, "precision": 3}, True, True, True, False, 3, "", -2, 2),
        (True, {"max": 2, "units": "TST", "precision": 3}, True, True, False, True, 3, "TST", 0, 2),
        (True, {"units": "TST", "min": -2, "precision": 3}, True, False, True, True, 3, "TST", -2, 0),
        (True, {"units": "TST", "max": 2, "min": -2}, False, True, True, True, 1, "TST", -2, 2),
        (True, {"units": "TST", "max": 2, "min": -2, "precision": 3}, True, True, True, True, 3, "TST", -2, 2),
    ],
)
def test_numeric_dialog_configures_initial_ui(use_precision, initial_data, expected_prec_val, expected_max_val, expected_unit_val,
                                              expected_min_val, expect_chk_min, expect_chk_max, expect_chk_prec,
                                              expect_chk_unit, qtbot: QtBot):
    widget = NumericFieldDialog(config=initial_data, use_precision=use_precision, on_save=mock.Mock())
    qtbot.add_widget(widget)
    assert widget.chkbx_min.isChecked() == expect_chk_min
    assert widget.chkbx_max.isChecked() == expect_chk_max
    assert widget.chkbx_units.isChecked() == expect_chk_unit
    assert widget.min_spinbox.value() == expected_min_val
    assert widget.max_spinbox.value() == expected_max_val
    assert widget.units_line.text() == expected_unit_val

    if use_precision:
        assert widget.chkbx_precision.isChecked() == expect_chk_prec
        assert widget.precision_spinbox.value() == expected_prec_val


@pytest.mark.parametrize("use_precision,expect_precision_controls", [
    (True, True),
    (False, False),
])
def test_numeric_dialog_precision_not_available_for_int(qtbot: QtBot, use_precision, expect_precision_controls):
    widget = NumericFieldDialog(config={}, use_precision=use_precision, on_save=mock.Mock())
    qtbot.add_widget(widget)
    assert widget.form.rowCount() == 4 if expect_precision_controls else 3
    assert widget.form.itemAt(0, QFormLayout.LabelRole).widget() == widget.chkbx_units
    assert widget.form.itemAt(0, QFormLayout.FieldRole).widget() == widget.units_line
    assert widget.form.itemAt(1, QFormLayout.LabelRole).widget() == widget.chkbx_min
    assert widget.form.itemAt(1, QFormLayout.FieldRole).widget() == widget.min_spinbox
    assert widget.form.itemAt(2, QFormLayout.LabelRole).widget() == widget.chkbx_max
    assert widget.form.itemAt(2, QFormLayout.FieldRole).widget() == widget.max_spinbox
    if expect_precision_controls:
        assert widget.form.itemAt(3, QFormLayout.LabelRole).widget() == widget.chkbx_precision
        assert widget.form.itemAt(3, QFormLayout.FieldRole).widget() == widget.precision_spinbox


@pytest.mark.parametrize("initial_data,expected_initial_decimals", [
    ({}, 1),
    ({"min": 1}, 1),
    ({"max": 4}, 1),
    ({"min": -2, "max": 5}, 1),
    ({"max": -2, "min": 5}, 1),
    ({"units": "TST"}, 1),
    ({"precision": 3}, 3),
    ({"units": "TST", "precision": 3}, 3),
    ({"units": "TST", "precision": 3, "min": -2, "max": 5}, 3),
    ({"units": "TST", "min": -2, "max": 5}, 1),
])
@pytest.mark.parametrize("new_precision,expected_new_decimals", [
    (1, 1),
    (2, 2),
    (3, 3),
    (10, 10),
    (15, 15),
    (20, 20),
])
def test_numeric_dialog_precision_reconfigures_limits(qtbot: QtBot, initial_data, expected_initial_decimals, new_precision,
                                                      expected_new_decimals):
    widget = NumericFieldDialog(config=initial_data, use_precision=True, on_save=mock.Mock())
    qtbot.add_widget(widget)
    assert widget.min_spinbox.decimals() == expected_initial_decimals
    assert widget.max_spinbox.decimals() == expected_initial_decimals
    widget.precision_spinbox.setValue(new_precision)
    assert widget.min_spinbox.decimals() == expected_new_decimals
    assert widget.max_spinbox.decimals() == expected_new_decimals


@pytest.mark.parametrize("use_precision,initial_data,toggle_prec,toggle_min,toggle_max,toggle_unit,expect_prec_enabled,expect_min_enabled,expect_max_enabled,expect_unit_enabled", [
    (False, {}, False, False, False, False, False, False, False, False),
    (False, {"min": 1}, False, False, False, False, False, True, False, False),
    (False, {"max": 4}, False, False, False, False, False, False, True, False),
    (False, {"min": -2, "max": 5}, False, False, False, False, False, True, True, False),
    (False, {"max": -2, "min": 5}, False, False, False, False, False, True, True, False),
    (False, {"units": "TST"}, False, False, False, False, False, False, False, True),
    (False, {"units": "TST", "min": -2, "max": 5}, False, False, False, False, False, True, True, True),
    (False, {}, False, True, False, False, False, True, False, False),
    (False, {"min": 1}, False, True, False, False, False, False, False, False),
    (False, {"max": 4}, False, True, False, False, False, True, True, False),
    (False, {"min": -2, "max": 5}, False, True, False, False, False, False, True, False),
    (False, {"max": -2, "min": 5}, False, True, False, False, False, False, True, False),
    (False, {"units": "TST"}, False, True, False, False, False, True, False, True),
    (False, {"units": "TST", "min": -2, "max": 5}, False, True, False, False, False, False, True, True),
    (False, {}, False, True, True, False, False, True, True, False),
    (False, {"min": 1}, False, True, True, False, False, False, True, False),
    (False, {"max": 4}, False, True, True, False, False, True, False, False),
    (False, {"min": -2, "max": 5}, False, True, True, False, False, False, False, False),
    (False, {"max": -2, "min": 5}, False, True, True, False, False, False, False, False),
    (False, {"units": "TST"}, False, True, True, False, False, True, True, True),
    (False, {"units": "TST", "min": -2, "max": 5}, False, True, True, False, False, False, False, True),
    (False, {}, False, False, False, True, False, False, False, True),
    (False, {"min": 1}, False, False, False, True, False, True, False, True),
    (False, {"max": 4}, False, False, False, True, False, False, True, True),
    (False, {"min": -2, "max": 5}, False, False, False, True, False, True, True, True),
    (False, {"max": -2, "min": 5}, False, False, False, True, False, True, True, True),
    (False, {"units": "TST"}, False, False, False, True, False, False, False, False),
    (False, {"units": "TST", "min": -2, "max": 5}, False, False, False, True, False, True, True, False),
    (False, {}, False, True, False, True, False, True, False, True),
    (False, {"min": 1}, False, True, False, True, False, False, False, True),
    (False, {"max": 4}, False, True, False, True, False, True, True, True),
    (False, {"min": -2, "max": 5}, False, True, False, True, False, False, True, True),
    (False, {"max": -2, "min": 5}, False, True, False, True, False, False, True, True),
    (False, {"units": "TST"}, False, True, False, True, False, True, False, False),
    (False, {"units": "TST", "min": -2, "max": 5}, False, True, False, True, False, False, True, False),
    (False, {}, False, False, True, True, False, False, True, True),
    (False, {"min": 1}, False, False, True, True, False, True, True, True),
    (False, {"max": 4}, False, False, True, True, False, False, False, True),
    (False, {"min": -2, "max": 5}, False, False, True, True, False, True, False, True),
    (False, {"max": -2, "min": 5}, False, False, True, True, False, True, False, True),
    (False, {"units": "TST"}, False, False, True, True, False, False, True, False),
    (False, {"units": "TST", "min": -2, "max": 5}, False, False, True, True, False, True, False, False),
    (False, {}, False, True, True, True, False, True, True, True),
    (False, {"min": 1}, False, True, True, True, False, False, True, True),
    (False, {"max": 4}, False, True, True, True, True, True, False, True),
    (False, {"min": -2, "max": 5}, False, True, True, True, False, False, False, True),
    (False, {"max": -2, "min": 5}, False, True, True, True, False, False, False, True),
    (False, {"units": "TST"}, False, True, True, True, False, True, True, False),
    (False, {"units": "TST", "min": -2, "max": 5}, False, True, True, True, False, False, False, False),
    (True, {}, False, False, False, True, False, False, False, True),
    (True, {"min": 1}, False, False, False, True, False, True, False, True),
    (True, {"max": 4}, False, False, False, True, False, False, True, True),
    (True, {"min": -2, "max": 5}, False, False, False, True, False, True, True, True),
    (True, {"max": -2, "min": 5}, False, False, False, True, False, True, True, True),
    (True, {"units": "TST"}, False, False, False, True, False, False, False, False),
    (True, {"units": "TST", "min": -2, "max": 5}, False, False, False, True, False, True, True, False),
    (True, {}, False, True, False, True, False, True, False, True),
    (True, {"min": 1}, False, True, False, True, False, False, False, True),
    (True, {"max": 4}, False, True, False, True, False, True, True, True),
    (True, {"min": -2, "max": 5}, False, True, False, True, False, False, True, True),
    (True, {"max": -2, "min": 5}, False, True, False, True, False, False, True, True),
    (True, {"units": "TST"}, False, True, False, True, False, True, False, False),
    (True, {"units": "TST", "min": -2, "max": 5}, False, True, False, True, False, False, True, False),
    (True, {}, False, False, False, False, False, False, False, False),
    (True, {"min": 1}, False, False, False, False, False, True, False, False),
    (True, {"max": 4}, False, False, False, False, False, False, True, False),
    (True, {"min": -2, "max": 5}, False, False, False, False, False, True, True, False),
    (True, {"max": -2, "min": 5}, False, False, False, False, False, True, True, False),
    (True, {"units": "TST"}, False, False, False, False, False, False, False, True),
    (True, {"units": "TST", "min": -2, "max": 5}, False, False, False, False, False, True, True, True),
    (True, {"precision": 3}, False, False, False, False, True, False, False, False),
    (True, {"units": "TST", "precision": 3}, False, False, False, False, True, False, False, True),
    (True, {"units": "TST", "precision": 3, "min": -2, "max": 5}, False, False, False, False, True, True, True, True),
])
def test_numeric_dialog_checkboxes_toggle_controls(qtbot: QtBot, use_precision, initial_data, toggle_prec, toggle_min,
                                                   toggle_max, toggle_unit, expect_prec_enabled, expect_min_enabled,
                                                   expect_max_enabled, expect_unit_enabled):
    widget = NumericFieldDialog(config=initial_data, use_precision=use_precision, on_save=mock.Mock())
    qtbot.add_widget(widget)
    if toggle_max:
        widget.chkbx_max.click()
    if toggle_min:
        widget.chkbx_min.click()
    if toggle_unit:
        widget.chkbx_units.click()
    if toggle_prec:
        widget.chkbx_precision.click()

    assert widget.min_spinbox.isEnabled() == expect_min_enabled
    assert widget.max_spinbox.isEnabled() == expect_max_enabled
    assert widget.units_line.isEnabled() == expect_unit_enabled
    if use_precision:
        assert widget.precision_spinbox.isEnabled() == expect_prec_enabled


@pytest.mark.parametrize("editable, button_name", [
    (True, "all_rw"),
    (False, "all_ro"),
])
def test_mark_all_editable(qtbot: QtBot, editable, button_name):
    initial_editable = [True, False, True]
    fields = []
    for idx, rw in enumerate(initial_editable):
        fields.append(PropertyEditField(field=f"f{idx}", type=PropertyEdit.ValueType.STRING, editable=rw))

    property_edit = mock_property_edit(fields)
    dialog = FieldsDialog(widget=property_edit)
    qtbot.add_widget(dialog)
    dialog.show()
    table_model = dialog.table.model()
    get_dialog_editables = lambda: [table_model.data(table_model.createIndex(row, 2))
                                    for row in range(table_model.rowCount())]
    actual_editable = get_dialog_editables()
    assert actual_editable == initial_editable
    getattr(dialog, button_name).click()
    expected_editable = [editable] * len(initial_editable)
    actual_editable = get_dialog_editables()
    assert actual_editable == expected_editable


@pytest.mark.parametrize("editable", [True, False])
@pytest.mark.parametrize("label", [None, "", "custom-label"])
@pytest.mark.parametrize("role", [Qt.DisplayRole, Qt.EditRole])
@pytest.mark.parametrize("row, column, expected_result", [
    (0, 0, "f1"),
    (0, 1, PropertyEdit.ValueType.INTEGER),
    (0, 2, lambda x: x),
    (0, 3, lambda x: x),
    (0, 4, None),
    (1, 0, "f2"),
    (1, 1, PropertyEdit.ValueType.REAL),
    (1, 2, lambda x: x),
    (1, 3, lambda x: x),
    (1, 4, None),
    (2, 0, "f3"),
    (2, 1, PropertyEdit.ValueType.BOOLEAN),
    (2, 2, lambda x: x),
    (2, 3, lambda x: x),
    (2, 4, None),
    (3, 0, "f4"),
    (3, 1, PropertyEdit.ValueType.STRING),
    (3, 2, lambda x: x),
    (3, 3, lambda x: x),
    (3, 4, None),
    (4, 0, "f5"),
    (4, 1, PropertyEdit.ValueType.ENUM),
    (4, 2, lambda x: x),
    (4, 3, lambda x: x),
    (4, 4, {"options": [("label", 1)]}),
])
def test_field_correct_item_values(row, column, role, editable, label, expected_result):
    data = [
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.INTEGER, editable=editable, label=label),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.REAL, editable=editable, label=label),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.BOOLEAN, editable=editable, label=label),
        PropertyEditField(field="f4", type=PropertyEdit.ValueType.STRING, editable=editable, label=label),
        PropertyEditField(field="f5", type=PropertyEdit.ValueType.ENUM, editable=editable, label=label, user_data={"options": [("label", 1)]}),
    ]
    model = FieldEditorTableModel(data)
    result = model.data(index=model.createIndex(row, column), role=role)
    if callable(expected_result):
        arg = editable if column == 2 else label
        assert result == expected_result(arg)
    else:
        assert result == expected_result


@pytest.mark.parametrize("editable", [True, False])
@pytest.mark.parametrize("row, column, role", [
    (-1, 0, Qt.DisplayRole),
    (0, -1, Qt.DisplayRole),
    (-1, -1, Qt.DisplayRole),
    (-1, 0, Qt.EditRole),
    (0, -1, Qt.EditRole),
    (-1, -1, Qt.EditRole),
    (0, 0, Qt.DecorationRole),
    (0, 0, Qt.ToolTipRole),
    (0, 0, Qt.StatusTipRole),
    (0, 0, Qt.WhatsThisRole),
    (0, 0, Qt.SizeHintRole),
])
def test_field_incorrect_item_values(row, column, role, editable):
    data = [
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.INTEGER, editable=editable),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.REAL, editable=editable),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.BOOLEAN, editable=editable),
        PropertyEditField(field="f4", type=PropertyEdit.ValueType.STRING, editable=editable),
        PropertyEditField(field="f5", type=PropertyEdit.ValueType.ENUM, editable=editable, user_data={"options": [("label", 1)]}),
    ]
    model = FieldEditorTableModel(data)
    result = model.data(index=model.createIndex(row, column), role=role)
    assert result == QVariant()


@pytest.mark.parametrize("role", [Qt.DisplayRole, Qt.EditRole])
@pytest.mark.parametrize("row, column, expected_result", [
    (0, 0, "label1"),
    (0, 1, 1),
    (1, 0, "label2"),
    (1, 1, 2),
    (2, 0, "label3"),
    (2, 1, 3),
])
def test_enum_correct_item_values(row, column, role, some_enum_config, expected_result):
    model = EnumEditorTableModel(some_enum_config)
    result = model.data(index=model.createIndex(row, column), role=role)
    assert result == expected_result


@pytest.mark.parametrize("row, column, role", [
    (-1, 0, Qt.DisplayRole),
    (0, -1, Qt.DisplayRole),
    (-1, -1, Qt.DisplayRole),
    (-1, 0, Qt.EditRole),
    (0, -1, Qt.EditRole),
    (-1, -1, Qt.EditRole),
    (0, 0, Qt.DecorationRole),
    (0, 0, Qt.ToolTipRole),
    (0, 0, Qt.StatusTipRole),
    (0, 0, Qt.WhatsThisRole),
    (0, 0, Qt.SizeHintRole),
])
def test_enum_incorrect_item_values(row, column, role, some_enum_config):
    model = EnumEditorTableModel(some_enum_config)
    result = model.data(index=model.createIndex(row, column), role=role)
    assert result == QVariant()
