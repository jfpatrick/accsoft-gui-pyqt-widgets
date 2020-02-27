import pytest
from typing import cast
from pytestqt.qtbot import QtBot
from unittest import mock
from qtpy.QtWidgets import (QFormLayout, QVBoxLayout, QHBoxLayout, QGroupBox, QFrame, QLabel, QDoubleSpinBox,
                            QSpinBox, QComboBox, QLineEdit, QCheckBox, QWidget)
from PyQt5.QtTest import QSignalSpy  # TODO: qtpy does not seem to expose QSignalSpy: https://github.com/spyder-ide/qtpy/issues/197
from accwidgets.property_edit.propedit import (PropertyEdit, PropertyEditField, PropertyEditWidgetDelegate,
                                               _unpack_designer_fields, _pack_designer_fields, PropertyEditFormLayoutDelegate,
                                               AbstractPropertyEditWidgetDelegate, AbstractPropertyEditLayoutDelegate,
                                               _QtDesignerButtons, _QtDesignerDecoration, _QtDesignerButtonPosition)
from accwidgets.led import Led


@pytest.mark.parametrize("field", ["f1", "", None])
@pytest.mark.parametrize("value_type", [PropertyEdit.ValueType.REAL, 2, None, 0])
@pytest.mark.parametrize("editable", [True, False, None])
@pytest.mark.parametrize("label", ["l1", "", None])
@pytest.mark.parametrize("user_data", [{}, {"key": "val"}, None])
def test_property_edit_field_init(field, value_type, editable, label, user_data):
    obj = PropertyEditField(field=field, type=value_type, editable=editable, label=label, user_data=user_data)
    assert obj.field == field
    assert obj.type == value_type
    assert obj.editable == editable
    assert obj.label == label
    assert obj.user_data == user_data


@pytest.mark.parametrize("api_flags, designer_enum", [
    (PropertyEdit.Buttons.GET, _QtDesignerButtons.Get),
    (PropertyEdit.Buttons.SET, _QtDesignerButtons.Set),
    (PropertyEdit.Buttons.GET & PropertyEdit.Buttons.SET, _QtDesignerButtons.Neither),
    (PropertyEdit.Buttons.GET | PropertyEdit.Buttons.SET, _QtDesignerButtons.Both),
    (PropertyEdit.ButtonPosition.RIGHT, _QtDesignerButtonPosition.Right),
    (PropertyEdit.ButtonPosition.BOTTOM, _QtDesignerButtonPosition.Bottom),
    (PropertyEdit.Decoration.FRAME, _QtDesignerDecoration.Frame),
    (PropertyEdit.Decoration.GROUP_BOX, _QtDesignerDecoration.GroupBox),
    (PropertyEdit.Decoration.NONE, _QtDesignerDecoration.Empty),
])
def test_designer_enums(api_flags, designer_enum):
    assert api_flags == designer_enum


@pytest.mark.parametrize("options, result", [
    ([("test", 2)], {"options": [("test", 2)]}),
    ([("test2", 2), ("test3", 3)], {"options": [("test2", 2), ("test3", 3)]}),
    ([], {"options": []}),
])
def test_enum_user_data(options, result):
    assert PropertyEdit.ValueType.enum_user_data(options) == result


@pytest.mark.parametrize("value, expected_values", [
    ({"str": "str", "int": 2, "bool": True, "float": 0.5, "enum": 4}, ["str", 2, True, 0.5, 4]),
    ({"str": "str", "int": 2, "bool": True, "float": 0.5, "enum": 4, "nonexising": "fake_news"}, ["str", 2, True, 0.5, 4]),
    ({"str": "str", "int": 2}, ["str", 2, None, None, None]),
    ({"str": "str", "bool": True}, ["str", None, True, None, None]),
    ({}, [None, None, None, None, None]),
])
@pytest.mark.parametrize("fields", [
    [
        (PropertyEditField(field="str", type=PropertyEdit.ValueType.STRING, editable=False), "text"),
        (PropertyEditField(field="int", type=PropertyEdit.ValueType.INTEGER, editable=False), "text"),
        (PropertyEditField(field="bool", type=PropertyEdit.ValueType.BOOLEAN, editable=False), None),
        (PropertyEditField(field="float", type=PropertyEdit.ValueType.REAL, editable=False), "text"),
        (PropertyEditField(field="enum", type=PropertyEdit.ValueType.ENUM, editable=False, user_data=PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)])), "text"),
    ],
    [
        (PropertyEditField(field="str", type=PropertyEdit.ValueType.STRING, editable=True), "text"),
        (PropertyEditField(field="int", type=PropertyEdit.ValueType.INTEGER, editable=True), "value"),
        (PropertyEditField(field="bool", type=PropertyEdit.ValueType.BOOLEAN, editable=True), "isChecked"),
        (PropertyEditField(field="float", type=PropertyEdit.ValueType.REAL, editable=True), "value"),
        (PropertyEditField(field="enum", type=PropertyEdit.ValueType.ENUM, editable=True, user_data=PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)])), "currentData"),
    ],
])
def test_set_value(qtbot: QtBot, value, expected_values, fields):
    config, getters = tuple(zip(*fields))  # Split list of tuple into tuple of lists
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.fields = config
    widget.setValue(value)
    assert widget._widget_layout.rowCount() == len(config)
    for idx, expected_value, getter, conf in zip(range(len(getters)), expected_values, getters, config):
        if getter is None:
            continue
        inner_widget = widget._widget_layout.itemAt(idx, QFormLayout.FieldRole).widget()
        displayed_value = getattr(inner_widget, getter)()
        if expected_value is None:
            assert not displayed_value
        else:
            expected_type = type(expected_value)
            if conf.type == PropertyEdit.ValueType.ENUM and not conf.editable:
                expected_value = [tp[0] for tp in conf.user_data["options"] if tp[1] == expected_value][0]
                expected_type = str
            assert expected_type(displayed_value) == expected_value


