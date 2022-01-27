from .fixtures import *  # noqa: F401,F403
import pytest
import sys
import numpy as np
from unittest import mock
from typing import cast, List
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QStyleOptionViewItem, QWidget, QCheckBox
from qtpy.QtGui import QPalette, QColor
from accwidgets.qt import ColorButton
from accwidgets.log_console import LogLevel, LogConsoleFormatter
from accwidgets.log_console._prefs_dialog import (ModelConfiguration, ColorTableModelItem, ColorTableModel,
                                                  LoggerTableModel, LoggerTableModelItem, LevelComboboxColumnDelegate,
                                                  LogPreferencesDialog, ViewConfiguration, FmtConfiguration)


@pytest.mark.parametrize("buffer_size,expect_size_ok", [
    (-1, False),
    (0, False),
    (1, True),
    (2, True),
    (555, True),
    (sys.maxsize, True),
    (np.nan, False),
])
@pytest.mark.parametrize("visible_levels,expect_levels_ok", [
    (set(), True),
    ({LogLevel.DEBUG}, True),
    ({LogLevel.DEBUG, LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING, LogLevel.INFO}, True),
    ({LogLevel.NOTSET}, False),
    ({LogLevel.ERROR, LogLevel.NOTSET}, False),
])
@pytest.mark.parametrize("selected_levels,available_levels,expect_selected_levels_ok", [
    ({}, {}, True),
    ({}, {"one": LogLevel.DEBUG}, False),
    ({"one": LogLevel.DEBUG}, {"one": LogLevel.DEBUG}, True),
    ({"one": LogLevel.DEBUG}, {"one": LogLevel.DEBUG, "two": LogLevel.INFO}, False),
    ({"one": LogLevel.DEBUG}, {}, False),
    ({"one": LogLevel.DEBUG}, {"two": LogLevel.INFO}, False),
    ({"one": LogLevel.DEBUG, "two": LogLevel.INFO}, {"one": LogLevel.DEBUG}, False),
])
@pytest.mark.parametrize("notice,expect_notice_ok", [
    (None, True),
    (("test notice", True), True),
    (("test notice", False), True),
    ((), False),
    (("test notice",), False),
    ("test notice", False),
])
def test_prefs_dialog_model_config_validate(buffer_size, visible_levels, selected_levels, available_levels, notice,
                                            expect_levels_ok, expect_notice_ok, expect_selected_levels_ok, expect_size_ok):
    config = ModelConfiguration(buffer_size=buffer_size,
                                visible_levels=visible_levels,
                                selected_logger_levels=selected_levels,
                                available_logger_levels=available_levels,
                                notice=notice)

    expected_error_message = None
    if not expect_levels_ok:
        expected_error_message = "Visible levels cannot contain NOTSET value"
    elif not expect_size_ok:
        expected_error_message = "Buffer size must be positive finite value, greater than 0"
    elif not expect_selected_levels_ok:
        expected_error_message = "selected_logger_levels and available_logger_levels must have the same keys"
    elif not expect_notice_ok:
        expected_error_message = "notice must be a tuple"

    if expected_error_message is None:
        config.validate()
    else:
        with pytest.raises(ValueError, match=expected_error_message):
            config.validate()


@pytest.mark.parametrize("column_idx,expected_column_name", [
    (0, "Color"),
    (1, "Invert"),
    (2, ""),
])
@pytest.mark.parametrize("levels,row_idx,expected_row_name", [
    (list(LogLevel.real_levels()), 0, " DEBUG"),
    (list(LogLevel.real_levels()), 1, " INFO"),
    (list(LogLevel.real_levels()), 2, " WARNING"),
    (list(LogLevel.real_levels()), 3, " ERROR"),
    (list(LogLevel.real_levels()), 4, " CRITICAL"),
    ([LogLevel.INFO, LogLevel.ERROR], 0, " INFO"),
    ([LogLevel.INFO, LogLevel.ERROR], 1, " ERROR"),
    ([LogLevel.INFO, LogLevel.ERROR], 2, ""),
])
def test_prefs_dialog_color_table_model_headers(column_idx, levels, row_idx, expected_column_name, expected_row_name):
    data = [ColorTableModelItem(level=level, color="", invert=False) for level in levels]
    model = ColorTableModel(data=data)
    assert model.columnCount() == 2
    assert model.headerData(column_idx, Qt.Horizontal) == expected_column_name
    assert model.headerData(row_idx, Qt.Vertical) == expected_row_name


