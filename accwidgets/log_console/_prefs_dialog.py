import operator
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, Set, Type, Tuple, cast
from qtpy.QtCore import QSignalBlocker, QModelIndex, Qt
from qtpy.QtGui import QShowEvent, QPalette
from qtpy.QtWidgets import (QDialog, QCheckBox, QPushButton, QWidget, QDialogButtonBox, QGroupBox, QVBoxLayout,
                            QSpinBox, QComboBox, QLabel, QHeaderView)
from qtpy.uic import loadUi
from accwidgets.qt import (ColorPropertyColumnDelegate, PersistentEditorTableView,
                           AbstractTableModel, BooleanPropertyColumnDelegate, AbstractComboBoxColumnDelegate)
from ._config import LogLevel, ColorMap
from ._fmt import AbstractLogConsoleFormatter
from ._model import LogConsoleRecord


@dataclass
class ModelConfiguration:
    buffer_size: int
    visible_levels: Set[LogLevel]
    selected_logger_levels: Dict[str, LogLevel]
    available_logger_levels: Dict[str, Set[LogLevel]]
    notice: Optional[Tuple[str, bool]]

    def validate(self):
        if LogLevel.NOTSET in self.visible_levels:
            raise ValueError("Visible levels cannot contain NOTSET value")
        if self.buffer_size < 1 or math.isnan(self.buffer_size):
            raise ValueError("Buffer size must be positive finite value, greater than 0")
        if self.selected_logger_levels.keys() != self.available_logger_levels.keys():
            raise ValueError("selected_logger_levels and available_logger_levels must have the same keys")
        if self.notice is not None and (not isinstance(self.notice, tuple) or len(self.notice) != 2):
            raise ValueError("notice must be a tuple")


@dataclass
class FmtConfiguration:
    value: bool
    title: str


@dataclass
class ViewConfiguration:
    fmt_config: Dict[str, FmtConfiguration]
    color_map: ColorMap


@dataclass
class ColorTableModelItem:
    level: LogLevel
    color: str
    invert: bool


class ColorTableModel(AbstractTableModel[ColorTableModelItem]):

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
        if role == Qt.DisplayRole and orientation == Qt.Vertical and section < self.rowCount():
            return " " + LogLevel.level_name(self.raw_data[section].level)
        return super().headerData(section, orientation, role)

    def columnCount(self, *_) -> int:
        return 2

    def column_name(self, section: int) -> str:
        if section == 0:
            return "Color"
        return "Invert"

    def get_cell_data(self, index: QModelIndex, row: ColorTableModelItem) -> Any:
        if index.column() == 0:
            return row.color
        return row.invert

    def set_cell_data(self, index: QModelIndex, row: ColorTableModelItem, value: Any) -> bool:
        if index.column() == 0:
            row.color = value
        elif index.column() == 1:
            row.invert = value
        else:
            return False
        return True


@dataclass
class LoggerTableModelItem:
    name: str
    available_levels: Set[LogLevel]
    selected_level: LogLevel


class LoggerTableModel(AbstractTableModel[LoggerTableModelItem]):

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
        if role == Qt.DisplayRole and orientation == Qt.Vertical and section < self.rowCount():
            return " " + self.raw_data[section].name
        return super().headerData(section, orientation, role)

    def columnCount(self, *_) -> int:
        return 1

    def column_name(self, section: int) -> str:
        return "Logger levels"

    def get_cell_data(self, index: QModelIndex, row: LoggerTableModelItem) -> Any:
        return row

    def set_cell_data(self, index: QModelIndex, row: LoggerTableModelItem, value: Any) -> bool:
        row.selected_level = value
        return True