@pytest.mark.parametrize("setting, get_enabled, set_enabled", [
    (PropertyEdit.Buttons.GET & PropertyEdit.Buttons.SET, False, False),
    (PropertyEdit.Buttons.GET, True, False),
    (PropertyEdit.Buttons.SET, False, True),
    (PropertyEdit.Buttons.GET | PropertyEdit.Buttons.SET, True, True),
])
def test_buttons(qtbot: QtBot, setting, get_enabled, set_enabled):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()  # Needed for visibility of the child widgets to be correct

    # Buttons should be invisible by default
    assert widget.buttons == PropertyEdit.Buttons.GET & PropertyEdit.Buttons.SET
    assert not widget._get_btn.isVisible()
    assert not widget._set_btn.isVisible()

    widget.buttons = setting

    assert widget._get_btn.isVisible() == get_enabled
    assert widget._set_btn.isVisible() == set_enabled


@pytest.mark.parametrize("settings", [[
    (PropertyEdit.ButtonPosition.BOTTOM, QVBoxLayout, 1, 2),
    (PropertyEdit.ButtonPosition.RIGHT, QHBoxLayout, 0, 1),
    (PropertyEdit.ButtonPosition.BOTTOM, QVBoxLayout, 1, 2),
]])
def test_button_position(qtbot: QtBot, settings):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()

    assert widget.buttonPosition == PropertyEdit.ButtonPosition.BOTTOM
    assert isinstance(widget._layout, QVBoxLayout)

    for setting, layout_type, get_btn_idx, set_btn_idx in settings:
        widget.buttonPosition = setting
        assert isinstance(widget._layout, layout_type)

        # Checks that vertical layout has spacer to center the buttons
        assert set_btn_idx < widget._button_box.count()
        assert widget._button_box.itemAt(get_btn_idx).widget() == widget._get_btn
        assert widget._button_box.itemAt(set_btn_idx).widget() == widget._set_btn


@pytest.mark.parametrize("setting, expected_msg", [
    (99, r"Unsupported button position value 99"),
])
def test_button_position_warns(qtbot: QtBot, setting, expected_msg):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()

    with pytest.warns(UserWarning, match=expected_msg):
        widget.buttonPosition = setting


@pytest.mark.parametrize("setting, container_type", [
    (PropertyEdit.Decoration.NONE, None),
    (PropertyEdit.Decoration.GROUP_BOX, QGroupBox),
    (PropertyEdit.Decoration.FRAME, QFrame),
])
def test_decoration(qtbot: QtBot, setting, container_type):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()

    assert widget.decoration == PropertyEdit.Decoration.NONE
    assert widget._decoration is None
    assert widget._layout == widget.layout()
    widget.decoration = setting
    assert widget.decoration == setting
    if container_type is None:
        assert widget._decoration is None
    else:
        assert isinstance(widget._decoration, container_type)
    container = widget if widget._decoration is None else widget._decoration
    assert container.layout() == widget._layout


def test_decoration_replace_existing(qtbot: QtBot):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()
    widget.decoration = PropertyEdit.Decoration.GROUP_BOX
    assert widget._decoration is not None
    container = widget._decoration
    assert container.layout() == widget._layout

    # Now reset to nothing
    widget.decoration = PropertyEdit.Decoration.NONE
    assert widget._decoration is None
    assert widget._layout == widget.layout()