@pytest.mark.parametrize("data,row,column,expected_data", [
    ([], 0, 0, None),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True)], 0, 0, "#cecece"),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True)], 0, 1, True),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 0, 0, "#cecece"),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 0, 1, True),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 1, 0, "#ff0000"),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 1, 1, False),
])
def test_prefs_dialog_color_table_model_get_cell_data(data, row, column, expected_data):
    model = ColorTableModel(data=data)
    index = model.createIndex(row, column)
    assert model.data(index) == expected_data


@pytest.mark.parametrize("data,row,column,set_data,check_attr,expect_set_succeeds", [
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True)], 0, 0, "#fbfbfb", "color", True),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True)], 0, 1, False, "invert", True),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True)], 0, 2, None, None, False),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 0, 0, "#fbfbfb", "color", True),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 0, 1, False, "invert", True),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 1, 0, "#232323", "color", True),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True),
      ColorTableModelItem(level=LogLevel.ERROR, color="#ff0000", invert=False)], 1, 1, True, "invert", True),
])
def test_prefs_dialog_color_table_model_set_cell_data(data, row, column, set_data, check_attr, expect_set_succeeds):
    model = ColorTableModel(data=data)
    index = model.createIndex(row, column)
    assert model.setData(index, set_data) == expect_set_succeeds
    if expect_set_succeeds:
        item = data[row]
        assert getattr(item, check_attr) == set_data


@pytest.mark.parametrize("column", [0, -1, 1])
@pytest.mark.parametrize("data,row", [
    ([], 0),
    ([ColorTableModelItem(level=LogLevel.INFO, color="#cecece", invert=True)], 1),
])
def test_prefs_dialog_color_table_model_set_cell_data_fails(data, row, column):
    model = ColorTableModel(data=data)
    index = model.createIndex(row, 0)
    with pytest.raises(IndexError):
        assert model.setData(index, "anything")


@pytest.mark.parametrize("column_idx,expected_column_name", [
    (0, "Logger levels"),
    (1, ""),
])
@pytest.mark.parametrize("names,row_idx,expected_row_name", [
    ([], 0, ""),
    (["logger1"], 0, " logger1"),
    (["logger1"], 1, ""),
    (["logger1", "logger2"], 0, " logger1"),
    (["logger1", "logger2"], 1, " logger2"),
    (["logger1", "logger2"], 2, ""),
])
def test_prefs_dialog_logger_table_model_headers(names, column_idx, row_idx, expected_row_name, expected_column_name):
    data = [LoggerTableModelItem(name=name, available_levels=set(), selected_level=LogLevel.DEBUG) for name in names]
    model = LoggerTableModel(data=data)
    assert model.columnCount() == 1
    assert model.headerData(column_idx, Qt.Horizontal) == expected_column_name
    assert model.headerData(row_idx, Qt.Vertical) == expected_row_name


@pytest.mark.parametrize("column", [0, 1])
@pytest.mark.parametrize("data,row", [
    ([LoggerTableModelItem(name="name", available_levels=set(), selected_level=LogLevel.DEBUG)], 0),
    ([LoggerTableModelItem(name="name1", available_levels=set(), selected_level=LogLevel.DEBUG),
      LoggerTableModelItem(name="name2", available_levels=set(), selected_level=LogLevel.INFO)], 0),
    ([LoggerTableModelItem(name="name1", available_levels=set(), selected_level=LogLevel.DEBUG),
      LoggerTableModelItem(name="name2", available_levels=set(), selected_level=LogLevel.INFO)], 1),
])
def test_prefs_dialog_logger_table_model_get_cell_data(data, row, column):
    model = LoggerTableModel(data=data)
    index = model.createIndex(row, column)
    assert model.data(index) == data[row]


