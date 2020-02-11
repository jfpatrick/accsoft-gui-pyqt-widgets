import pytest
from pytestqt.qtbot import QtBot
from unittest import mock
from qtpy.QtCore import QVariant, Qt, QLocale
from qtpy.QtWidgets import QStyleOptionViewItem, QWidget, QPushButton, QAction
from PyQt5.QtTest import QAbstractItemModelTester
from accwidgets.property_edit.propedit import PropertyEdit, PropertyEditField, _pack_designer_fields
from accwidgets.property_edit.designer.designer_extensions import (
    qvariant_to_value_type,
    value_type_to_str,
    FieldsDialog,
    EnumOptionsDialog,
    EnumEditorTableModel,
    FieldEditorTableModel,
    PropertyFieldExtension,
    AbstractTableModel,
    UserDataColumnDelegate,
    FieldTypeColumnDelegate,
)


@pytest.fixture
def some_fields():
    return [
        PropertyEditField(field=f"f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field=f"f2", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field=f"f3", type=PropertyEdit.ValueType.STRING, editable=True),
    ]


@pytest.fixture
def some_enum_config():
    return [("label1", 1), ("label2", 2), ("label3", 3)]


@pytest.fixture
def abstract_model_impl():
    with mock.patch.multiple(AbstractTableModel, __abstractmethods__=set()):
        yield AbstractTableModel


@pytest.mark.parametrize("role", [Qt.DisplayRole, Qt.EditRole, Qt.DecorationRole, Qt.ToolTipRole, Qt.StatusTipRole, Qt.WhatsThisRole, Qt.SizeHintRole])
def test_abstract_table_model_flags(abstract_model_impl, role):
    assert abstract_model_impl([]).flags(role) == Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable


@pytest.mark.parametrize("data", [
    [],
    [1],
    [1, 2, 3],
])
def test_abstract_table_model_row_count(abstract_model_impl, data):
    assert abstract_model_impl(data).rowCount() == len(data)


@pytest.mark.parametrize("role, orientation, section, expected_label", [
    (Qt.DisplayRole, Qt.Horizontal, 0, "real_section_name"),
    (Qt.DisplayRole, Qt.Horizontal, 1, ""),
    (Qt.DisplayRole, Qt.Vertical, 0, "1"),
    (Qt.DisplayRole, Qt.Vertical, 1, "2"),
    (Qt.DisplayRole, Qt.Vertical, 2, "3"),
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
def test_abstract_table_model_header_data(abstract_model_impl, role, orientation, section, expected_label):
    model = abstract_model_impl([1, 2, 3])
    with mock.patch.object(model, "column_name", return_value="real_section_name"):
        with mock.patch.object(model, "columnCount", return_value=1):
            actual_label = model.headerData(section, orientation, role)
            assert actual_label == expected_label


@pytest.mark.parametrize("row, column, role, expected_result", [
    (0, 0, Qt.DisplayRole, "real-0-0"),
    (0, 1, Qt.DisplayRole, QVariant()),
    (-1, 0, Qt.DisplayRole, QVariant()),
    (4, 0, Qt.DisplayRole, QVariant()),
    (0, 0, Qt.EditRole, "real-0-0"),
    (0, 1, Qt.EditRole, QVariant()),
    (-1, 0, Qt.EditRole, QVariant()),
    (4, 0, Qt.EditRole, QVariant()),
    (0, 0, Qt.ToolTipRole, QVariant()),
    (0, 1, Qt.ToolTipRole, QVariant()),
    (-1, 0, Qt.ToolTipRole, QVariant()),
    (4, 0, Qt.ToolTipRole, QVariant()),
])
def test_abstract_table_model_data(abstract_model_impl, row, column, role, expected_result):
    def callback(idx):
        return f"real-{idx.row()}-{idx.column()}"

    model = abstract_model_impl([1, 2, 3])
    with mock.patch.object(model, "columnCount", return_value=1):
        with mock.patch.object(model, "data_at_index", side_effect=callback):
            actual_data = model.data(model.createIndex(row, column), role)
            assert actual_data == expected_result


@pytest.mark.parametrize("row, column, role, expected_success", [
    (0, 0, Qt.DisplayRole, False),
    (0, 1, Qt.DisplayRole, False),
    (-1, 0, Qt.DisplayRole, False),
    (4, 0, Qt.DisplayRole, False),
    (0, 0, Qt.EditRole, True),
    (0, 1, Qt.EditRole, False),
    (-1, 0, Qt.EditRole, False),
    (4, 0, Qt.EditRole, False),
    (0, 0, Qt.ToolTipRole, False),
    (0, 1, Qt.ToolTipRole, False),
    (-1, 0, Qt.ToolTipRole, False),
    (4, 0, Qt.ToolTipRole, False),
])
def test_abstract_table_model_set_data(abstract_model_impl, row, column, role, expected_success):
    model = abstract_model_impl([1, 2, 3])
    with mock.patch.object(model, "columnCount", return_value=1):
        with mock.patch.object(model, "update_data_at_index", return_value=1) as mocked_method:
            actual_success = model.setData(model.createIndex(row, column), "test_val", role)
            assert actual_success == expected_success
            if expected_success:
                mocked_method.assert_called_once()
            else:
                mocked_method.assert_not_called()


def test_abstract_table_model_raw_data(abstract_model_impl):
    assert abstract_model_impl([1, 2, 3]).raw_data == [1, 2, 3]


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
        qtbot.addWidget(property_edit)
        property_edit.show()
        dialog = FieldsDialog(widget=property_edit)
        qtbot.addWidget(dialog)
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
        qtbot.addWidget(property_edit)
        ext = PropertyFieldExtension(property_edit)
        assert len(ext.actions()) == 1
        act = ext.actions()[0]
        act.activate(QAction.Trigger)
        show_mock.assert_called_once()
        exec_mock.assert_called_once()


@pytest.mark.parametrize("row, expected_type, check_slot", [
    (0, QWidget, False),
    (1, QPushButton, False),
])
def test_setup_enums(qtbot: QtBot, expected_type, row, check_slot):
    config = [
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.ENUM, editable=True),
    ]

    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(config)
        property_edit = PropertyEdit()
        qtbot.addWidget(property_edit)
        dialog = FieldsDialog(widget=property_edit)
        qtbot.addWidget(dialog)
        dialog.show()
        dialog.table.selectRow(row)
        user_data_column = 4
        delegate = dialog.table.itemDelegateForColumn(user_data_column)
        # dialog.table.selectionModel().select(dialog.table.model().createIndex(0, 4), QItemSelectionModel.Select)
        index = dialog.table.model().createIndex(row, user_data_column)
        with mock.patch.object(delegate, "_open_editor") as mocked_slot:
            widget = delegate.createEditor(parent=property_edit, option=QStyleOptionViewItem(), index=index)
            assert isinstance(widget, expected_type)
            if check_slot:
                widget.click()
                mocked_slot.assert_called_with(row)


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
        qtbot.addWidget(property_edit)
        dialog = FieldsDialog(widget=property_edit)
        qtbot.addWidget(dialog)
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


def test_enum_dialog_disabled_buttons(qtbot: QtBot, some_enum_config):
    dialog = EnumOptionsDialog(options=some_enum_config, on_save=lambda _: None)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False
    dialog.add_btn.click()
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False
    dialog.table.selectRow(0)
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is True
    for _ in range(len(some_enum_config) + 1):
        dialog.table.selectRow(0)
        dialog.remove_btn.click()
    assert dialog.add_btn.isEnabled() is True
    assert dialog.remove_btn.isEnabled() is False


@mock.patch("qtpy.QtWidgets.QMessageBox.warning")
def test_field_dialog_warning_on_invalid_data(mocked_warning, qtbot: QtBot):
    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields([])
        property_edit = PropertyEdit()
        qtbot.addWidget(property_edit)
        dialog = FieldsDialog(widget=property_edit)
        qtbot.addWidget(dialog)
        dialog.show()

        def side_effect():
            raise Exception("test")

        with mock.patch.object(dialog.table.model(), "validate", side_effect=side_effect):
            dialog.buttons.accepted.emit()
            mocked_warning.assert_called_with(dialog, "Invalid data", "test")


@mock.patch("qtpy.QtWidgets.QMessageBox.warning")
def test_enum_dialog_warning_on_invalid_data(mocked_warning, some_enum_config, qtbot: QtBot):
    dialog = EnumOptionsDialog(options=some_enum_config, on_save=lambda _: None)
    qtbot.addWidget(dialog)
    dialog.show()

    def side_effect():
        raise Exception("test")

    with mock.patch.object(dialog.table.model(), "validate", side_effect=side_effect):
        dialog.buttons.accepted.emit()
        mocked_warning.assert_called_with(dialog, "Invalid data", "test")


def test_enum_dialog_before_save(qtbot: QtBot, some_enum_config):
    my_mock = mock.Mock()
    dialog = EnumOptionsDialog(options=some_enum_config, on_save=my_mock)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.buttons.accepted.emit()
    my_mock.assert_called_once()


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
    [("label1", 0)],
    [("label1", -1)],
    [("label1", 999)],
    [("label1", 0), ("label2", 1)],
])
def test_enum_config_validate_succeeds(data):
    model = EnumEditorTableModel(data=data)
    model.validate()