@pytest.mark.parametrize("setting, expected_msg", [
    (99, "Unsupported decoration value 99"),
])
def test_decoration_warns(qtbot: QtBot, setting, expected_msg):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()

    assert widget.decoration == PropertyEdit.Decoration.NONE
    assert widget._decoration is None
    assert widget._layout == widget.layout()
    with pytest.warns(UserWarning, match=expected_msg):
        widget.decoration = setting
    assert widget.decoration == setting
    assert widget._decoration is None
    assert widget._layout == widget.layout()


def test_title(qtbot: QtBot):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()
    widget.decoration = PropertyEdit.Decoration.GROUP_BOX
    assert not widget.title
    assert not cast(QGroupBox, widget._decoration).title()
    new_val = "My title"
    widget.title = new_val
    assert widget.title == new_val
    assert cast(QGroupBox, widget._decoration).title() == new_val


@pytest.mark.parametrize("config, expected_widgets", [(
    [
        (PropertyEditField(field="str", label="label1", type=PropertyEdit.ValueType.STRING, editable=False)),
        (PropertyEditField(field="int", label="label2", type=PropertyEdit.ValueType.INTEGER, editable=False)),
        (PropertyEditField(field="bool", label="label3", type=PropertyEdit.ValueType.BOOLEAN, editable=False)),
        (PropertyEditField(field="float", label="label4", type=PropertyEdit.ValueType.REAL, editable=False)),
        (PropertyEditField(field="enum", label="label5", type=PropertyEdit.ValueType.ENUM, editable=False, user_data=PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)]))),
    ], [
        (QLabel, "text", "label1"),
        (QLabel, "text", "label2"),
        (Led, "_get_status", "label3"),
        (QLabel, "text", "label4"),
        (QLabel, "text", "label5"),
    ],
), (
    [
        (PropertyEditField(field="str", type=PropertyEdit.ValueType.STRING, editable=False)),
        (PropertyEditField(field="int", type=PropertyEdit.ValueType.INTEGER, editable=False)),
        (PropertyEditField(field="bool", type=PropertyEdit.ValueType.BOOLEAN, editable=False)),
        (PropertyEditField(field="float", type=PropertyEdit.ValueType.REAL, editable=False)),
        (PropertyEditField(field="enum", type=PropertyEdit.ValueType.ENUM, editable=False, user_data=PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)]))),
    ], [
        (QLabel, "text", "str"),
        (QLabel, "text", "int"),
        (Led, "_get_status", "bool"),
        (QLabel, "text", "float"),
        (QLabel, "text", "enum"),
    ],
), (
    [
        (PropertyEditField(field="str", type=PropertyEdit.ValueType.STRING, editable=True)),
        (PropertyEditField(field="int", type=PropertyEdit.ValueType.INTEGER, editable=True)),
        (PropertyEditField(field="bool", type=PropertyEdit.ValueType.BOOLEAN, editable=True)),
        (PropertyEditField(field="float", type=PropertyEdit.ValueType.REAL, editable=True)),
        (PropertyEditField(field="enum", type=PropertyEdit.ValueType.ENUM, editable=True, user_data=PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)]))),
    ], [
        (QLineEdit, "text", "str"),
        (QSpinBox, "value", "int"),
        (QCheckBox, "isChecked", "bool"),
        (QDoubleSpinBox, "value", "float"),
        (QComboBox, "currentText", "enum"),
    ],
), (
    "["
    '  {"field": "str", "type": 4, "rw": false},'
    '  {"field": "int", "type": 1, "rw": false},'
    '  {"field": "bool", "type": 3, "rw": false},'
    '  {"field": "float", "type": 2, "rw": false},'
    '  {"field": "enum", "type": 5, "rw": false, "ud": {'
    '      "options": ['
    '          ["none", 0],'
    '          ["one", 4],'
    '          ["two", 5]'
    "      ]"
    "   }}"
    "]",
    [
        (QLabel, "text", "str"),
        (QLabel, "text", "int"),
        (Led, "_get_status", "bool"),
        (QLabel, "text", "float"),
        (QLabel, "text", "enum"),
    ],
), (
    "["
    '  {"field": "str", "type": 4, "rw": true},'
    '  {"field": "int", "type": 1, "rw": true},'
    '  {"field": "bool", "type": 3, "rw": true},'
    '  {"field": "float", "type": 2, "rw": true},'
    '  {"field": "enum", "type": 5, "rw": true, "ud": {'
    '      "options": ['
    '          ["none", 0],'
    '          ["one", 4],'
    '          ["two", 5]'
    "      ]"
    "   }}"
    "]",
    [
        (QLineEdit, "text", "str"),
        (QSpinBox, "value", "int"),
        (QCheckBox, "isChecked", "bool"),
        (QDoubleSpinBox, "value", "float"),
        (QComboBox, "currentText", "enum"),
    ],
)])
def test_fields(qtbot: QtBot, config, expected_widgets):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.show()
    widget.fields = config
    assert widget._widget_layout.rowCount() == len(expected_widgets)
    widget.setValue({
        "str": "val1",
        "int": 10,
        "bool": True,
        "float": 0.5,
        "enum": 4,
    })
    expected_widget_values = ["val1", 10, True, 0.5, "one"]
    indexes = range(len(expected_widgets))
    separated_lists = list(zip(*expected_widgets))
    combined_iter = zip(indexes, *separated_lists, expected_widget_values)
    for idx, widget_type, getter, expected_label, expected_value in combined_iter:
        label_widget = widget._widget_layout.itemAt(idx, QFormLayout.LabelRole).widget()
        assert isinstance(label_widget, QLabel)
        inner_widget = widget._widget_layout.itemAt(idx, QFormLayout.FieldRole).widget()
        assert isinstance(inner_widget, widget_type)
        displayed_value = getattr(inner_widget, getter)()
        expected_type = type(expected_value)
        assert label_widget.text() == expected_label
        assert expected_type(displayed_value) == expected_value