@pytest.mark.parametrize("data,row,set_data", [
    ([LoggerTableModelItem(name="name", available_levels={LogLevel.DEBUG, LogLevel.INFO}, selected_level=LogLevel.DEBUG)], 0, LogLevel.INFO),
    ([LoggerTableModelItem(name="name1", available_levels={LogLevel.DEBUG, LogLevel.INFO}, selected_level=LogLevel.DEBUG),
      LoggerTableModelItem(name="name2", available_levels={LogLevel.DEBUG, LogLevel.INFO}, selected_level=LogLevel.INFO)], 0, LogLevel.INFO),
    ([LoggerTableModelItem(name="name1", available_levels={LogLevel.DEBUG, LogLevel.ERROR}, selected_level=LogLevel.DEBUG),
      LoggerTableModelItem(name="name2", available_levels={LogLevel.DEBUG, LogLevel.ERROR}, selected_level=LogLevel.ERROR)], 1, LogLevel.DEBUG),
])
def test_prefs_dialog_logger_table_model_set_cell_data(data, row, set_data):
    model = LoggerTableModel(data=data)
    index = model.createIndex(row, 0)
    assert model.setData(index, set_data) is True
    assert model.data(index).selected_level == set_data


@pytest.mark.parametrize("available_levels", [
    set(LogLevel.real_levels()),
    {LogLevel.INFO},
    {LogLevel.INFO, LogLevel.ERROR},
    {},
])
def test_prefs_dialog_level_combobox_renders_available_levels_only(qtbot: QtBot, available_levels):
    try:
        selected_level = list(available_levels)[0]
    except IndexError:
        selected_level = LogLevel.INFO
    item = LoggerTableModelItem(name="logger", available_levels=available_levels, selected_level=selected_level)
    model = LoggerTableModel(data=[item])
    parent_widget = QWidget()
    qtbot.add_widget(parent_widget)
    index = model.createIndex(0, 0)
    delegate = LevelComboboxColumnDelegate()
    combobox = cast(QComboBox, delegate.createEditor(parent_widget, QStyleOptionViewItem(), index))
    delegate.setEditorData(combobox, index)
    assert combobox.count() == len(available_levels)
    actual_options = {(combobox.itemText(idx), combobox.itemData(idx)) for idx in range(combobox.count())}
    expected_options = {(LogLevel.level_name(level), level.value) for level in available_levels}
    assert actual_options == expected_options


@pytest.mark.parametrize("available_levels,selected_level,expected_selected_option,expected_selected_data", [
    (set(LogLevel.real_levels()), LogLevel.DEBUG, "DEBUG", LogLevel.DEBUG.value),
    (set(LogLevel.real_levels()), LogLevel.INFO, "INFO", LogLevel.INFO.value),
    (set(LogLevel.real_levels()), LogLevel.WARNING, "WARNING", LogLevel.WARNING.value),
    (set(LogLevel.real_levels()), LogLevel.ERROR, "ERROR", LogLevel.ERROR.value),
    (set(LogLevel.real_levels()), LogLevel.CRITICAL, "CRITICAL", LogLevel.CRITICAL.value),
    ({LogLevel.INFO}, LogLevel.INFO, "INFO", LogLevel.INFO.value),
    ({LogLevel.INFO, LogLevel.ERROR}, LogLevel.INFO, "INFO", LogLevel.INFO.value),
    ({LogLevel.INFO, LogLevel.ERROR}, LogLevel.ERROR, "ERROR", LogLevel.ERROR.value),
    ({}, LogLevel.INFO, "", None),
])
def test_prefs_dialog_level_combobox_selected_option(qtbot: QtBot, available_levels, selected_level, expected_selected_option,
                                                     expected_selected_data):
    item = LoggerTableModelItem(name="logger", available_levels=available_levels, selected_level=selected_level)
    model = LoggerTableModel(data=[item])
    parent_widget = QWidget()
    qtbot.add_widget(parent_widget)
    index = model.createIndex(0, 0)
    delegate = LevelComboboxColumnDelegate()
    combobox = cast(QComboBox, delegate.createEditor(parent_widget, QStyleOptionViewItem(), index))
    delegate.setEditorData(combobox, index)
    assert combobox.currentText() == expected_selected_option
    assert combobox.currentData() == expected_selected_data