@pytest.mark.parametrize("initial_config, expected_value", [
    ([], 0),
    ([("label1", 0)], 1),
    ([("label1", 0), ("label2", 1)], 2),
    ([("label1", 10), ("label2", 1)], 11),
])
def test_enum_default_value_increases(initial_config, expected_value):
    model = EnumEditorTableModel(data=initial_config)
    model.append()
    last_value = model.raw_data[-1][1]
    assert last_value == expected_value


@pytest.mark.parametrize("data", [
    [],
    [("label1", 0)],
    [("label1", -1)],
    [("label1", 999)],
    [("label1", 0), ("label2", 1)],
])
def test_enum_model(data):
    model = EnumEditorTableModel(data=data)
    _ = QAbstractItemModelTester(model)


@pytest.mark.parametrize("data, error_msg", [
    ([("", 0)], r'Row #1 is lacking "Label".'),
    ([("label1", 0), ("", 1)], r'Row #2 is lacking "Label".'),
    ([(None, 0)], r'Row #1 is lacking "Label".'),
    ([("label1", 0), ("label2", 0)], r'Enum value "0" is being used more than once.'),
    ([("label1", 0), ("label1", 1)], r'Label value "label1" is being used more than once.'),
    ([("label1", 0), ("label1", 0)], r'(Enum value "0" is being used more than once.)|(Label value "label1" is being used more than once.)'),
    ([("label1", 0), (None, 0)], r'(Row #2 is lacking "Label".)|(Enum value "0" is being used more than once.)'),
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
        qtbot.addWidget(property_edit)
        dialog = FieldsDialog(widget=property_edit)
        qtbot.addWidget(dialog)
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


def test_field_table_append(qtbot: QtBot, some_fields):
    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(some_fields)
        property_edit = PropertyEdit()
        qtbot.addWidget(property_edit)
        dialog = FieldsDialog(widget=property_edit)
        qtbot.addWidget(dialog)
        dialog.show()
        table_model = dialog.table.model()
        initial_fields = [x.field for x in some_fields]
        get_dialog_field_names = lambda: [table_model.data(table_model.createIndex(row, 0))
                                          for row in range(table_model.rowCount())]
        actual_fields = get_dialog_field_names()
        assert actual_fields == initial_fields
        dialog.add_btn.click()
        expected_fields = [*initial_fields, ""]
        actual_fields = get_dialog_field_names()
        assert actual_fields == expected_fields


def test_field_table_remove_last(qtbot: QtBot, some_fields):
    with mock.patch("accwidgets.property_edit.PropertyEdit.fields", new_callable=mock.PropertyMock) as mock_prop:
        # Because designer always expects JSON, we need to "pack" it.
        # We also cannot simply assign it to the ``fields``, because they will be unpacked internally.
        mock_prop.return_value = _pack_designer_fields(some_fields)
        property_edit = PropertyEdit()
        qtbot.addWidget(property_edit)
        dialog = FieldsDialog(widget=property_edit)
        qtbot.addWidget(dialog)
        dialog.show()
        table_model = dialog.table.model()
        initial_fields = [x.field for x in some_fields]
        get_dialog_field_names = lambda: [table_model.data(table_model.createIndex(row, 0))
                                          for row in range(table_model.rowCount())]
        actual_fields = get_dialog_field_names()
        assert actual_fields == initial_fields
        dialog.table.selectRow(len(some_fields) - 1)
        dialog.remove_btn.click()
        expected_fields = initial_fields[:-1]
        actual_fields = get_dialog_field_names()
        assert actual_fields == expected_fields
        dialog.table.selectRow(0)
        dialog.remove_btn.click()
        expected_fields.pop(0)
        actual_fields = get_dialog_field_names()
        assert actual_fields == expected_fields


def test_enum_table_append(qtbot: QtBot, some_enum_config):
    dialog = EnumOptionsDialog(options=some_enum_config, on_save=lambda _: None)
    qtbot.addWidget(dialog)
    dialog.show()
    table_model = dialog.table.model()
    initial_options = [x[0] for x in some_enum_config]
    get_dialog_names = lambda: [table_model.data(table_model.createIndex(row, 0))
                                for row in range(table_model.rowCount())]
    actual_options = get_dialog_names()
    assert actual_options == initial_options
    dialog.add_btn.click()
    expected_options = [*initial_options, ""]
    actual_options = get_dialog_names()
    assert actual_options == expected_options


def test_enum_table_remove_last(qtbot: QtBot, some_enum_config):
    dialog = EnumOptionsDialog(options=some_enum_config, on_save=lambda _: None)
    qtbot.addWidget(dialog)
    dialog.show()
    table_model = dialog.table.model()
    initial_options = [x[0] for x in some_enum_config]
    get_dialog_names = lambda: [table_model.data(table_model.createIndex(row, 0))
                                for row in range(table_model.rowCount())]
    actual_options = get_dialog_names()
    assert actual_options == initial_options
    dialog.table.selectRow(len(some_enum_config) - 1)
    dialog.remove_btn.click()
    expected_options = initial_options[:-1]
    actual_options = get_dialog_names()
    assert actual_options == expected_options
    dialog.table.selectRow(0)
    dialog.remove_btn.click()
    expected_options.pop(0)
    actual_options = get_dialog_names()
    assert actual_options == expected_options


@pytest.mark.parametrize("row, column, value, expected_data", [
    (0, 0, "test", ("test", 1)),
    (0, 1, 99, ("one", 99)),
    (1, 0, "test", ("test", 2)),
    (1, 1, 99, ("two", 99)),
])
def test_enum_table_update_data(row, column, value, expected_data):
    model = EnumEditorTableModel([("one", 1), ("two", 2)])
    res = model.update_data_at_index(model.createIndex(row, column), value)
    assert res == expected_data


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
    (0, 10, Qt.DisplayRole),
    (10, 0, Qt.DisplayRole),
    (10, 10, Qt.DisplayRole),
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
    (0, 10, Qt.DisplayRole),
    (10, 0, Qt.DisplayRole),
    (10, 10, Qt.DisplayRole),
])
def test_enum_incorrect_item_values(row, column, role, some_enum_config):
    model = EnumEditorTableModel(some_enum_config)
    result = model.data(index=model.createIndex(row, column), role=role)
    assert result == QVariant()