@pytest.mark.parametrize("send_only_updated, str_input_val, expected_val", [
    (True, "val1", {}),
    (True, "val2", {"str": "val2"}),
    (False, "val1", {"str": "val1", "int": 10, "bool": True, "float": 0.5}),
    (False, "val2", {"str": "val2", "int": 10, "bool": True, "float": 0.5}),
])
def test_send_only_updated_set(qtbot: QtBot, send_only_updated, str_input_val, expected_val):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.sendOnlyUpdatedValues = send_only_updated
    widget.fields = [
        (PropertyEditField(field="str", type=PropertyEdit.ValueType.STRING, editable=True)),
        (PropertyEditField(field="int", type=PropertyEdit.ValueType.INTEGER, editable=True)),
        (PropertyEditField(field="bool", type=PropertyEdit.ValueType.BOOLEAN, editable=False)),
        (PropertyEditField(field="float", type=PropertyEdit.ValueType.REAL, editable=False)),
    ]
    widget.setValue({
        "str": "val1",
        "int": 10,
        "bool": True,
        "float": 0.5,
        "unconfigured": "unconfigured-value",  # Should not be sent. We don't want hidden values being sent.
    })
    widget.findChild(QLineEdit).setText(str_input_val)
    spy = QSignalSpy(widget.valueUpdated)
    widget._set_btn.click()
    value_updated_spy = spy[0]
    received_val = value_updated_spy[0]
    assert received_val == expected_val


def test_get_btn(qtbot: QtBot):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    spy = QSignalSpy(widget.valueRequested)
    assert len(spy) == 0
    widget._get_btn.click()
    assert len(spy) == 1
    assert len(spy[0]) == 0


def test_set_btn(qtbot: QtBot):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.fields = [
        PropertyEditField(field="test", type=PropertyEdit.ValueType.STRING, editable=True),
    ]
    spy = QSignalSpy(widget.valueUpdated)
    assert len(spy) == 0
    widget._set_btn.click()
    assert len(spy) == 1
    value_updated_spy = spy[0]
    assert len(value_updated_spy) == 1
    received_val = value_updated_spy[0]
    assert received_val == {"test": ""}


def test_widget_delegate():

    class MyCustomDelegate(AbstractPropertyEditWidgetDelegate):
        """Testing subclassing"""

        def create_widget(self, *args, **kwargs):
            return QLabel()

        def display_data(self, *args, **kwargs):
            pass

        def send_data(self, *args, **kwargs):
            return 1

    delegate = MyCustomDelegate()
    assert delegate.read_value(True) == {}


def test_layout_delegate():

    class MyCustomDelegate(AbstractPropertyEditLayoutDelegate[QVBoxLayout]):
        """Testing subclassing"""

        def create_layout(self) -> QVBoxLayout:
            return QVBoxLayout()

        def layout_widgets(self, *args, **kwargs):
            pass


def test_abstract_delegate_widget_for_item_recreates_expired_weakref(qtbot: QtBot):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    dangling_widget = delegate.widget_for_item(parent=None,  # By setting parent to None, we leave it dangling
                                               config=PropertyEditField(field="test",
                                                                        type=PropertyEdit.ValueType.STRING,
                                                                        editable=False))
    assert "test" in delegate.widget_map
    delegate.widget_map["test"] = (lambda: None), None  # type: ignore # Pretend we have deleted weakref (lambda returning None)

    # This should create a new one, since dangling_widget should be missing by now
    new_widget = delegate.widget_for_item(parent=widget,
                                          config=PropertyEditField(field="test",
                                                                   type=PropertyEdit.ValueType.STRING,
                                                                   editable=False))
    assert new_widget != dangling_widget

    # This should NOT create a new one, since the widget should stay the same
    another_widget = delegate.widget_for_item(parent=widget,
                                              config=PropertyEditField(field="test",
                                                                       type=PropertyEdit.ValueType.STRING,
                                                                       editable=False))
    assert another_widget == new_widget