@pytest.mark.parametrize("available_levels,selected_level,new_level,expected_model_update", [
    (set(LogLevel.real_levels()), LogLevel.DEBUG, "DEBUG", LogLevel.DEBUG),
    (set(LogLevel.real_levels()), LogLevel.DEBUG, "INFO", LogLevel.INFO),
    (set(LogLevel.real_levels()), LogLevel.DEBUG, "WARNING", LogLevel.WARNING),
    (set(LogLevel.real_levels()), LogLevel.DEBUG, "ERROR", LogLevel.ERROR),
    (set(LogLevel.real_levels()), LogLevel.DEBUG, "CRITICAL", LogLevel.CRITICAL),
    (set(LogLevel.real_levels()), LogLevel.INFO, "INFO", LogLevel.INFO),
    (set(LogLevel.real_levels()), LogLevel.INFO, "DEBUG", LogLevel.DEBUG),
    (set(LogLevel.real_levels()), LogLevel.INFO, "WARNING", LogLevel.WARNING),
    (set(LogLevel.real_levels()), LogLevel.INFO, "ERROR", LogLevel.ERROR),
    (set(LogLevel.real_levels()), LogLevel.INFO, "CRITICAL", LogLevel.CRITICAL),
    (set(LogLevel.real_levels()), LogLevel.WARNING, "WARNING", LogLevel.WARNING),
    (set(LogLevel.real_levels()), LogLevel.WARNING, "DEBUG", LogLevel.DEBUG),
    (set(LogLevel.real_levels()), LogLevel.WARNING, "INFO", LogLevel.INFO),
    (set(LogLevel.real_levels()), LogLevel.WARNING, "ERROR", LogLevel.ERROR),
    (set(LogLevel.real_levels()), LogLevel.WARNING, "CRITICAL", LogLevel.CRITICAL),
    (set(LogLevel.real_levels()), LogLevel.ERROR, "ERROR", LogLevel.ERROR),
    (set(LogLevel.real_levels()), LogLevel.ERROR, "DEBUG", LogLevel.DEBUG),
    (set(LogLevel.real_levels()), LogLevel.ERROR, "WARNING", LogLevel.WARNING),
    (set(LogLevel.real_levels()), LogLevel.ERROR, "INFO", LogLevel.INFO),
    (set(LogLevel.real_levels()), LogLevel.ERROR, "CRITICAL", LogLevel.CRITICAL),
    (set(LogLevel.real_levels()), LogLevel.CRITICAL, "CRITICAL", LogLevel.CRITICAL),
    (set(LogLevel.real_levels()), LogLevel.CRITICAL, "DEBUG", LogLevel.DEBUG),
    (set(LogLevel.real_levels()), LogLevel.CRITICAL, "WARNING", LogLevel.WARNING),
    (set(LogLevel.real_levels()), LogLevel.CRITICAL, "ERROR", LogLevel.ERROR),
    (set(LogLevel.real_levels()), LogLevel.CRITICAL, "INFO", LogLevel.INFO),
    ({LogLevel.INFO}, LogLevel.INFO, "INFO", LogLevel.INFO),
    ({LogLevel.INFO, LogLevel.ERROR}, LogLevel.INFO, "INFO", LogLevel.INFO),
    ({LogLevel.INFO, LogLevel.ERROR}, LogLevel.ERROR, "ERROR", LogLevel.ERROR),
    ({LogLevel.INFO, LogLevel.ERROR}, LogLevel.INFO, "ERROR", LogLevel.ERROR),
    ({LogLevel.INFO, LogLevel.ERROR}, LogLevel.ERROR, "INFO", LogLevel.INFO),
])
def test_prefs_dialog_level_combobox_sends_log_level_to_model(qtbot: QtBot, available_levels, selected_level, new_level,
                                                              expected_model_update):
    item = LoggerTableModelItem(name="logger", available_levels=available_levels, selected_level=selected_level)
    model = LoggerTableModel(data=[item])
    parent_widget = QWidget()
    qtbot.add_widget(parent_widget)
    index = model.createIndex(0, 0)
    delegate = LevelComboboxColumnDelegate()
    combobox = cast(QComboBox, delegate.createEditor(parent_widget, QStyleOptionViewItem(), index))
    assert isinstance(combobox, QComboBox)
    delegate.setEditorData(combobox, index)
    new_index = combobox.findText(new_level)
    assert new_index != -1

    with mock.patch.object(model, "setData") as setData:
        combobox.setCurrentIndex(new_index)
        combobox.activated.emit(new_index)  # Gets triggered only by user interaction
        setData.assert_called_once_with(index, expected_model_update)