@pytest.mark.parametrize("value, expected_text", [
    (None, ""),
    ("", ""),
    ("sdf", ""),
    ({}, ""),
    ({"options": []}, ""),
    ({"options": [("one", 1)]}, "1 option"),
    ({"options": [("one", 1), ("two", 2)]}, "2 options"),
    ({"options": [("one", 1), ("two", 2), ("three", 3)]}, "3 options"),
])
def test_user_data_column_display_text(value, expected_text):
    delegate = UserDataColumnDelegate()
    actual_text = delegate.displayText(value, QLocale())
    assert actual_text == expected_text


@pytest.mark.parametrize("row, column, expected_index", [
    (0, 1, 4),
    (1, 1, 5),
])
def test_type_column_set_editor_data_succeeds(row, column, expected_index):
    config = [
        PropertyEditField(field="f1", type=PropertyEdit.ValueType.STRING, editable=True),
        PropertyEditField(field="f2", type=PropertyEdit.ValueType.ENUM, editable={"options": [("one", 1), ("two", 2)]}),
    ]
    model = FieldEditorTableModel(config)
    delegate = FieldTypeColumnDelegate()
    editor = mock.MagicMock()
    editor.findData.side_effect = lambda x: PropertyEdit.ValueType(x)
    index = model.createIndex(row, column)
    delegate.setEditorData(editor=editor, index=index)
    editor.setCurrentIndex.assert_called_with(expected_index)


