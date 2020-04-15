import copy
import warnings
import functools
from abc import abstractmethod
from typing import Optional, List, Union, cast, Callable, TypeVar, Generic, Dict
from pathlib import Path
from collections import OrderedDict
from qtpy.QtCore import QObject, QAbstractTableModel, QModelIndex, Qt, QVariant, QLocale, QEvent
from qtpy.QtWidgets import (QDialog, QPushButton, QTableView, QDialogButtonBox, QAction, QStyledItemDelegate, QStyle,
                            QWidget, QStyleOptionViewItem, QComboBox, QMessageBox, QStyleOptionButton, QApplication)
from qtpy.QtGui import QPainter
from qtpy.QtDesigner import QDesignerFormWindowInterface
from qtpy.uic import loadUi
from accwidgets.generics import GenericQObjectMeta
from accwidgets.common import AbstractQObjectMeta
from accwidgets.property_edit import PropertyEdit, PropertyEditField, EnumItemConfig
from accwidgets.property_edit.propedit import _pack_designer_fields, _unpack_designer_fields
from accwidgets.designer_base import WidgetsExtension


T = TypeVar("T")
D = TypeVar("D")


class AbstractTableModel(QAbstractTableModel, Generic[T, D], metaclass=GenericQObjectMeta):

    def __init__(self, data: List[T], parent: Optional[QObject] = None):
        """
        Base class for the table model to be shared between :class:`PropertyEdit` dialog tables.

        Args:
            data: Initial data for the model
            parent: Parent Widget
        """
        super().__init__(parent)
        self._data = data

    @abstractmethod
    def column_name(self, section: int) -> str:
        """Name of the column to be embedded in the header.

        Args:
            section: Column index.

        Returns:
            Name string.
        """
        pass

    @abstractmethod
    def make_row(self) -> T:
        """Create a new empty object when appending a new row to the table."""
        pass

    @abstractmethod
    def data_at_index(self, index: QModelIndex) -> D:
        """
        Return data for the table item at given index.

        Args:
            index: Row and column in the table.

        Returns:
            Data item.
        """
        pass

    @abstractmethod
    def update_data_at_index(self, index: QModelIndex, value: D) -> T:
        """
        Update data at the given index and return the item to get inserted in case if the structure is immutable.

        Args:
            index: Row and column in the table
            value: Value to insert

        Returns:
            Updated data item.
        """
        pass

    @abstractmethod
    def validate(self):
        """
        Validate the model before saving it to file. Throw ValueError on any problem that you find.

        Raises:
            ValueError: Whenever a problem is detected with the data model.
        """
        pass

    def flags(self, _) -> int:
        """
        Flags to render the table cell editable / selectable / enabled.

        Args:
            index: Position of the cell.

        Returns:
            Flags how to render the cell.
        """
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def rowCount(self, _: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        """Returns the number of rows under the given parent."""
        return len(self._data)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> str:
        """
        Returns the data for the given role and section in the header with the specified orientation.

        For horizontal headers, the section number corresponds to the column number. Similarly,
        for vertical headers, the section number corresponds to the row number.

        Args:
            section: column / row of which the header data should be returned
            orientation: Columns / Row
            role: Not used by this implementation, if not DisplayRole, super
                  implementation is called

        Returns:
            Header Data (f.e. name) for the row / column
        """
        if role != Qt.DisplayRole:
            return super().headerData(section, orientation, role)
        if orientation == Qt.Horizontal and section < self.columnCount():
            return self.column_name(section)
        elif orientation == Qt.Vertical and section < self.rowCount():
            return str(section + 1)
        return ""

    def append(self):
        """Append a new row to the model."""
        new_idx = len(self._data)
        self.beginInsertRows(QModelIndex(), new_idx, new_idx)
        new_obj = self.make_row()
        self._data.append(new_obj)
        self.endInsertRows()
        idx = self.createIndex(new_idx, 0)
        self.dataChanged.emit(idx, idx)

    def remove(self, index: QModelIndex):
        """
        Remove a row in the data model by a given index.

        Args:
            index: Index of row, which needs to be removed.
        """
        removed_idx = index.row()
        self.beginRemoveRows(QModelIndex(), removed_idx, removed_idx)
        self._data.remove(self._data[removed_idx])
        self.endRemoveRows()
        idx = self.createIndex(removed_idx, 0)
        self.dataChanged.emit(idx, idx)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> D:
        """
        Get Data from the table's model by a given index.

        Args:
            index: row & column in the table
            role: which property is requested

        Returns:
            Data associated with the passed index
        """
        # Handle invalid indices
        if not index.isValid():
            return QVariant()
        if index.row() >= self.rowCount():
            return QVariant()
        if index.column() >= self.columnCount():
            return QVariant()
        # Return found data
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.data_at_index(index)
        return QVariant()

    def setData(self, index: QModelIndex, value: D, role: Qt.ItemDataRole = Qt.EditRole) -> bool:
        """
        Set Data to the tables data model at the given index.

        Args:
            index: Position of the new value
            value: new value
            role: which property is requested

        Returns:
            True if the data could be successfully set.
        """
        if not index.isValid():
            return False
        if index.row() >= self.rowCount():
            return False
        if index.column() >= self.columnCount():
            return False
        if role == Qt.EditRole:
            updated_row: T = self.update_data_at_index(index=index, value=value)
            self._data[index.row()] = updated_row
            self.dataChanged.emit(index, index)
            return True
        return False

    @property
    def raw_data(self) -> List[T]:
        """Getter for the internal data structure."""
        return self._data


FieldTableData = Union[QVariant, str, float, int, bool]
"""Possible types of values in the FieldEditor table."""


class FieldEditorTableModel(AbstractTableModel[PropertyEditField, FieldTableData]):

    def __init__(self, data: List[PropertyEditField], parent: Optional[QObject] = None):
        """
        Data Model for the table of the :class:`PropertyEdit` field editor.

        Args:
            data: Initial data for the model
            parent: Parent Widget
        """
        super().__init__(data=copy.copy(data), parent=parent)
        self._columns = OrderedDict()
        self._columns["Field name"] = "field"
        self._columns["Field type"] = "type"
        self._columns["Editable"] = "editable"
        self._columns["Label"] = "label"
        self._columns["User data"] = "user_data"

    def columnCount(self, _: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        """Returns the number of columns for the children of the given parent."""
        return len(self._columns)

    def column_name(self, section: int) -> str:
        return list(self._columns.keys())[section]

    def make_row(self) -> PropertyEditField:
        return PropertyEditField(field="", type=PropertyEdit.ValueType.INTEGER, editable=False)

    def data_at_index(self, index: QModelIndex) -> FieldTableData:
        column_name = list(self._columns.keys())[index.column()]
        row = self._data[index.row()]
        return getattr(row, self._columns[column_name])

    def update_data_at_index(self, index: QModelIndex, value: FieldTableData) -> PropertyEditField:
        column_name = list(self._columns.keys())[index.column()]
        row = self._data[index.row()]
        setattr(row, self._columns[column_name], value)
        return row

    def set_fields_editable(self, editable: bool):
        """
        Sets the (non-)editable flag on all the defined fields.

        Args:
            editable: flag to set.
        """
        for idx in range(len(self._data)):
            self.setData(self.createIndex(idx, 2), editable)

    def data_for_item(self, row: int, column: int) -> FieldTableData:
        """
        Convenience getter for data item given the separate `row`, column indexes as opposed to :class:`QModelIndex`.

        Args:
            row: Index of the row.
            column: Index of the column.

        Returns:
            Data in the given cell.
        """
        idx = self.createIndex(row, column)
        return self.data(idx)

    def validate(self):
        used_fields = set()
        for idx, item in enumerate(cast(List[PropertyEditField], self._data)):
            if not item.field:
                raise ValueError(f'Row #{idx+1} is lacking mandatory "Field name".')
            if item.field in used_fields:
                raise ValueError(f'Field "{item.field}" is used more than once.')
            try:
                _ = PropertyEdit.ValueType(item.type)  # Raises ValueError if value is outside of defined by enum
            except ValueError:
                raise ValueError(f'Row #{idx+1} defines unknown "Field type".')
            if item.type == PropertyEdit.ValueType.ENUM:
                ud = item.user_data or {}
                options = ud.get("options")
                if not options:
                    raise ValueError(f'Row #{idx+1} must define enum options via "User data".')
            used_fields.add(item.field)


EnumTableData = Union[str, int]
"""Possible types of values in the EnumEditor table."""


class EnumEditorTableModel(AbstractTableModel[EnumItemConfig, EnumTableData]):

    def __init__(self, data: List[EnumItemConfig], parent: Optional[QObject] = None):
        """
        Data Model for the configuration of the ENUM type property fields.

        Args:
            data: Initial data for the model
            parent: Parent Widget
        """
        super().__init__(data=[*data], parent=parent)

    def columnCount(self, _: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        """Returns the number of columns for the children of the given parent."""
        return 2

    def column_name(self, section: int) -> str:
        return "Label" if section == 0 else "Value"

    def make_row(self) -> EnumItemConfig:
        return "", self._find_largest_code() + 1

    def data_at_index(self, index: QModelIndex) -> EnumTableData:
        return self._data[index.row()][index.column()]

    def update_data_at_index(self, index: QModelIndex, value: EnumTableData) -> EnumItemConfig:
        row = list(self._data[index.row()])
        row[index.column()] = value
        return cast(EnumItemConfig, tuple(row))

    def validate(self):
        used_codes = set()
        used_labels = set()
        for idx, item in enumerate(self._data):
            label, code = item
            if not label:
                raise ValueError(f'Row #{idx+1} is lacking "Label".')
            if code in used_codes:
                raise ValueError(f'Enum value "{code}" is being used more than once.')
            if label in used_labels:
                raise ValueError(f'Label value "{label}" is being used more than once.')
            used_codes.add(code)
            used_labels.add(label)

    def _find_largest_code(self) -> int:
        return max([x[1] for x in self._data] + [-1])


class UserDataColumnDelegate(QStyledItemDelegate):
    """
    Customizes field user data column to be displayed as a button for selected types.
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """
        Overrides :class:`QStyledItemDelegate` base method to embed a button. Without this, button would be
        visible only in the editing mode (when user focuses inside the cell), as that's the default behavior for
        using :meth:`createMethod`. This approach discovered in the description of
        https://doc.qt.io/qt-5/qabstractitemdelegate.html and
        https://programtalk.com/python-examples/PyQt4.QtGui.QStyleOptionButton/. As referred in the official documentation,
        it uses "the second approach", opting in for paint-editorEvent pair rather than using :meth:`createEditor` method.
        It is done so that there's only one button (createEditor would create another instance that is rendered only when
        double clicking), and one event.

        Args:
            painter: used to render the item
            option: provides information about how to render the item
            index: location of the item in the table
        """
        model = cast(FieldEditorTableModel, index.model())
        item_type = qvariant_to_value_type(model.data_for_item(index.row(), 1))
        if item_type == PropertyEdit.ValueType.ENUM:

            enum_config = model.data_for_item(index.row(), 4) or {}
            option_cnt = len(cast(Dict[str, List], enum_config).get("options", []))
            if option_cnt == 0:
                suffix = ""
            else:
                suffix = f" ({option_cnt} option"
                if option_cnt > 1:
                    suffix += "s"
                suffix += ")"

            btn_option = QStyleOptionButton()
            btn_option.text = "Configure" + suffix
            btn_option.state = option.state
            btn_option.rect = option.rect
            btn_option.palette = option.palette
            cast(QStyle, QApplication.style()).drawControl(QStyle.CE_PushButton, btn_option, painter)
        else:
            super().paint(painter, option, index)

    def editorEvent(self, event: QEvent, model: QAbstractTableModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """
        Overridden event filter. It prevents default double-click from initiating edit mode, and simulates single
        click on a button to open a dialog.

        Args:
            event: event that triggered the editing
            model: model that holds the data
            option: provides information about how to render the item
            index: location of the item in the table

        Returns:
            ``False`` indicates that it event has has not been handled.
        """
        if event.type() == QEvent.MouseButtonPress:
            item_type = qvariant_to_value_type(cast(FieldEditorTableModel, index.model()).data_for_item(index.row(), 1))
            if item_type == PropertyEdit.ValueType.ENUM:
                self._open_editor(index)
                event.accept()
                return True
        elif event.type() == QEvent.MouseButtonDblClick:
            # Prevent default editing mode on double-click
            event.accept()
            return True
        return super().editorEvent(event, model, option, index)

    def _open_editor(self, index: QModelIndex):
        enum_config = cast(FieldEditorTableModel, index.model()).data_for_item(index.row(), 4) or {}
        dialog = EnumOptionsDialog(options=cast(Dict[str, List[EnumItemConfig]], enum_config).get("options", []),
                                   on_save=lambda config: index.model().setData(index, PropertyEdit.ValueType.enum_user_data(config), Qt.EditRole))
        dialog.show()
        dialog.exec_()


class FieldTypeColumnDelegate(QStyledItemDelegate):
    """
    Customizes field type column to be displayed as a combobox.
    """

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """
        The widget for the controlled column.
        This overrides :class:`QStyledItemDelegate` base method.

        Args:
            parent: parent widget
            option: controls the appearance of the editor
            index: position of the editor in the table

        Returns:
            New editor widget
        """
        editor = QComboBox(parent)
        for opt in PropertyEdit.ValueType:
            editor.addItem(value_type_to_str(opt), opt)

        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        """
        Set the combobox text from the table item's model.
        This overrides :class:`QStyledItemDelegate` base method.

        Args:
            editor: editor to adjust the text of
            index: position of the editor in the table
        """
        combo = cast(QComboBox, editor)
        data = index.model().data(index, Qt.EditRole)
        editor_idx = combo.findData(qvariant_to_value_type(data))
        if editor_idx != -1:
            combo.setCurrentIndex(editor_idx)
        else:
            warnings.warn("Can't find the option for the combobox to set")

    def setModelData(self, editor: QWidget, model: QAbstractTableModel, index: QModelIndex):
        """
        Gets data from the editor widget and stores it in the specified model at the item index.
        This overrides :class:`QStyledItemDelegate` base method.

        Args:
            editor: editor the data was entered in
            model: model the data should be saved in
            index: position of the editor in the table
        """
        combo = cast(QComboBox, editor)
        model.setData(index, combo.currentData(), Qt.EditRole)

    def displayText(self, value: QVariant, locale: QLocale) -> str:
        """
        Returns textual value of the field, when user is not editing it.
        This overrides :class:`QStyledItemDelegate` base method.

        Args:
            value: value to convert to the string representation
            locale: locale to use for string conversion

        Returns:
            Formatter string.
        """
        val = qvariant_to_value_type(value)
        return value_type_to_str(val)


class AbstractPropertyEditDialog(QDialog, metaclass=AbstractQObjectMeta):

    def __init__(self, ui_file: str, table_model: AbstractTableModel, parent: Optional[QObject] = None):
        """
        Base Dialog class for displaying editing features of the :class:`PropertyEdit`.

        Args:
            ui_file: Filename of the related Qt Designer file.
            table_model: Type for instantiating table model.
            parent: Parent item for the dialog.
        """
        super().__init__(parent)

        self.add_btn: QPushButton = None
        self.remove_btn: QPushButton = None
        self.buttons: QDialogButtonBox = None
        self.table: QTableView = None

        loadUi(str(Path(__file__).absolute().parent / ui_file), self)

        self.add_btn.clicked.connect(self._add)
        self.remove_btn.clicked.connect(self._remove)
        self.remove_btn.setEnabled(False)
        self.buttons.accepted.connect(self._save)

        self._table_model = table_model
        self.table.setModel(self._table_model)
        self.table.selectionModel().selectionChanged.connect(self._on_selection)

    @abstractmethod
    def before_save(self):
        """
        Method that is called when validations have passed and the dialog is about to close.

        Here is a good time to send the updated data to the original owner.
        """
        pass

    def _on_selection(self):
        removable = self.table.selectionModel().hasSelection()
        self.remove_btn.setEnabled(removable)

    def _add(self):
        self._table_model.append()

    def _remove(self):
        self._table_model.remove(self.table.currentIndex())

    def _save(self):
        try:
            self._table_model.validate()
        except Exception as ex:
            QMessageBox.warning(self, "Invalid data", str(ex))
            return

        self.before_save()
        self.accept()


class EnumOptionsDialog(AbstractPropertyEditDialog):

    def __init__(self, options: List[EnumItemConfig], on_save: Callable[[List[EnumItemConfig]], None], parent: Optional[QObject] = None):
        """
        Dialog displaying a table to the user for editing configuration of the ENUM field.

        Args:
            options: Setup for the combobox options.
            on_save: Callback to accept updated values.
            parent: Parent item for the dialog.
        """
        table_model = EnumEditorTableModel(data=options)
        super().__init__(ui_file="enum_editor.ui", table_model=table_model, parent=parent)
        self._on_save = on_save

        self.setWindowTitle("Configure enum options")

        self.buttons.rejected.connect(self.close)

        self.resize(400, 200)

    def before_save(self):
        self._on_save(self._table_model.raw_data)


class FieldsDialog(AbstractPropertyEditDialog):

    def __init__(self, widget: PropertyEdit, parent: Optional[QObject] = None):
        """
        Dialog displaying a table to the user for editing fields of the :class:`PropertyEdit` object.

        Args:
            widget: Widget that will be the base of the tables data model.
            parent: Parent item for the dialog.
        """
        self.all_rw: QPushButton = None
        self.all_ro: QPushButton = None
        table_model = FieldEditorTableModel(_unpack_designer_fields(cast(str, widget.fields)))
        super().__init__(ui_file="field_editor.ui", table_model=table_model, parent=parent)
        self._widget = widget

        # self.setWindowTitle(f"Edit Fields for {widget.propertyName}")  # Use this when propertyName made available
        self.setWindowTitle("Define PropertyEdit fields")

        self.all_rw.clicked.connect(functools.partial(self._table_model.set_fields_editable, True))
        self.all_ro.clicked.connect(functools.partial(self._table_model.set_fields_editable, False))

        # This will be connected by default, but we do want to do additional validation,
        # so we need to prevent automatic closing
        self.buttons.accepted.disconnect(self.accept)

        self.table.model().dataChanged.connect(self._on_data_change)
        self.table.setItemDelegateForColumn(1, FieldTypeColumnDelegate(self))
        self.table.setItemDelegateForColumn(4, UserDataColumnDelegate(self))

        # Recalculate button states
        self._on_data_change()

        self.resize(600, 300)

    def before_save(self):
        form = QDesignerFormWindowInterface.findFormWindow(self._widget)
        if form:
            form.cursor().setProperty("fields", _pack_designer_fields(self._table_model.raw_data))

    def _on_data_change(self):
        data_prefilled = len(self._table_model.raw_data) > 0
        self.all_ro.setEnabled(data_prefilled)
        self.all_rw.setEnabled(data_prefilled)


class PropertyFieldExtension(WidgetsExtension):

    def __init__(self, widget: PropertyEdit):
        """
        Task Menu Extension for editing :class:`PropertyEdit` fields in a dialog.

        Args:
            widget: widget the extension is associated with.
        """
        super().__init__(widget)
        self.action = QAction("Edit Contents...", self.widget)
        self.action.triggered.connect(self._open_dialog)

    def actions(self):
        """Actions associated with this extension."""
        return [self.action]

    def _open_dialog(self):
        dialog = FieldsDialog(widget=self.widget, parent=self.widget)
        dialog.show()
        dialog.exec_()


def qvariant_to_value_type(value: Union[QVariant, int, PropertyEdit.ValueType]) -> PropertyEdit.ValueType:
    """
    Converts multiple possible representations of the value type into a proper enum value.

    Args:
        value: incoming value.

    Returns:
        Converted value.
    """
    if isinstance(value, QVariant):
        value = value.value()
    if isinstance(value, int):
        return PropertyEdit.ValueType(value)  # When loaded from file
    else:
        return cast(PropertyEdit.ValueType, value)  # When set inside dialog


def value_type_to_str(val: PropertyEdit.ValueType) -> str:
    """
    Formats the name of the enum value type to the user-readable string.

    Args:
        val: Enum value.

    Returns:
        User-facing string.
    """
    name = str(val).split(".")[1]  # Otherwise it is seen as 'ValueType.SOMETHING'
    return name.title()