@pytest.mark.parametrize("fmt_config,expected_titles", [
    ({"test_attr": FmtConfiguration(value=True, title="Attribute 1"), "test_attr2": FmtConfiguration(value=True, title="Attribute 2")}, {"Attribute 1", "Attribute 2"}),
    ({"test_attr": FmtConfiguration(value=False, title="Attribute 1"), "test_attr2": FmtConfiguration(value=True, title="Attribute 2")}, {"Attribute 1", "Attribute 2"}),
    ({"test_attr": FmtConfiguration(value=True, title="Attribute 1"), "test_attr2": FmtConfiguration(value=False, title="Attribute 2")}, {"Attribute 1", "Attribute 2"}),
    ({"test_attr": FmtConfiguration(value=False, title="Attribute 1"), "test_attr2": FmtConfiguration(value=False, title="Attribute 2")}, {"Attribute 1", "Attribute 2"}),
    ({"test_attr": FmtConfiguration(value=True, title="Attribute 1")}, {"Attribute 1"}),
    ({"test_attr": FmtConfiguration(value=False, title="Attribute 1")}, {"Attribute 1"}),
    ({}, set()),
    ({"smth_custom": FmtConfiguration(value=True, title="Use something custom")}, {"Use something custom"}),
    ({"smth_custom": FmtConfiguration(value=False, title="Use something custom")}, {"Use something custom"}),
])
def test_prefs_dialog_creates_ui_for_formatter(qtbot: QtBot, fmt_config, expected_titles, custom_fmt_class_parametrized):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=set(),
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config=fmt_config,
                                                                color_map={}),
                                  sample_formatter_type=custom_fmt_class_parametrized({k: v.title for k, v in fmt_config.items()}))
    qtbot.add_widget(dialog)
    existing_checkboxes = cast(List[QCheckBox], [chkbx for chkbx in dialog.fmt_group.children() if isinstance(chkbx, QCheckBox)])
    existing_titles = {chkbx.text() for chkbx in existing_checkboxes}
    assert existing_titles == expected_titles


@pytest.mark.parametrize("visible_levels", [
    set(),
    set(LogLevel.real_levels()),
    {LogLevel.DEBUG},
    {LogLevel.DEBUG, LogLevel.INFO},
    {LogLevel.DEBUG, LogLevel.WARNING},
    {LogLevel.DEBUG, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.INFO},
    {LogLevel.INFO, LogLevel.WARNING},
    {LogLevel.INFO, LogLevel.ERROR},
    {LogLevel.INFO, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.WARNING},
    {LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.ERROR},
    {LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.CRITICAL},
])
def test_prefs_dialog_severity_checkboxes_reflect_model(qtbot: QtBot, visible_levels):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=visible_levels,
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={},
                                                                color_map={}),
                                  sample_formatter_type=LogConsoleFormatter)
    qtbot.add_widget(dialog)
    assert dialog.chkbx_debug.isChecked() == (LogLevel.DEBUG in visible_levels)
    assert dialog.chkbx_info.isChecked() == (LogLevel.INFO in visible_levels)
    assert dialog.chkbx_warning.isChecked() == (LogLevel.WARNING in visible_levels)
    assert dialog.chkbx_error.isChecked() == (LogLevel.ERROR in visible_levels)
    assert dialog.chkbx_critical.isChecked() == (LogLevel.CRITICAL in visible_levels)


@pytest.mark.parametrize("notice_text,expect_visible", [
    (None, False),
    ("", True),
    ("some notice", True),
])
@pytest.mark.parametrize("notice_highlighted,expected_color", [
    (True, "#ff0000"),
    (False, "#626262"),
])
def test_prefs_dialog_presents_model_level_notice(qtbot: QtBot, notice_text, notice_highlighted, expect_visible, expected_color):
    notice = (notice_text, notice_highlighted) if notice_text is not None else None
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=set(),
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=notice),
                                  view_config=ViewConfiguration(fmt_config={},
                                                                color_map={}),
                                  sample_formatter_type=LogConsoleFormatter)
    qtbot.add_widget(dialog)
    with qtbot.wait_exposed(dialog):
        dialog.show()
    assert dialog.notice_label.isVisible() == expect_visible
    if expect_visible:
        assert dialog.notice_label.text() == notice_text
        assert dialog.notice_label.palette().color(QPalette.WindowText).name().lower() == expected_color