def test_abstract_delegate_widget_for_item(qtbot: QtBot):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    with mock.patch.object(delegate, "create_widget", return_value=QLabel()) as mocked_method:
        _ = delegate.widget_for_item(parent=widget,
                                     config=PropertyEditField(field="test",
                                                              type=PropertyEdit.ValueType.STRING,
                                                              editable=False))
        mocked_method.assert_called_once()
        mocked_method.reset_mock()
        mocked_method.assert_not_called()
        _ = delegate.widget_for_item(parent=widget,
                                     config=PropertyEditField(field="test",
                                                              type=PropertyEdit.ValueType.STRING,
                                                              editable=False))
        mocked_method.assert_not_called()


def test_abstract_delegate_value_updated_not_called_for_expired_weakref(qtbot: QtBot):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    delegate.widget_map["test"] = (lambda: None), None  # type: ignore # Pretend we have deleted weakref (lambda returning None)

    with mock.patch.object(delegate, "display_data") as mocked_method:
        with pytest.warns(UserWarning, match=r"Won't be displaying data on deleted weak reference"):
            delegate.value_updated({
                "test": "new_val",
            })
            mocked_method.assert_not_called()


@pytest.mark.parametrize("configured_field_id, updated_field_id, should_be_called", [
    ("test", "non_existing", False),
    ("test", "test", True),
])
def test_abstract_delegate_value_updated(qtbot: QtBot, configured_field_id, updated_field_id, should_be_called):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    _ = delegate.widget_for_item(parent=widget,
                                 config=PropertyEditField(field=configured_field_id,
                                                          type=PropertyEdit.ValueType.STRING,
                                                          editable=False))
    with mock.patch.object(delegate, "display_data") as mocked_method:
        delegate.value_updated({
            updated_field_id: "new_val",
        })
        if should_be_called:
            mocked_method.assert_called_once()
        else:
            mocked_method.assert_not_called()


def test_abstract_delegate_read_value_not_called_for_expired_weakref(qtbot: QtBot):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    delegate.widget_map["test"] = (lambda: None), None  # type: ignore # Pretend we have deleted weakref (lambda returning None)

    with mock.patch.object(delegate, "send_data") as mocked_method:
        with pytest.warns(UserWarning, match=r"Won't be sending data from deleted weak reference"):
            delegate.read_value(False)
            mocked_method.assert_not_called()


@pytest.mark.parametrize("send_only_updated, editable, should_be_called", [
    (True, True, True),
    (False, True, True),
    (True, False, False),
    (False, False, True),
])
def test_abstract_delegate_read_value(qtbot: QtBot, send_only_updated, editable, should_be_called):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    _ = delegate.widget_for_item(parent=widget,
                                 config=PropertyEditField(field="test",
                                                          type=PropertyEdit.ValueType.STRING,
                                                          editable=editable))
    with mock.patch.object(delegate, "send_data") as mocked_method:
        # Not called for read-only fields in send_only_updated mode
        delegate.read_value(send_only_updated)
        if should_be_called:
            mocked_method.assert_called_once()
        else:
            mocked_method.assert_not_called()


@pytest.mark.parametrize("editable, value_type, expected_widget_type", [
    (False, PropertyEdit.ValueType.INTEGER, QLabel),
    (False, PropertyEdit.ValueType.REAL, QLabel),
    (False, PropertyEdit.ValueType.BOOLEAN, Led),
    (False, PropertyEdit.ValueType.STRING, QLabel),
    (False, PropertyEdit.ValueType.ENUM, QLabel),
    (True, PropertyEdit.ValueType.INTEGER, QSpinBox),
    (True, PropertyEdit.ValueType.REAL, QDoubleSpinBox),
    (True, PropertyEdit.ValueType.BOOLEAN, QCheckBox),
    (True, PropertyEdit.ValueType.STRING, QLineEdit),
    (True, PropertyEdit.ValueType.ENUM, QComboBox),
])
def test_delegate_create_widget(qtbot: QtBot, editable, value_type, expected_widget_type):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    new_widget = delegate.widget_for_item(parent=widget,
                                          config=PropertyEditField(field="test",
                                                                   type=value_type,
                                                                   editable=editable))
    assert isinstance(new_widget, expected_widget_type)