class LevelComboboxColumnDelegate(AbstractComboBoxColumnDelegate):

    def configure_editor(self, editor: QComboBox, model):
        # Leave empty, since we configure it via setEditorData
        pass

    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        if not isinstance(editor, QComboBox):
            return

        if editor.count() == 0:
            data: LoggerTableModelItem = index.data()

            # Setup options on the first render attempt
            # Assume later they don't change dynamically
            for level in sorted(data.available_levels, key=operator.attrgetter("value")):
                editor.addItem(LogLevel.level_name(level), level.value)

        super().setEditorData(editor, index)

    def model_to_user_data(self, value: LoggerTableModelItem) -> int:
        return value.selected_level.value

    def user_data_to_model(self, value: int) -> LogLevel:
        return LogLevel(value)


class LogPreferencesDialog(QDialog):

    def __init__(self,
                 model_config: ModelConfiguration,
                 view_config: ViewConfiguration,
                 sample_formatter_type: Type[AbstractLogConsoleFormatter],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.buttons: QDialogButtonBox = None
        self.btn_hide_all: QPushButton = None
        self.btn_show_all: QPushButton = None
        self.chkbx_critical: QCheckBox = None
        self.chkbx_debug: QCheckBox = None
        self.chkbx_error: QCheckBox = None
        self.chkbx_info: QCheckBox = None
        self.chkbx_warning: QCheckBox = None
        self.table_colors: PersistentEditorTableView = None  # type: ignore
        self.table_loggers: PersistentEditorTableView = None  # type: ignore
        self.fmt_group: QGroupBox = None
        self.spin_buffer_size: QSpinBox = None
        self.sample_msg: QLabel = None
        self.notice_label: QLabel = None

        loadUi(Path(__file__).parent / "prefs.ui", self)

        self.model_config = model_config
        self.view_config = view_config
        self._sample_formatter_type = sample_formatter_type
        self._fmt_checkboxes: Dict[str, QCheckBox] = {}

        self._adjust_level_checkboxes()
        self._adjust_buffer_size()

        for attr_name, config in reversed(list(view_config.fmt_config.items())):
            chkbx = QCheckBox(config.title)
            chkbx.setObjectName(f"checkbox_fmt_{attr_name}")
            cast(QVBoxLayout, self.fmt_group.layout()).insertWidget(0, chkbx)
            _update_chkbx_without_side_effect(chkbx, config.value)
            chkbx.stateChanged.connect(self._on_fmt_chkbx_change)
            self._fmt_checkboxes[attr_name] = chkbx

        self.btn_hide_all.clicked.connect(self._hide_all)
        self.btn_show_all.clicked.connect(self._show_all)

        self.spin_buffer_size.valueChanged.connect(self._on_buffer_size_change)

        self.table_colors.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._colors_model = ColorTableModel(data=[ColorTableModelItem(level=level, color=val[0], invert=val[1])
                                                   for level, val in view_config.color_map.items()],
                                             parent=self)
        self.table_colors.setModel(self._colors_model)
        self.table_colors.setItemDelegateForColumn(0, ColorPropertyColumnDelegate(self))
        self.table_colors.setItemDelegateForColumn(1, BooleanPropertyColumnDelegate(self))
        self.table_colors.set_persistent_editor_for_column(0)
        self.table_colors.set_persistent_editor_for_column(1)
        self._colors_model.dataChanged.connect(self._on_color_map_change)

        all_levels = set(LogLevel.real_levels())
        for level in all_levels:
            self._chkbx_for_level(level).stateChanged.connect(self._adjust_level)

        logger_data = [LoggerTableModelItem(name=logger_name,
                                            available_levels=model_config.available_logger_levels[logger_name],
                                            selected_level=logger_level)
                       for logger_name, logger_level in sorted(model_config.selected_logger_levels.items(),
                                                               key=operator.itemgetter(0))]

        self._loggers_model = LoggerTableModel(data=logger_data, parent=self)
        self.table_loggers.setModel(self._loggers_model)
        self.table_loggers.setItemDelegateForColumn(0, LevelComboboxColumnDelegate(self))
        self.table_loggers.set_persistent_editor_for_column(0)
        self._loggers_model.dataChanged.connect(self._on_logger_levels_changed)

        if model_config.notice is None:
            self.notice_label.hide()
        else:
            text, highlighted = model_config.notice
            self.notice_label.show()
            self.notice_label.setText(text)
            palette = self.notice_label.palette()
            if not highlighted:
                palette.setColor(QPalette.WindowText, palette.color(QPalette.Text))
            else:
                palette.setColor(QPalette.WindowText, palette.color(QPalette.HighlightedText))
            self.notice_label.setPalette(palette)

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        if not event.spontaneous():
            self._render_dummy_message()

    def _show_all(self):
        all_levels = set(LogLevel.real_levels())
        self.model_config.visible_levels = all_levels
        self._adjust_level_checkboxes()

    def _hide_all(self):
        self.model_config.visible_levels = set()
        self._adjust_level_checkboxes()

    def _adjust_level(self):
        chkbx: QCheckBox = self.sender()
        level = LogLevel[chkbx.objectName().replace("chkbx_", "").upper()]
        if chkbx.isChecked():
            self.model_config.visible_levels.add(level)
        else:
            try:
                self.model_config.visible_levels.remove(level)
            except KeyError:
                pass

    def _chkbx_for_level(self, level: LogLevel) -> QCheckBox:
        return getattr(self, f"chkbx_{LogLevel.level_name(level).lower()}")

    def _adjust_level_checkboxes(self):
        all_levels = set(LogLevel.real_levels())
        enabled_levels = self.model_config.visible_levels
        disabled_levels = all_levels.difference(enabled_levels)
        for level in enabled_levels:
            chkbx = self._chkbx_for_level(level)
            _update_chkbx_without_side_effect(chkbx, True)
        for level in disabled_levels:
            chkbx = self._chkbx_for_level(level)
            _update_chkbx_without_side_effect(chkbx, False)

    def _render_dummy_message(self):
        fmt_kwargs = {attr_name: config.value for attr_name, config in self.view_config.fmt_config.items()}
        fmt = self._sample_formatter_type.create(**fmt_kwargs)

        class MyExceptionType(Exception):
            __module__ = "my_module"
            __qualname__ = "MyExceptionType"

        exc = MyExceptionType("My Exception Body")
        exc_info = (type(exc), exc, None)  # Follows the logic from logging Logger._log()
        msg = LogConsoleRecord(logger_name="My Logger",
                               level=LogLevel.ERROR,
                               message="My Message",
                               timestamp=datetime.now().timestamp(),
                               extras={"exc_info": exc_info})
        formatted_msg = fmt.format(msg)
        self.sample_msg.setText(formatted_msg)

    def _adjust_buffer_size(self):
        blocker = QSignalBlocker(self.spin_buffer_size)
        try:
            self.spin_buffer_size.setValue(self.model_config.buffer_size)
        except OverflowError:
            if self.model_config.buffer_size < self.spin_buffer_size.minimum():
                self.spin_buffer_size.setValue(self.spin_buffer_size.minimum())
            else:
                self.spin_buffer_size.setValue(self.spin_buffer_size.maximum())
        blocker.unblock()

    def _on_color_map_change(self):
        self.view_config.color_map = {item.level: (item.color, item.invert)
                                      for item in self._colors_model.raw_data}

    def _on_fmt_chkbx_change(self):
        chkbx: QCheckBox = self.sender()
        for attr_name, widget in self._fmt_checkboxes.items():
            if widget == chkbx:
                self.view_config.fmt_config[attr_name].value = chkbx.isChecked()
                self._render_dummy_message()
                break

    def _on_buffer_size_change(self, val: int):
        self.model_config.buffer_size = val

    def _on_logger_levels_changed(self):
        self.model_config.selected_logger_levels = {item.name: item.selected_level
                                                    for item in self._loggers_model.raw_data}


def _update_chkbx_without_side_effect(chkbx: QCheckBox, val: bool):
    blocker = QSignalBlocker(chkbx)
    chkbx.setChecked(val)
    blocker.unblock()
