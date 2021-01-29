import pytest
from pytestqt.qtbot import QtBot
from unittest import mock
from qtpy.QtCore import QVariant, Qt
from qtpy.QtWidgets import QStyleOptionViewItem, QAction, QPushButton
from PyQt5.QtTest import QAbstractItemModelTester
from accwidgets.property_edit.propedit import PropertyEdit, PropertyEditField, _pack_designer_fields
from accwidgets.property_edit.designer.designer_extensions import (
    FieldsDialog,
    EnumEditorTableModel,
    FieldEditorTableModel,
    PropertyFieldExtension,
    EnumTableData,
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