def test_type_column_set_editor_data_warns(some_fields):
    model = FieldEditorTableModel(some_fields)
    delegate = FieldTypeColumnDelegate()
    editor = mock.MagicMock()
    index = model.createIndex(0, 0)
    with mock.patch.object(editor, "findData", return_value=-1):
        with pytest.warns(UserWarning, match=r"Can't find the option for the combobox to set"):
            delegate.setEditorData(editor=editor, index=index)
            editor.setCurrentIndex.assert_not_called()


def test_type_column_set_model_data(some_fields):
    model = FieldEditorTableModel(some_fields)
    delegate = FieldTypeColumnDelegate()
    editor = mock.MagicMock()
    editor.currentData.return_value = 99
    index = model.createIndex(0, 0)
    with mock.patch.object(model, "setData") as mocked_method:
        delegate.setModelData(editor=editor, index=index, model=model)
        mocked_method.assert_called_with(index, 99, Qt.EditRole)


@pytest.mark.parametrize("value, expected_text", [
    (1, "Integer"),
    (2, "Real"),
    (3, "Boolean"),
    (4, "String"),
    (5, "Enum"),
])
def test_type_column_display_text(value, expected_text):
    delegate = FieldTypeColumnDelegate()
    actual_text = delegate.displayText(value, QLocale())
    assert actual_text == expected_text


