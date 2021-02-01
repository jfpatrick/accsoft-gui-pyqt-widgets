import pytest
from pytestqt.qtbot import QtBot
from unittest import mock
from qtpy.QtCore import QVariant, Qt
from qtpy.QtWidgets import QStyleOptionViewItem, QAction, QPushButton, QDialogButtonBox, QFormLayout
from PyQt5.QtTest import QAbstractItemModelTester
from accwidgets.property_edit.propedit import PropertyEdit, PropertyEditField, _pack_designer_fields
from accwidgets.property_edit.designer.designer_extensions import (
    FieldsDialog,
    EnumEditorTableModel,
    FieldEditorTableModel,
    PropertyFieldExtension,
    EnumTableData,
    NumericFieldDialog,
)


@pytest.fixture
def some_fields():
    return [
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.STRING, editable=True),
    ]


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
    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(fields)
        property_edit = PropertyEdit()
        qtbot.add_widget(property_edit)
        property_edit.show()
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        dialog.show()
        dialog._save()
        find_form_mock().cursor().setProperty.assert_called_with("fields", expected_string)


@mock.patch("accwidgets.property_edit.designer.designer_extensions.FieldsDialog.show")
@mock.patch("accwidgets.property_edit.designer.designer_extensions.FieldsDialog.exec_")
def test_edit_contents_opens_dialog(show_mock, exec_mock, qtbot: QtBot):
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
        exec_mock.assert_called_once()


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

    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(config)
        property_edit = PropertyEdit()
        qtbot.add_widget(property_edit)
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
def test_user_data_event(opt_dialog, qtbot: QtBot, row, handles_dbl_click, handles_single_click, editor_options):
    config = [
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.ENUM, editable=True),
        PropertyEditField(field="f3", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={}),
        PropertyEditField(field="f4", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": []}),
        PropertyEditField(field="f5", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": [(1, "test1")]}),
        PropertyEditField(field="f6", type=PropertyEdit.ValueType.ENUM, editable=True, user_data={"options": [(1, "test1"), (2, "test2")]}),
    ]

    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(config)
        property_edit = PropertyEdit()
        qtbot.add_widget(property_edit)
        dialog = FieldsDialog(widget=property_edit)
        qtbot.add_widget(dialog)
        dialog.show()
        user_data_column = 4
        delegate = dialog.table.itemDelegateForColumn(user_data_column)
        index = dialog.table.model().createIndex(row, user_data_column)
        editor = delegate.createEditor(dialog.table, QStyleOptionViewItem(), index)
        assert isinstance(editor, QPushButton)
        editor.click()
        opt_dialog.assert_called_once_with(options=editor_options, on_save=mock.ANY)
        opt_dialog.return_value.exec_.assert_called_once()


@pytest.mark.parametrize("initial_fields, initial_enabled", [
    ([
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.STRING, editable=True),
    ], True),
    ([], False),
])
def test_field_dialog_disabled_buttons(qtbot: QtBot, initial_fields, initial_enabled):
    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(initial_fields)
        property_edit = PropertyEdit()
        qtbot.add_widget(property_edit)
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

    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(fields)
        property_edit = PropertyEdit()
        qtbot.add_widget(property_edit)
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