@pytest.mark.parametrize("buffer_size,expected_value", [
    (-sys.maxsize, "1 message(s)"),
    (-1, "1 message(s)"),
    (0, "1 message(s)"),
    (1, "1 message(s)"),
    (1000, "1000 message(s)"),
    (30000, "30000 message(s)"),
    (9999999, "9999999 message(s)"),
    (sys.maxsize, "9999999 message(s)"),
])
def test_prefs_dialog_buffer_size_reflects_model(qtbot: QtBot, buffer_size, expected_value):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=buffer_size,
                                                                  visible_levels=set(),
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={},
                                                                color_map={}),
                                  sample_formatter_type=LogConsoleFormatter)
    qtbot.add_widget(dialog)
    assert dialog.spin_buffer_size.text() == expected_value


@pytest.mark.parametrize("fmt_config,expected_config", [
    ({"test_attr": FmtConfiguration(value=True, title="Attribute 1"), "test_attr2": FmtConfiguration(value=True, title="Attribute 2")}, {"test_attr": True, "test_attr2": True}),
    ({"test_attr": FmtConfiguration(value=False, title="Attribute 1"), "test_attr2": FmtConfiguration(value=True, title="Attribute 2")}, {"test_attr": False, "test_attr2": True}),
    ({"test_attr": FmtConfiguration(value=True, title="Attribute 1"), "test_attr2": FmtConfiguration(value=False, title="Attribute 2")}, {"test_attr": True, "test_attr2": False}),
    ({"test_attr": FmtConfiguration(value=False, title="Attribute 1"), "test_attr2": FmtConfiguration(value=False, title="Attribute 2")}, {"test_attr": False, "test_attr2": False}),
    ({"test_attr": FmtConfiguration(value=True, title="Attribute 1")}, {"test_attr": True}),
    ({"test_attr": FmtConfiguration(value=False, title="Attribute 1")}, {"test_attr": False}),
    ({}, {}),
    ({"smth_custom": FmtConfiguration(value=True, title="Use something custom")}, {"smth_custom": True}),
    ({"smth_custom": FmtConfiguration(value=False, title="Use something custom")}, {"smth_custom": False}),
])
def test_prefs_dialog_formatter_reflects_config(qtbot: QtBot, fmt_config, expected_config, custom_fmt_class_parametrized):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=set(),
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config=fmt_config,
                                                                color_map={}),
                                  sample_formatter_type=custom_fmt_class_parametrized({k: v.title for k, v in fmt_config.items()}))
    qtbot.add_widget(dialog)
    existing_config = {chkbx.objectName().replace("checkbox_fmt_", ""): chkbx.isChecked()
                       for chkbx in dialog.fmt_group.children() if isinstance(chkbx, QCheckBox)}

    assert existing_config == expected_config


@pytest.mark.parametrize("visible_levels", [
    set(),
    set(LogLevel.real_levels()),
    {LogLevel.DEBUG},
    {LogLevel.DEBUG, LogLevel.INFO},
    {LogLevel.DEBUG, LogLevel.WARNING},
    {LogLevel.DEBUG, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.INFO},
    {LogLevel.INFO, LogLevel.WARNING},
    {LogLevel.INFO, LogLevel.ERROR},
    {LogLevel.INFO, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.WARNING},
    {LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.ERROR},
    {LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.CRITICAL},
])
def test_prefs_dialog_show_all_severity_levels(qtbot: QtBot, visible_levels):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=visible_levels,
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={},
                                                                color_map={}),
                                  sample_formatter_type=LogConsoleFormatter)
    qtbot.add_widget(dialog)
    dialog.btn_show_all.click()
    assert dialog.chkbx_debug.isChecked()
    assert dialog.chkbx_info.isChecked()
    assert dialog.chkbx_warning.isChecked()
    assert dialog.chkbx_error.isChecked()
    assert dialog.chkbx_critical.isChecked()


