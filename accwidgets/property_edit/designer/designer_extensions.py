import copy
import functools
from dataclasses import dataclass
from typing import Optional, List, cast, Callable, Dict, Any
from pathlib import Path
from collections import OrderedDict
from qtpy.QtCore import QObject, QModelIndex, Qt, QPersistentModelIndex
from qtpy.QtWidgets import (QPushButton, QAction, QStyledItemDelegate, QWidget,
                            QStyleOptionViewItem, QComboBox)
from accwidgets.property_edit import PropertyEdit, PropertyEditField, EnumItemConfig
from accwidgets.property_edit.propedit import _pack_designer_fields, _unpack_designer_fields
from accwidgets._designer_base import WidgetsTaskMenuExtension, get_designer_cursor
from accwidgets.qt import (AbstractTableDialog, AbstractTableModel, BooleanPropertyColumnDelegate,
                           AbstractComboBoxColumnDelegate, TableViewColumnResizer, _STYLED_ITEM_DELEGATE_INDEX)


class FieldEditorTableModel(AbstractTableModel[PropertyEditField]):

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

    def notify_change(self, start: QModelIndex, end: QModelIndex, action_type: AbstractTableModel.ChangeType):
        if action_type == self.ChangeType.UPDATE_ITEM and start.column() == 1:
            # Update all row. When setting Field Type, it may affect appearance of the user data column
            super().notify_change(start=start,
                                  end=end.siblingAtColumn(end.model().columnCount() - 1),
                                  action_type=action_type)
        else:
            super().notify_change(start=start, end=end, action_type=action_type)

    def columnCount(self, _: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return len(self._columns)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        This makes user data cells disabled when not available.
        """
        if index.column() == self.columnCount() - 1:
            if index.siblingAtColumn(1).data() != PropertyEdit.ValueType.ENUM:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            else:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return super().flags(index)

    def column_name(self, section: int) -> str:
        return list(self._columns.keys())[section]

    def create_row(self) -> PropertyEditField:
        return PropertyEditField(field="", type=PropertyEdit.ValueType.INTEGER, editable=False)

    def get_cell_data(self, index: QModelIndex, row: PropertyEditField) -> Any:
        column_name = list(self._columns.keys())[index.column()]
        return getattr(row, self._columns[column_name])

    def set_cell_data(self, index: QModelIndex, row: PropertyEditField, value: Any) -> bool:
        if (index.column() == len(self._columns) - 1) and not (value is None or isinstance(value, dict)):
            # For some reason we are getting False for "User data" here sometimes.
            return False
        column_name = list(self._columns.keys())[index.column()]
        setattr(row, self._columns[column_name], value)
        return True

    def set_fields_editable(self, editable: bool):
        """
        Sets the (non-)editable flag on all the defined fields.

        Args:
            editable: flag to set.
        """
        for idx in range(len(self._data)):
            self.setData(self.createIndex(idx, 2), editable)

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
            elif item.type == PropertyEdit.ValueType.REAL:
                ud = item.user_data or {}
                precision = ud.get("precision")
                if precision == 0:
                    raise ValueError(f'Row #{idx+1} has 0 precision for REAL type. Use INTEGER instead.')
            used_fields.add(item.field)


@dataclass
class EnumTableData:
    """Possible types of values in the EnumEditor table."""
    label: str
    value: int

    @classmethod
    def from_enum_item_config(cls, item: EnumItemConfig):
        """Instantiate view model from the core component data structure."""
        label, code = item
        return cls(label=label, value=code)

    def to_enum_item_config(self) -> EnumItemConfig:
        """Convert view model to the original data structure."""
        return self.label, self.value


class EnumEditorTableModel(AbstractTableModel[EnumTableData]):

    def columnCount(self, _: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        """Returns the number of columns for the children of the given parent."""
        return 2

    def column_name(self, section: int) -> str:
        return "Label" if section == 0 else "Value"

    def create_row(self) -> EnumTableData:
        return EnumTableData(label="", value=self._find_largest_code() + 1)

    def get_cell_data(self, index: QModelIndex, row: EnumTableData) -> Any:
        return row.label if index.column() == 0 else row.value

    def set_cell_data(self, index: QModelIndex, row: EnumTableData, value: Any) -> bool:
        if index.column() == 0:
            row.label = value
        else:
            row.value = value
        return True

    def validate(self):
        used_codes = set()
        used_labels = set()
        for idx, item in enumerate(self._data):
            if not item.label:
                raise ValueError(f'Row #{idx+1} is lacking "Label".')
            if item.value in used_codes:
                raise ValueError(f'Enum value "{item.value}" is being used more than once.')
            if item.label in used_labels:
                raise ValueError(f'Label value "{item.label}" is being used more than once.')
            used_codes.add(item.value)
            used_labels.add(item.label)

    def _find_largest_code(self) -> int:
        return max([x.value for x in self._data] + [-1])


class UserDataColumnDelegate(QStyledItemDelegate):
    """
    Customizes field user data column to be displayed as a button for selected types.
    """

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QPushButton(parent)
        editor.clicked.connect(self._open_dialog)
        setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))
        return editor

    def setEditorData(self, editor: QPushButton, index: QModelIndex):
        if not isinstance(editor, QPushButton):
            return

        enum_config = index.data() or {}
        option_cnt = len(cast(Dict[str, List], enum_config).get("options", []))
        if option_cnt == 0:
            suffix = ""
        else:
            suffix = f" ({option_cnt} option"
            if option_cnt > 1:
                suffix += "s"
            suffix += ")"
        editor.setText("Configure" + suffix)

        if getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None) != index:
            setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))

    def displayText(self, _, __) -> str:
        # Make sure that transparent button does not expose set label underneath
        return ""

    def _open_dialog(self):
        editor = self.sender()
        index: Optional[QPersistentModelIndex] = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None)
        if index and index.isValid():
            regular_index = QModelIndex(index)  # We can't use QPersistentModelIndex to update data
            enum_config = regular_index.data() or {}
            options = cast(Dict[str, List[EnumItemConfig]], enum_config).get("options", [])
            dialog = EnumOptionsDialog(options=options,
                                       on_save=functools.partial(self._save_from_dialog, index=regular_index))
            dialog.show()
            dialog.exec_()

    def _save_from_dialog(self, data: List[EnumItemConfig], index: QModelIndex):
        value = PropertyEdit.ValueType.enum_user_data(data)
        index.model().setData(index, value)


class FieldTypeColumnDelegate(AbstractComboBoxColumnDelegate):
    """
    Customizes field type column to be displayed as a combobox.
    """

    def configure_editor(self, editor: QComboBox, _):
        for opt in PropertyEdit.ValueType:
            editor.addItem(str(opt).split(".")[-1].title(), opt)  # Otherwise it is seen as 'ValueType.SOMETHING'


class EnumOptionsDialog(AbstractTableDialog[EnumItemConfig, EnumEditorTableModel]):

    def __init__(self, options: List[EnumItemConfig], on_save: Callable[[List[EnumItemConfig]], None], parent: Optional[QObject] = None):
        """
        Dialog displaying a table to the user for editing configuration of the ENUM field.

        Args:
            options: Setup for the combobox options.
            on_save: Callback to accept updated values.
            parent: Parent item for the dialog.
        """
        table_model = EnumEditorTableModel(data=list(map(EnumTableData.from_enum_item_config, options)))
        super().__init__(table_model=table_model, parent=parent)
        TableViewColumnResizer.install_onto(self.table)
        self._on_save = on_save

        self.setWindowTitle("Configure enum options")

        self.resize(400, 200)

    def on_save(self):
        self._on_save([row.to_enum_item_config() for row in self._table_model.raw_data])


class FieldsDialog(AbstractTableDialog[PropertyEditField, FieldEditorTableModel]):

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
        super().__init__(file_path=Path(__file__).absolute().parent / "field_editor.ui", table_model=table_model, parent=parent)
        self._widget = widget
        TableViewColumnResizer.install_onto(self.table)

        self.setWindowTitle("Define PropertyEdit fields")

        self.all_rw.clicked.connect(functools.partial(self._table_model.set_fields_editable, True))
        self.all_ro.clicked.connect(functools.partial(self._table_model.set_fields_editable, False))

        # This will be connected by default, but we do want to do additional validation,
        # so we need to prevent automatic closing
        self.buttons.accepted.disconnect(self.accept)

        self.table.model().dataChanged.connect(self._on_data_change)
        self.table.setItemDelegateForColumn(1, FieldTypeColumnDelegate(self.table))
        self.table.setItemDelegateForColumn(2, BooleanPropertyColumnDelegate(self.table))
        self.table.setItemDelegateForColumn(4, UserDataColumnDelegate(self.table))
        self.table.set_persistent_editor_for_column(1)
        self.table.set_persistent_editor_for_column(2)
        self.table.set_persistent_editor_for_column(4)

        # Recalculate button states
        self._on_data_change()

        self.resize(800, 300)

    def on_save(self):
        cursor = get_designer_cursor(self._widget)
        if cursor:
            cursor.setProperty("fields", _pack_designer_fields(self._table_model.raw_data))

    def _on_data_change(self):
        data_prefilled = len(self._table_model.raw_data) > 0
        self.all_ro.setEnabled(data_prefilled)
        self.all_rw.setEnabled(data_prefilled)


class PropertyFieldExtension(WidgetsTaskMenuExtension):

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