@pytest.mark.parametrize("val, expected_type", [
    (1, PropertyEdit.ValueType.INTEGER),
    (2, PropertyEdit.ValueType.REAL),
    (3, PropertyEdit.ValueType.BOOLEAN),
    (4, PropertyEdit.ValueType.STRING),
    (5, PropertyEdit.ValueType.ENUM),
    (QVariant(1), PropertyEdit.ValueType.INTEGER),
    (QVariant(2), PropertyEdit.ValueType.REAL),
    (QVariant(3), PropertyEdit.ValueType.BOOLEAN),
    (QVariant(4), PropertyEdit.ValueType.STRING),
    (QVariant(5), PropertyEdit.ValueType.ENUM),
    (PropertyEdit.ValueType.INTEGER, PropertyEdit.ValueType.INTEGER),
    (PropertyEdit.ValueType.REAL, PropertyEdit.ValueType.REAL),
    (PropertyEdit.ValueType.BOOLEAN, PropertyEdit.ValueType.BOOLEAN),
    (PropertyEdit.ValueType.STRING, PropertyEdit.ValueType.STRING),
    (PropertyEdit.ValueType.ENUM, PropertyEdit.ValueType.ENUM),
    (QVariant(PropertyEdit.ValueType.INTEGER), PropertyEdit.ValueType.INTEGER),
    (QVariant(PropertyEdit.ValueType.REAL), PropertyEdit.ValueType.REAL),
    (QVariant(PropertyEdit.ValueType.BOOLEAN), PropertyEdit.ValueType.BOOLEAN),
    (QVariant(PropertyEdit.ValueType.STRING), PropertyEdit.ValueType.STRING),
    (QVariant(PropertyEdit.ValueType.ENUM), PropertyEdit.ValueType.ENUM),
])
def test_qvariant_to_value(val, expected_type):
    assert qvariant_to_value_type(val) == expected_type


@pytest.mark.parametrize("val, expected_str", [
    (PropertyEdit.ValueType.INTEGER, "Integer"),
    (PropertyEdit.ValueType.REAL, "Real"),
    (PropertyEdit.ValueType.BOOLEAN, "Boolean"),
    (PropertyEdit.ValueType.STRING, "String"),
    (PropertyEdit.ValueType.ENUM, "Enum"),
])
def test_value_to_str(val, expected_str):
    assert value_type_to_str(val) == expected_str