@pytest.mark.parametrize("visible_levels", [
    set(),
    set(LogLevel.real_levels()),
    {LogLevel.DEBUG},
    {LogLevel.DEBUG, LogLevel.INFO},
    {LogLevel.DEBUG, LogLevel.WARNING},
    {LogLevel.DEBUG, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.DEBUG, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.INFO},
    {LogLevel.INFO, LogLevel.WARNING},
    {LogLevel.INFO, LogLevel.ERROR},
    {LogLevel.INFO, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.WARNING},
    {LogLevel.WARNING, LogLevel.ERROR},
    {LogLevel.WARNING, LogLevel.CRITICAL},
    {LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.ERROR},
    {LogLevel.ERROR, LogLevel.CRITICAL},
    {LogLevel.CRITICAL},
])
def test_prefs_dialog_hide_all_severity_levels(qtbot: QtBot, visible_levels):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=visible_levels,
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={},
                                                                color_map={}),
                                  sample_formatter_type=LogConsoleFormatter)
    qtbot.add_widget(dialog)
    dialog.btn_hide_all.click()
    assert not dialog.chkbx_debug.isChecked()
    assert not dialog.chkbx_info.isChecked()
    assert not dialog.chkbx_warning.isChecked()
    assert not dialog.chkbx_error.isChecked()
    assert not dialog.chkbx_critical.isChecked()


@pytest.mark.parametrize("new_attr_val,new_attr2_val,expected_string", [
    (True, True, "fixed string+1+2"),
    (True, False, "fixed string+1"),
    (False, True, "fixed string+2"),
    (False, False, "fixed string"),
])
def test_prefs_dialog_formatter_change_rerenders_sample_message_on_config_change(qtbot: QtBot, custom_fmt_class,
                                                                                 new_attr_val, new_attr2_val, expected_string):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=set(),
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={"test_attr": FmtConfiguration(value=False, title=""),
                                                                            "test_attr2": FmtConfiguration(value=False, title="")},
                                                                color_map={}),
                                  sample_formatter_type=custom_fmt_class)
    qtbot.add_widget(dialog)
    with qtbot.wait_exposed(dialog):
        dialog.show()
    attr_chkbx = cast(QCheckBox, next((chkbx for chkbx in dialog.fmt_group.children() if chkbx.objectName() == "checkbox_fmt_test_attr")))
    attr2_chkbx = cast(QCheckBox, next((chkbx for chkbx in dialog.fmt_group.children() if chkbx.objectName() == "checkbox_fmt_test_attr2")))
    attr_chkbx.setCheckState(Qt.Checked if new_attr_val else Qt.Unchecked)
    attr2_chkbx.setCheckState(Qt.Checked if new_attr2_val else Qt.Unchecked)
    assert dialog.sample_msg.text() == expected_string


@pytest.mark.parametrize("attr_val,attr2_val,expected_string", [
    (True, True, "fixed string+1+2"),
    (True, False, "fixed string+1"),
    (False, True, "fixed string+2"),
    (False, False, "fixed string"),
])
def test_prefs_dialog_renders_formatter_sample_message_on_show(qtbot: QtBot, custom_fmt_class,
                                                               attr_val, attr2_val, expected_string):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels=set(),
                                                                  selected_logger_levels={},
                                                                  available_logger_levels={},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={"test_attr": FmtConfiguration(value=attr_val, title=""),
                                                                            "test_attr2": FmtConfiguration(value=attr2_val, title="")},
                                                                color_map={}),
                                  sample_formatter_type=custom_fmt_class)
    qtbot.add_widget(dialog)
    assert dialog.sample_msg.text() != expected_string
    with qtbot.wait_exposed(dialog):
        dialog.show()
    assert dialog.sample_msg.text() == expected_string