@pytest.mark.parametrize("editable, value_type, sent_value, expected_method_call, expected_method_arg, property_mock", [
    (False, PropertyEdit.ValueType.INTEGER, 2, "setNum", 2, False),
    (False, PropertyEdit.ValueType.REAL, 2.5, "setNum", 2.5, False),
    (False, PropertyEdit.ValueType.BOOLEAN, True, "status", Led.Status.ON, True),
    (False, PropertyEdit.ValueType.STRING, "val", "setText", "val", False),
    (False, PropertyEdit.ValueType.ENUM, 4, "setText", "one", False),
    (False, PropertyEdit.ValueType.ENUM, (4, "custom-text"), "setText", "custom-text", False),
    (True, PropertyEdit.ValueType.INTEGER, 2, "setValue", 2, False),
    (True, PropertyEdit.ValueType.REAL, 2.5, "setValue", 2.5, False),
    (True, PropertyEdit.ValueType.BOOLEAN, True, "setChecked", True, False),
    (True, PropertyEdit.ValueType.STRING, "val", "setText", "val", False),
    (True, PropertyEdit.ValueType.ENUM, 4, "setCurrentIndex", 1, False),
    (True, PropertyEdit.ValueType.ENUM, (4, "custom-text"), "setCurrentIndex", 1, False),
])
def test_delegate_display_data(qtbot: QtBot, editable, value_type, sent_value, expected_method_call, expected_method_arg, property_mock):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    ud = PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)])  # user_data is ignored by all except enums
    new_widget = delegate.widget_for_item(parent=widget,
                                          config=PropertyEditField(field="test",
                                                                   type=value_type,
                                                                   editable=editable,
                                                                   user_data=ud))
    assert hasattr(new_widget, expected_method_call)
    with mock.patch(f"{new_widget.__class__.__module__}.{new_widget.__class__.__qualname__}.{expected_method_call}",
                    new_callable=mock.PropertyMock if property_mock else mock.MagicMock) as mocked_method:
        qtbot.addWidget(new_widget)
        delegate.display_data(field_id="test", value=sent_value, item_type=value_type, user_data=ud, widget=new_widget)
        mocked_method.assert_called_once_with(expected_method_arg)


@pytest.mark.parametrize("editable, value_type, sent_value, expected_msg", [
    (False, PropertyEdit.ValueType.ENUM, 99, r"Can't set data 99 to QLabel. Unexpected enum value received."),
    (True, PropertyEdit.ValueType.ENUM, 99, r"Can't set data 99 to QComboBox. Unexpected enum value received."),
    (False, PropertyEdit.ValueType.ENUM, {}, r"Can't set data {} to QLabel. Unexpected enum value received."),
    (True, PropertyEdit.ValueType.ENUM, {}, r"Can't set data {} to QComboBox. Unexpected enum value received."),
    (False, PropertyEdit.ValueType.ENUM, (0,), r"Can't set data \(0,\) to QLabel. Unexpected enum value received."),
    (True, PropertyEdit.ValueType.ENUM, (0,), r"Can't set data \(0,\) to QComboBox. Unexpected enum value received."),
    (False, PropertyEdit.ValueType.ENUM, [0, "label"], r"Can't set data \[0, 'label'\] to QLabel. Unexpected enum value received."),
    (True, PropertyEdit.ValueType.ENUM, [0, "label"], r"Can't set data \[0, 'label'\] to QComboBox. Unexpected enum value received."),
    (False, PropertyEdit.ValueType.INTEGER, {}, r"Can't set data {} to QLabel. Unsupported data type."),
    (False, PropertyEdit.ValueType.REAL, {}, r"Can't set data {} to QLabel. Unsupported data type."),
    (False, PropertyEdit.ValueType.STRING, {}, r"Can't set data {} to QLabel. Unsupported data type."),
])
def test_delegate_display_data_warns(qtbot: QtBot, editable, value_type, sent_value, expected_msg):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    ud = PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)])  # user_data is ignored by all except enums
    new_widget = delegate.widget_for_item(parent=widget,
                                          config=PropertyEditField(field="test",
                                                                   type=value_type,
                                                                   editable=editable,
                                                                   user_data=ud))
    with pytest.warns(UserWarning, match=expected_msg):
        delegate.display_data(field_id="test", value=sent_value, item_type=value_type, user_data=ud, widget=new_widget)