def test_prefs_dialog_accept_propagates_model_changes(qtbot: QtBot, custom_fmt_class):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels={LogLevel.CRITICAL},
                                                                  selected_logger_levels={"logger": LogLevel.WARNING},
                                                                  available_logger_levels={"logger": {LogLevel.ERROR, LogLevel.WARNING}},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={"test_attr": FmtConfiguration(value=True, title=""),
                                                                            "test_attr2": FmtConfiguration(value=False, title="")},
                                                                color_map={LogLevel.ERROR: ("#ff0000", False),
                                                                           LogLevel.WARNING: ("#ffff00", False)}),
                                  sample_formatter_type=custom_fmt_class)
    qtbot.add_widget(dialog)
    assert dialog.model_config.visible_levels == {LogLevel.CRITICAL}
    assert dialog.model_config.buffer_size == 1
    assert dialog.model_config.selected_logger_levels == {"logger": LogLevel.WARNING}
    assert dialog.model_config.available_logger_levels == {"logger": {LogLevel.ERROR, LogLevel.WARNING}}

    dialog.spin_buffer_size.setValue(100)
    dialog.chkbx_error.setChecked(True)
    dialog.chkbx_critical.setChecked(False)

    def find_combobox_child_recursive(parent: QWidget):
        if isinstance(parent, QComboBox):
            yield parent
        for child in parent.children():
            if isinstance(child, QWidget):
                for grandchild in find_combobox_child_recursive(child):
                    yield grandchild

    combobox = next(iter(find_combobox_child_recursive(dialog.table_loggers)))
    combobox.setCurrentText("ERROR")
    combo_idx = combobox.findText("ERROR")
    assert combo_idx != -1
    combobox.activated.emit(combo_idx)  # Gets triggered only by user interaction

    dialog.accept()

    assert dialog.model_config.visible_levels == {LogLevel.ERROR}
    assert dialog.model_config.buffer_size == 100
    assert dialog.model_config.selected_logger_levels == {"logger": LogLevel.ERROR}
    assert dialog.model_config.available_logger_levels == {"logger": {LogLevel.ERROR, LogLevel.WARNING}}


def test_prefs_dialog_accept_propagates_view_changes(qtbot: QtBot, custom_fmt_class):
    dialog = LogPreferencesDialog(model_config=ModelConfiguration(buffer_size=1,
                                                                  visible_levels={LogLevel.CRITICAL},
                                                                  selected_logger_levels={"logger": LogLevel.WARNING},
                                                                  available_logger_levels={"logger": {LogLevel.ERROR, LogLevel.WARNING}},
                                                                  notice=None),
                                  view_config=ViewConfiguration(fmt_config={"test_attr": FmtConfiguration(value=True, title=""),
                                                                            "test_attr2": FmtConfiguration(value=False, title="")},
                                                                color_map={LogLevel.ERROR: ("#ff0000", False),
                                                                           LogLevel.WARNING: ("#ffff00", False)}),
                                  sample_formatter_type=custom_fmt_class)
    qtbot.add_widget(dialog)
    assert dialog.view_config.fmt_config == {"test_attr": FmtConfiguration(value=True, title=""),
                                             "test_attr2": FmtConfiguration(value=False, title="")}
    assert dialog.view_config.color_map == {LogLevel.ERROR: ("#ff0000", False),
                                            LogLevel.WARNING: ("#ffff00", False)}

    attr_chkbx = cast(QCheckBox, next((chkbx for chkbx in dialog.fmt_group.children() if chkbx.objectName() == "checkbox_fmt_test_attr")))
    attr2_chkbx = cast(QCheckBox, next((chkbx for chkbx in dialog.fmt_group.children() if chkbx.objectName() == "checkbox_fmt_test_attr2")))
    attr_chkbx.setCheckState(Qt.Unchecked)
    attr2_chkbx.setCheckState(Qt.Checked)

    def find_color_button_child_recursive(parent: QWidget):
        if isinstance(parent, ColorButton):
            yield parent
        for child in parent.children():
            if isinstance(child, QWidget):
                for grandchild in find_color_button_child_recursive(child):
                    yield grandchild

    color_iter = iter(find_color_button_child_recursive(dialog.table_colors))
    err_color_btn = cast(ColorButton, next(color_iter))
    with mock.patch("accwidgets.qt.QColorDialog.getColor", return_value=QColor("#232323")):
        err_color_btn.click()
    warn_color_btn = cast(ColorButton, next(color_iter))
    with mock.patch("accwidgets.qt.QColorDialog.getColor", return_value=QColor("#fefefe")):
        warn_color_btn.click()

    dialog.accept()

    assert dialog.view_config.fmt_config == {"test_attr": FmtConfiguration(value=False, title=""),
                                             "test_attr2": FmtConfiguration(value=True, title="")}
    assert dialog.view_config.color_map == {LogLevel.ERROR: ("#232323", False),
                                            LogLevel.WARNING: ("#fefefe", False)}