@pytest.mark.parametrize("editable, value_type, sent_value, expected_method_call, expected_method_return_val", [
    (False, PropertyEdit.ValueType.INTEGER, 2, "text", 2),
    (False, PropertyEdit.ValueType.REAL, 2.5, "text", 2.5),
    (False, PropertyEdit.ValueType.BOOLEAN, True, None, True),
    (False, PropertyEdit.ValueType.STRING, "val", "text", "val"),
    (False, PropertyEdit.ValueType.ENUM, 4, "text", 4),
    (True, PropertyEdit.ValueType.INTEGER, 2, "value", 2),
    (True, PropertyEdit.ValueType.REAL, 2.5, "value", 2.5),
    (True, PropertyEdit.ValueType.BOOLEAN, True, "isChecked", True),
    (True, PropertyEdit.ValueType.STRING, "val", "text", "val"),
    (True, PropertyEdit.ValueType.ENUM, 4, "currentData", 4),
])
def test_delegate_send_data(qtbot: QtBot, editable, value_type, sent_value, expected_method_call, expected_method_return_val):
    delegate = PropertyEditWidgetDelegate()
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.widget_delegate = delegate
    ud = PropertyEdit.ValueType.enum_user_data([("none", 0), ("one", 4), ("two", 5)])  # user_data is ignored by all except enums
    new_widget = delegate.widget_for_item(parent=widget,
                                          config=PropertyEditField(field="test",
                                                                   type=value_type,
                                                                   editable=editable,
                                                                   user_data=ud))
    delegate.value_updated({
        "test": sent_value,
    })
    res = delegate.send_data(field_id="test", user_data=ud, widget=new_widget, item_type=value_type)
    assert res == expected_method_return_val
    if expected_method_call is None:
        return
    assert hasattr(new_widget, expected_method_call)
    with mock.patch.object(new_widget, expected_method_call) as mocked_method:
        delegate.send_data(field_id="test", user_data=ud, widget=new_widget, item_type=value_type)
        if isinstance(new_widget, QLabel):
            # Label should never be retrieved value from. We use cache dictionary instead
            mocked_method.assert_not_called()
        else:
            mocked_method.assert_called_once()


@pytest.mark.parametrize("input, fields", [
    ('[{"field": "f1", "type": 1, "rw": false}]', [("f1", PropertyEdit.ValueType.INTEGER, False, None, None)]),
    ('[{"field": "f1", "type": 1, "rw": true}]', [("f1", PropertyEdit.ValueType.INTEGER, True, None, None)]),
    ('[{"field": "f1", "type": 2, "rw": true}]', [("f1", PropertyEdit.ValueType.REAL, True, None, None)]),
    ('[{"field": "f1", "type": 3, "rw": true}]', [("f1", PropertyEdit.ValueType.BOOLEAN, True, None, None)]),
    ('[{"field": "f1", "type": 4, "rw": true}]', [("f1", PropertyEdit.ValueType.STRING, True, None, None)]),
    ('[{"field": "f1", "type": 5, "rw": true}]', [("f1", PropertyEdit.ValueType.ENUM, True, None, None)]),
    ('[{"field": "f1", "type": 1, "rw": true, "label": "l1"}]', [("f1", PropertyEdit.ValueType.INTEGER, True, "l1", None)]),
    ('[{"field": "f1", "type": 1, "rw": true, "label": null}]', [("f1", PropertyEdit.ValueType.INTEGER, True, None, None)]),
    ('[{"field": "f1", "type": 1, "rw": true, "ud": null}]', [("f1", PropertyEdit.ValueType.INTEGER, True, None, None)]),
    ('[{"field": "f1", "type": 1, "rw": true, "ud": {"key": "val"}}]', [("f1", PropertyEdit.ValueType.INTEGER, True, None, {"key": "val"})]),
    ('[{"field": "f1", "type": 1, "rw": true, "label": "l1", "ud": null}]', [("f1", PropertyEdit.ValueType.INTEGER, True, "l1", None)]),
    ('[{"field": "f1", "type": 1, "rw": true, "label": "l1", "ud": {"key": "val"}}]', [("f1", PropertyEdit.ValueType.INTEGER, True, "l1", {"key": "val"})]),
    ('[{"field": "f1", "type": 1, "rw": true, "label": "l1"}, {"field": "f2", "type": 2, "rw": true}]', [("f1", PropertyEdit.ValueType.INTEGER, True, "l1", None), ("f2", PropertyEdit.ValueType.REAL, True, None, None)]),
])
def test_unpack_fields_succeeds(input, fields):
    deserialized = _unpack_designer_fields(input)
    assert len(deserialized) == len(fields)
    for actual, expected in zip(deserialized, fields):
        field, value_type, editable, label, user_data = expected
        assert actual.field == field
        assert actual.type == value_type
        assert actual.editable == editable
        assert actual.label == label
        assert actual.user_data == user_data


@pytest.mark.parametrize("input, is_warning, error_type, error_msg", [
    ('[{"list"', True, UserWarning, r"Failed to decode json:.*$"),
    ("{}", True, UserWarning, r"Decoded fields is not a list$"),
    ('{"field": "f1", "type": 1, "rw": false}', True, UserWarning, r"Decoded fields is not a list$"),
    ('[{"type": 1, "rw": false}]', False, KeyError, r"field"),
    ('[{"field": "f1", "rw": false}]', False, KeyError, r"type"),
    ('[{"field": "f1", "type": 1, "label": "l1"}]', False, KeyError, r"rw"),
    ('[{"field": "f1", "type": 0, "label": "l1"}]', False, ValueError, r"0 is not a valid ValueType"),
])
def test_unpack_fields_fails(input, is_warning, error_type, error_msg):
    trap = pytest.warns if is_warning else pytest.raises
    with trap(error_type, match=error_msg):
        res = _unpack_designer_fields(input)
        if is_warning:
            assert res == []


@pytest.mark.parametrize("value_type, expected_type", [
    (PropertyEdit.ValueType.INTEGER, 1),
    (PropertyEdit.ValueType.REAL, 2),
    (PropertyEdit.ValueType.BOOLEAN, 3),
    (PropertyEdit.ValueType.STRING, 4),
    (PropertyEdit.ValueType.ENUM, 5),
])
@pytest.mark.parametrize("editable", [True, False])
@pytest.mark.parametrize("label, extra_label_kwargs", [
    ("my-label", {"label": "my-label"}),
    ("", {}),
    (None, {}),
])
@pytest.mark.parametrize("user_data, extra_ud_kwargs", [
    ({"options": [("enum1", 1), ("enum2", 2)]}, {"ud": {"options": [("enum1", 1), ("enum2", 2)]}}),
    ({"options": []}, {"ud": {"options": []}}),
    ({}, {}),
    (None, {}),
])
@pytest.mark.parametrize("repeat", [0, 1, 2])
def test_pack_fields(value_type,
                     expected_type,
                     editable,
                     user_data,
                     extra_ud_kwargs,
                     label,
                     extra_label_kwargs,
                     repeat):
    input = []
    expected = []
    for _ in range(repeat):
        obj = PropertyEditField(field="my-field",
                                type=value_type,
                                editable=editable,
                                label=label,
                                user_data=user_data)
        input.append(obj)
        json_obj = {
            "field": "my-field",
            "type": expected_type,
            "rw": editable,
            **extra_ud_kwargs,
            **extra_label_kwargs,
        }
        expected.append(json_obj)

    with mock.patch("json.dumps", side_effect=lambda obj: obj):
        assert _pack_designer_fields(input) == expected


@pytest.mark.parametrize("config, expected_call_cnt", [
    ([
        (PropertyEditField(field="str", type=PropertyEdit.ValueType.STRING, editable=True)),
        (PropertyEditField(field="int", type=PropertyEdit.ValueType.INTEGER, editable=True)),
    ], 2),
    ([], 0),
])
def test_default_layout_delegate_calls_widget_delegate_create_method(qtbot: QtBot, config, expected_call_cnt):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    widget.fields = config
    widget_delegate = widget.widget_delegate
    layout_delegate = widget.layout_delegate
    with mock.patch.object(widget_delegate, "create_widget", return_value=QWidget()) as mocked_method:
        layout_delegate.layout_widgets(layout=layout_delegate.create_layout(),
                                       widget_config=config,
                                       parent=widget,
                                       create_widget=mocked_method)
        assert len(mocked_method.mock_calls) == expected_call_cnt


def test_layout_delegate_setter_updates_layout_on_new_delegate(qtbot: QtBot):
    widget = PropertyEdit()
    qtbot.addWidget(widget)

    assert widget._layout.children()[1] == widget._button_box
    assert widget._layout.children()[0] == widget._widget_layout
    orig_widget_layout = widget._layout.children()[0]

    widget.layout_delegate = PropertyEditFormLayoutDelegate()
    assert widget._layout.children()[1] == widget._button_box
    assert widget._layout.children()[0] != orig_widget_layout
    assert widget._layout.children()[0] == widget._widget_layout
    assert isinstance(widget._layout.children()[0], type(widget.layout_delegate.create_layout()))


def test_layout_delegate_setter_does_not_updates_layout_on_same_delegate(qtbot: QtBot):
    widget = PropertyEdit()
    qtbot.addWidget(widget)

    assert widget._layout.children()[1] == widget._button_box
    assert widget._layout.children()[0] == widget._widget_layout
    orig_widget_layout = widget._layout.children()[0]

    existing_delegate = widget.layout_delegate
    widget.layout_delegate = existing_delegate
    assert widget._layout.children()[1] == widget._button_box
    assert widget._layout.children()[0] == orig_widget_layout
    assert widget._layout.children()[0] == widget._widget_layout


def test_initial_layout_is_form(qtbot: QtBot):
    widget = PropertyEdit()
    qtbot.addWidget(widget)
    assert isinstance(widget._widget_layout, QFormLayout)
