import warnings
from enum import IntEnum, auto
from pathlib import Path
from typing import Optional, Set, List, TypeVar, Generic, Any
from abc import abstractmethod, ABCMeta
from qtpy.QtWidgets import (QTableView, QWidget, QAbstractItemDelegate, QMessageBox, QPushButton, QDialog, QColorDialog,
                            QDialogButtonBox, QStyledItemDelegate, QStyleOptionViewItem, QSpacerItem, QSizePolicy,
                            QHBoxLayout, QToolButton, QCheckBox, QComboBox, QHeaderView, QGraphicsItem, QFrame,
                            QApplication)
from qtpy.QtCore import (Qt, QModelIndex, QAbstractItemModel, QAbstractTableModel, QObject, QVariant,
                         QPersistentModelIndex, QLocale, Signal, Slot)
from qtpy.QtGui import QFont, QColor, QIcon, QPixmap
from qtpy.uic import loadUi
from accwidgets._generics import GenericQtMeta
from accwidgets._signal import attach_sigint


class AbstractQObjectMeta(type(QObject), ABCMeta):  # type: ignore
    """
    Metaclass for abstract classes based on :class:`QObject`.

    A class inheriting from :class:`QObject` with :class:`~abc.ABCMeta` as metaclass will lead to
    an metaclass conflict:

    ``TypeError: metaclass conflict: the metaclass of a derived class must be
    a (non-strict) subclass of the meta-classes of all its bases``
    """
    pass


class AbstractQGraphicsItemMeta(type(QGraphicsItem), ABCMeta):  # type: ignore
    """
    Metaclass for abstract classes based on :class:`QGraphicsItem`.

    A class inheriting from :class:`QGraphicsItem` with :class:`~abc.ABCMeta` as metaclass will lead to
    an metaclass conflict:

    ``TypeError: metaclass conflict: the metaclass of a derived class must be
    a (non-strict) subclass of the meta-classes of all its bases``
    """
    pass


class TableViewColumnResizer(QObject):

    @classmethod
    def install_onto(cls, watched: QTableView) -> "TableViewColumnResizer":
        """
        **DEPRECATED!** Use ``QTableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)``.

        Configures the table view's horizontal header (displaying columns) to resize evenly,
        or interactively by the user.

        Args:
            watched: Table view to start monitoring.

        Returns:
            Instance of the resizer objects that's been installed.
        """
        warnings.warn(f"{cls.__name__}.install_onto is deprecated. Please use "
                      "QTableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) instead.")
        spy = cls()
        header = watched.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        return spy


class PersistentEditorTableView(QTableView):

    def __init__(self, parent: Optional[QWidget] = None):
        """
        :class:`QTableView` subclass that assumes always-editable mode for specified columns or rows.

        By default, :class:`QTableView` will allow editing content (and hence display editors) only when user clicks
        inside a cell. This works well for spreadsheet-like applications but falls short for complex editing scenarios,
        where user needs open editors at his fingertips. Even when using :class:`QStyledItemDelegate` subclasses, your
        editor will be opened by the table view only when focus in the cell. :class:`QTableWidget` offers always-editable
        workflow, where you can define any editor you want. However, it does not allow working with user-defined models.
        """
        super().__init__(parent)
        self._persistent_cols: Set[int] = set()
        self._persistent_rows: Set[int] = set()

    def setModel(self, model: QAbstractItemModel):
        """
        Sets the model for the view to present.

        This function will create and set a new selection model, replacing any model that was previously set with
        :meth:`QAbstractItemView.setSelectionModel`. However, the old selection model will not be deleted as it may
        be shared between several views. We recommend that you delete the old selection model if it is no longer
        required. If both the old model and the old selection model do not have parents, or if their parents are
        long-lived objects, it may be preferable to call their :meth:`QObject.deleteLater` functions to explicitly
        delete them.

        The view does not take ownership of the model unless it is the model's parent object because the model may
        be shared between many different views.

        Args:
            model: New model.
        """
        prev_model: QAbstractItemModel = self.model()
        model_changed = prev_model != model
        if model_changed:
            if prev_model:
                prev_model.dataChanged.disconnect(self._check_persistent_editors_for_data)
            if model:
                model.dataChanged.connect(self._check_persistent_editors_for_data)

        super().setModel(model)

        if model_changed:
            # This needs self.model() to be up to date
            self._update_all_persistent_editors()

    def setItemDelegate(self, delegate: QAbstractItemDelegate):
        """
        Sets the item delegate for this view and its model to delegate. This is useful if you want complete
        control over the editing and display of items.

        Any existing delegate will be removed, but not deleted. :class:`QAbstractItemView` does not take ownership
        of delegate.

        **Warning:** You should not share the same instance of a delegate between views. Doing so can cause
        incorrect or unintuitive editing behavior since each view connected to a given delegate may receive the
        :meth:`QAbstractItemDelegate.closeEditor` signal, and attempt to access, modify or close an editor that
        has already been closed.

        Args:
            delegate: New delegate
        """
        super().setItemDelegate(delegate)
        # Reset editorHash amongst other things, so that previously created editors of different types
        # (due to different delegate) are removed and allow creating new ones
        self.reset()

        self._update_all_persistent_editors()

    def setItemDelegateForColumn(self, column: int, delegate: QAbstractItemDelegate):
        """
        Sets the given item delegate used by this view and model for the given column. All items on column will be
        drawn and managed by delegate instead of using the default delegate (i.e.,
        :meth:`QAbstractItemView.itemDelegate`).

        Any existing column delegate for column will be removed, but not deleted. :class:`QAbstractItemView` does not
        take ownership of delegate.

        **Note:** If a delegate has been assigned to both a row and a column, the row delegate will take precedence
        and manage the intersecting cell index.

        **Warning:** You should not share the same instance of a delegate between views. Doing so can cause incorrect
        or unintuitive editing behavior since each view connected to a given delegate may receive the
        :meth:`QAbstractItemDelegate.closeEditor` signal, and attempt to access, modify or close an editor that has
        already been closed.

        Args:
            column: Column index.
            delegate: New delegate.
        """
        super().setItemDelegateForColumn(column, delegate)
        model: QAbstractItemModel = self.model()
        if model is None or column >= model.columnCount():
            return
        rows = model.rowCount()
        if rows > 0:
            # Reset editorHash amongst other things, so that previously created editors of different types
            # (due to different delegate) are removed and allow creating new ones
            self.reset()
            # We must update all, because even if delegate is set to a column not related to persistent editors,
            # they still will be closed
            self._update_all_persistent_editors()

    def setItemDelegateForRow(self, row: int, delegate: QAbstractItemDelegate):
        """
        Sets the given item delegate used by this view and model for the given row. All items on row will be drawn
        and managed by delegate instead of using the default delegate (i.e., :meth:`QAbstractItemView.itemDelegate`).

        Any existing row delegate for row will be removed, but not deleted. :class:`QAbstractItemView` does not take
        ownership of delegate.

        **Note:** If a delegate has been assigned to both a row and a column, the row delegate (i.e., this delegate)
        will take precedence and manage the intersecting cell index.

        **Warning:** You should not share the same instance of a delegate between views. Doing so can cause incorrect
        or unintuitive editing behavior since each view connected to a given delegate may receive the
        :meth:`QAbstractItemDelegate.closeEditor` signal, and attempt to access, modify or close an editor that has
        already been closed.

        Args:
            row: Row index.
            delegate: New delegate.
        """
        super().setItemDelegateForRow(row, delegate)
        model: QAbstractItemModel = self.model()
        if model is None or row >= model.rowCount():
            return
        cols = model.columnCount()
        if cols > 0:
            # Reset editorHash amongst other things, so that previously created editors of different types
            # (due to different delegate) are removed and allow creating new ones
            self.reset()
            # We must update all, because even if delegate is set to a row not related to persistent editors,
            # they still will be closed
            self._update_all_persistent_editors()

    def set_persistent_editor_for_column(self, col: int):
        """
        Marks the given column as the one possessing persistent editors.

        Args:
            col: Column index.
        """
        self._persistent_cols.add(col)
        self._update_persistent_editors_for_col(col)

    def set_persistent_editor_for_row(self, row: int):
        """
        Marks the given row as the one possessing persistent editors.

        Args:
            row: Row index.
        """
        self._persistent_rows.add(row)
        self._update_persistent_editors_for_row(row)

    def _update_persistent_editors_for_col(self, col: int):
        model = self.model()
        if model is None:
            return
        if col >= 0 and col < model.columnCount():
            for row in range(model.rowCount()):
                index = model.createIndex(row, col)
                self._manage_persistent_editor(index)

    def _update_persistent_editors_for_row(self, row: int):
        model = self.model()
        if model is None:
            return
        if row >= 0 and row < model.rowCount():
            for col in range(model.columnCount()):
                index = model.createIndex(row, col)
                self._manage_persistent_editor(index)

    def _update_all_persistent_editors(self):
        for row in self._persistent_rows:
            self._update_persistent_editors_for_row(row)
        for col in self._persistent_cols:
            self._update_persistent_editors_for_col(col)

    def _check_persistent_editors_for_data(self, top_left: QModelIndex, bottom_right: QModelIndex, roles: Optional[List[Qt.ItemDataRole]] = None):
        # In case where this slot was called after creating a new item in the model, we need to mark it
        if roles and not (Qt.DisplayRole in roles or Qt.EditRole in roles):
            return

        model = top_left.model()
        if model is None:
            model = self.model()
        if model is None:
            return
        affected_indexes: List[QModelIndex] = []
        for col in self._persistent_cols:
            if col >= top_left.column() and col <= bottom_right.column():
                affected_indexes.extend([model.createIndex(r, col) for r in range(top_left.row(), bottom_right.row() + 1)])
        for row in self._persistent_rows:
            if row >= top_left.row() and row <= bottom_right.row():
                affected_indexes.extend([model.createIndex(row, c) for c in range(top_left.column(), bottom_right.column() + 1)])

        for index in affected_indexes:
            self._manage_persistent_editor(index)

    def _manage_persistent_editor(self, index: QModelIndex):
        is_editable = index.flags() & Qt.ItemIsEditable
        if is_editable:
            self.openPersistentEditor(index)
        else:
            self.closePersistentEditor(index)


LI = TypeVar("LI")
"""Generic List Item for the list-based models."""


class AbstractListModel(Generic[LI], metaclass=GenericQtMeta):

    class ChangeType(IntEnum):
        """Circumstances when dataChanged signal is about to be called"""
        ADD_ROW = auto()
        REMOVE_ROW = auto()
        UPDATE_ITEM = auto()

    def __init__(self, data: List[LI]):
        """
        Simple model that is based on :class:`~typing.List` data structure, called ``self._data``.
        It implements common scenarios for 1-dimensional list, but does not inherit directly
        from the Qt base class, since it can be used with both :class:`QAbstractTableModel` and
        :class:`QAbstractListModel`. As a bonus, this model allows serializing data as JSON.

        Args:
            data: Initial data. It is not copied, therefore pay attention, when changing it outside
        """
        if not isinstance(self, QAbstractItemModel):
            warnings.warn(f"{AbstractListModel.__name__} must be subclassed together with {QAbstractItemModel.__name__}"
                          " or its derivative, otherwise it may break if assumed API is not present.",
                          RuntimeWarning)
        self._data = data

    def create_row(self) -> LI:
        """Create a new empty object when appending a new row to the table."""
        pass

    def rowCount(self, _: Optional[QModelIndex] = None) -> int:
        """Returns the number of rows under the given parent."""
        return len(self._data)

    def append_row(self):
        """Append a new empty row to the model."""
        new_row = self.create_row()
        if new_row is None:
            # Method was not overridden, assume the table does not support adding new items (only fixed contents)
            return

        new_row_idx = self.rowCount()
        self.beginInsertRows(QModelIndex(), new_row_idx, new_row_idx)  # type: ignore   # presuming QAbstractItemView super
        self._data.append(new_row)
        self.endInsertRows()  # type: ignore   # presuming QAbstractItemView super
        new_row_idx = len(self._data) - 1
        new_index = self.createIndex(new_row_idx, 0)
        self.notify_change(start=new_index, end=new_index, action_type=self.ChangeType.ADD_ROW)

    def remove_row_at_index(self, index: QModelIndex):
        """
        Remove a row in the data model by a given index.

        Args:
            index: Index of row, which needs to be removed.
        """
        removed_idx = index.row()
        self.beginRemoveRows(QModelIndex(), removed_idx, removed_idx)  # type: ignore   # presuming QAbstractItemView super
        del self._data[removed_idx]
        self.endRemoveRows()  # type: ignore   # presuming QAbstractItemView super
        self.notify_change(start=QModelIndex(), end=QModelIndex(), action_type=self.ChangeType.REMOVE_ROW)

    def notify_change(self, start: QModelIndex, end: QModelIndex, action_type: "AbstractListModel.ChangeType"):
        """
        Use this method to emit dataChanged signal. Based on the action type, you may decide which indices to use
        for notification, in order to optimally refresh the table.

        Default implementation simply calls the signal, but you may changed that.

        Args:
            start: Start index of the data changed notification.
            end: End index of the data changed notification.
            type: Type of the action that caused this.
        """
        _ = action_type
        self.dataChanged.emit(start, end)  # type: ignore   # presuming QAbstractItemView super

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        """
        Get Data from the table's model by a given index.

        Args:
            index: row & column in the table
            role: which property is requested

        Returns:
            Data associated with the passed index
        """
        # EditRole is essential for default QStyledDelegate implementations to correctly pick up the type
        # DisplayRole is essential for custom delegates to display the value
        if (not index.isValid()
                or role not in [Qt.DisplayRole, Qt.EditRole]
                or index.row() >= len(self._data)):
            return QVariant()
        row = self._data[index.row()]
        return row

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = Qt.EditRole) -> bool:
        """
        Set Data to the tables data model at the given index.

        Args:
            index: Position of the new value
            value: new value
            role: which property is requested

        Returns:
            True if the data could be successfully set.
        """
        if (not index.isValid()
                or role != Qt.EditRole
                or index.row() >= len(self._data)):
            return False
        self._data[index.row()] = value
        self.notify_change(start=index, end=index, action_type=self.ChangeType.UPDATE_ITEM)
        return True

    def validate(self):
        """
        Validate the model before saving it to file. Throw :exc:`ValueError` on any problem that you find.

        Raises:
            ValueError: Whenever a problem is detected with the data model.
        """
        pass

    @property
    def raw_data(self) -> List[LI]:
        """Getter for the internal data structure."""
        return self._data


class AbstractTableModel(AbstractListModel[LI], QAbstractTableModel, Generic[LI], metaclass=GenericQtMeta):

    def __init__(self, data: List[LI], parent: Optional[QObject] = None):
        """
        Base class for the models used in the table, this is a more high-level abstraction than list-based model.
        Note! Use with caution, as it is somewhat more opinionated than a more liberal superclass implementation.

        Args:
            data: Initial data.
            parent: Owning object.
        """
        AbstractListModel.__init__(self, data=data)
        QAbstractTableModel.__init__(self, parent)

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
    def get_cell_data(self, index: QModelIndex, row: LI) -> Any:
        """
        Data at the given row, for any column except the first, which is reserved. Whenever this method is called,
        all the checks are passed, so index is guaranteed to be valid.

        Args:
            index: Index to fetch.
            row: A data entry at that row.

        Returns:
            The data for the cell.
        """
        pass

    @abstractmethod
    def set_cell_data(self, index: QModelIndex, row: LI, value: Any) -> bool:
        """
        Update data at the given row, for any column except the first, which is reserved.
        Whenever this method is called, all the checks are passed, so index is guaranteed to be valid.

        Args:
            index: Index to fetch.
            row: A data entry at that row.
            value: Value to set.

        Returns:
            ``True`` if data was updated.
        """
        pass

    def notify_change(self, start: QModelIndex, end: QModelIndex, action_type: "AbstractListModel.ChangeType"):
        if action_type == self.ChangeType.ADD_ROW:
            # Expand end index for all columns, not only the first, as defined by parent 1D list model.
            new_end = self.createIndex(end.row(), self.columnCount() - 1)
            super().notify_change(start=start, end=new_end, action_type=action_type)
        else:
            super().notify_change(start=start, end=end, action_type=action_type)

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
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
            Header Data (e.g. name) for the row / column
        """
        if role != Qt.DisplayRole:
            return super().headerData(section, orientation, role)
        if orientation == Qt.Horizontal and section < self.columnCount():
            return self.column_name(section)
        elif orientation == Qt.Vertical and section < self.rowCount():
            return f" {str(section + 1)} "
        return ""

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        row = super().data(index, role)
        if isinstance(row, QVariant):
            return row
        return self.get_cell_data(index=index, row=row)

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        row = self._data[index.row()]
        changed = self.set_cell_data(index=index, row=row, value=value)
        if changed:
            self.notify_change(start=index, end=index, action_type=self.ChangeType.UPDATE_ITEM)
        return changed

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Flags to render the table cell editable / selectable / enabled.

        Args:
            index: Position of the cell.

        Returns:
            Flags how to render the cell.
        """
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable


DM = TypeVar("DM", bound=AbstractTableModel)
"""Generic Table model used in :class:`AbstractTableDialog`."""


class AbstractTableDialog(QDialog, Generic[LI, DM], metaclass=GenericQtMeta):

    def __init__(self, table_model: DM, file_path: Optional[Path] = None, parent: Optional[QObject] = None):
        """
        Base Dialog class for displaying dialog with a table view, where rows can be added or removed.

        Args:
            table_model: Table model object.
            file_path: Path to Qt Designer file. If not provided, 'table_dialog.ui' will be used.
            parent: Parent item for the dialog.
        """
        super().__init__(parent)

        self.add_btn: QPushButton = None
        self.remove_btn: QPushButton = None
        self.buttons: QDialogButtonBox = None
        self.table: PersistentEditorTableView = None  # type: ignore  # mypy doesn't get the trick, like with PyQt classes

        if file_path is None:
            file_path = Path(__file__).absolute().parent / "table_dialog.ui"

        loadUi(str(file_path), self)

        self.add_btn.clicked.connect(self._add_row)
        self.remove_btn.clicked.connect(self._del_row)
        self.remove_btn.setEnabled(False)
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.close)

        self._table_model = table_model
        self.table.setModel(self._table_model)
        self.table.selectionModel().selectionChanged.connect(self._on_selection)

    @abstractmethod
    def on_save(self):
        """
        Method that is called when validations have passed and the dialog is about to close.

        Here is a good time to send the updated data to the original owner.
        """
        pass

    def _on_selection(self):
        is_removable = self.table.selectionModel().hasSelection()
        self.remove_btn.setEnabled(is_removable)

    def _add_row(self):
        self._table_model.append_row()

    def _del_row(self):
        self._table_model.remove_row_at_index(self.table.currentIndex())

    def _save(self):
        try:
            self._table_model.validate()
        except Exception as ex:  # noqa: B902
            # We must catch all types of exceptions here, even though we target ValueError only,
            # Because otherwise it will abort python interpreter due to exceptions in virtual methods
            # See https://pytest-qt.readthedocs.io/en/latest/virtual_methods.html for details.
            QMessageBox.warning(self, "Invalid data" if isinstance(ex, ValueError) else "Unexpected error", str(ex))
            return

        self.on_save()
        self.accept()


_STYLED_ITEM_DELEGATE_INDEX = "_accwidgets_persistent_index_"


class AbstractComboBoxColumnDelegate(QStyledItemDelegate, metaclass=AbstractQObjectMeta):
    """
    Delegate to render a configurable combobox in the cell.
    """

    @abstractmethod
    def configure_editor(self, editor: QComboBox, model: QAbstractItemModel):
        """
        Method to configure the options in the combobox. Use "userData" field to store the values that
        will be communicated to the model. E.g.

        >>> for opt_label, opt_value in my_options:
        >>>     editor.addItem(opt_label, opt_value)

        Args:
            editor: Combobox to configure.
        """

    def model_to_user_data(self, value: Any) -> Any:
        """Hook to convert the raw model value, into user data stored in the combo box."""
        return value

    def user_data_to_model(self, value: Any) -> Any:
        """
        Hook to convert the combo box user data to the model acceptable value.

        Raise :class:`ValueError` if the value can't be converted and the model should not be updated.

        Raises:
            ValueError: value can't be converted and the model should not be updated.
        """
        return value

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QComboBox(parent)
        self.configure_editor(editor, index.model())
        editor.activated.connect(self._val_changed)
        setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))
        return editor

    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        if not isinstance(editor, QComboBox):
            return
        value = self.model_to_user_data(index.data())
        opt_idx = editor.findData(value)
        if opt_idx != -1:
            editor.setCurrentIndex(opt_idx)
        if index != getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None):
            setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))

    def setModelData(self, editor: QComboBox, model: QAbstractTableModel, index: QModelIndex):
        if not isinstance(editor, QComboBox):
            return
        try:
            new_val = self.user_data_to_model(editor.currentData())
        except ValueError:
            return
        model.setData(index, new_val)

    def _val_changed(self):
        editor = self.sender()
        index: Optional[QPersistentModelIndex] = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None)
        if not index or not index.isValid():
            return
        self.setModelData(editor, index.model(), QModelIndex(index))


class BooleanButton(QToolButton):

    value_changed = Signal()
    """Boolean value has been updated by the user."""

    def __init__(self, parent: Optional[QObject] = None):
        """
        Button used to set a boolean flag in a table.

        This is a slicker-looking implementation, as the default behavior sets Combobox (True/False) in the table.

        Args:
            parent: Owning object.
        """
        super().__init__(parent)
        self.setAutoRaise(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        checkbox = QCheckBox(self)
        checkbox.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.clicked.connect(self._toggle)
        layout.addSpacerItem(QSpacerItem(10, 1, QSizePolicy.Expanding, QSizePolicy.Preferred))
        layout.addWidget(checkbox)
        layout.addSpacerItem(QSpacerItem(10, 1, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.setLayout(layout)
        self._checkbox = checkbox

    @property
    def value(self) -> bool:
        """Boolean value."""
        return self._checkbox.isChecked()

    @value.setter
    def value(self, new_val: bool):
        self._checkbox.setCheckState(Qt.Checked if new_val else Qt.Unchecked)

    def _toggle(self):
        self._checkbox.toggle()
        self.value_changed.emit()


class BooleanPropertyColumnDelegate(QStyledItemDelegate):
    """
    Table delegate that draws :class:`BooleanButton` widget in the cell.
    """

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = BooleanButton(parent)
        editor.value_changed.connect(self._val_changed)
        setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))
        return editor

    def setEditorData(self, editor: BooleanButton, index: QModelIndex):
        if not isinstance(editor, BooleanButton):
            return

        editor.value = bool(index.data())
        if getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None) != index:
            setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))

    def setModelData(self, editor: BooleanButton, model: QAbstractTableModel, index: QModelIndex):
        if not isinstance(editor, BooleanButton):
            return
        index.model().setData(index, editor.value)

    def displayText(self, value: Any, locale: QLocale) -> str:
        # Make sure that transparent button does not expose set label underneath
        return ""

    def _val_changed(self):
        editor = self.sender()
        index: Optional[QPersistentModelIndex] = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None)
        if index and index.isValid():
            self.setModelData(editor, index.model(), QModelIndex(index))


class ColorButton(QToolButton):

    def __init__(self, parent: Optional[QObject] = None):
        """
        Button that opens a picker and displays the selected color using the RBG hex, as well as a thumbnail
        with background color corresponding to the picked color.

        Args:
            parent: Owning object.
        """
        super().__init__(parent)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.setFont(font)
        self.setAutoRaise(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 0, 0)
        icon = QFrame(self)
        icon.setFrameStyle(QFrame.Box)
        icon.resize(10, 10)
        icon.setMinimumSize(10, 10)
        icon.setMaximumSize(10, 10)
        layout.addWidget(icon)
        layout.addSpacerItem(QSpacerItem(10, 1, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self._color_thumb = icon
        self.setLayout(layout)
        self.color = "#000000"

    @property
    def color(self) -> str:
        """Currently selected color, in RGB hex notation."""
        return self.text()

    @color.setter
    def color(self, new_val: str):
        name = QColor(new_val).name()  # Transform things like 'red' or 'darkblue' to HEX
        self.setText(name.upper())
        self._color_thumb.setStyleSheet(f"background-color: {new_val}")


class ColorPropertyColumnDelegate(QStyledItemDelegate):
    """
    Table delegate that draws :class:`ColorButton` widget in the cell.
    """

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = ColorButton(parent)
        editor.clicked.connect(self._open_color_dialog)
        setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))
        return editor

    def setEditorData(self, editor: ColorButton, index: QModelIndex):
        if not isinstance(editor, ColorButton):
            return
        editor.color = str(index.data())
        if getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None) != index:
            setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))

    def setModelData(self, editor: QWidget, model: QAbstractTableModel, index: QModelIndex):
        # Needs to be overridden so that underlying implementation does not set garbage data to the model
        # This delegate is read-only, as we don not propagate value to the model from the editor, but rather
        # open the dialog ourselves.
        pass

    def displayText(self, value: Any, locale: QLocale) -> str:
        # Make sure that transparent button does not expose set label underneath
        return ""

    def _open_color_dialog(self):
        # This can't be part of the ColorButton, as sometimes it gets deallocated by the table, while color dialog
        # is open, resulting in C++ deallocation, while Python logic is in progress. Therefore, we keep it in the
        # delegate, that exists as long as table model exists.
        editor: ColorButton = self.sender()
        index: Optional[QPersistentModelIndex] = getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None)
        if not index or not index.isValid():
            return
        new_color = QColorDialog.getColor(QColor(str(index.data())))
        if not new_color.isValid():
            # User cancelled the selection
            return
        new_name = new_color.name()
        index.model().setData(QModelIndex(index), new_name)


class OrientedToolButton(QToolButton):

    def __init__(self,
                 primary: QSizePolicy,
                 secondary: QSizePolicy,
                 orientation: Qt.Orientation = Qt.Horizontal,
                 parent: Optional[QWidget] = None):
        """
        Toolbar button that changes (swaps) it's resizing policies based on the toolbar :meth:`~QToolBar.orientation`.

        Args:
            primary: Horizontal size policy in the `Qt.Horizontal` orientation, otherwise acts as a vertical size policy.
            secondary: Vertical size policy in the `Qt.Horizontal` orientation, otherwise acts as a horizontal size policy.
            orientation: Initial orientation.
            parent: Owning object.
        """
        super().__init__(parent)
        self._primary_policy = primary
        self._secondary_policy = secondary
        self.setOrientation(orientation)

    @Slot(Qt.Orientation)
    def setOrientation(self, new_val: Qt.Orientation):
        """
        Update size policies according to the new orientation.

        Args:
            new_val: New orientation.
        """
        if new_val == Qt.Horizontal:
            self.setSizePolicy(self._primary_policy, self._secondary_policy)
        else:
            self.setSizePolicy(self._secondary_policy, self._primary_policy)


def make_icon(path: Path) -> QIcon:
    """Shortcut to create :class:`QIcon` objects from their image paths."""
    if not path.is_file():
        warnings.warn(f"Icon '{str(path)}' cannot be found")
    pixmap = QPixmap(str(path))
    return QIcon(pixmap)


def exec_app_interruptable(app: QApplication) -> int:
    """
    Run PyQt application's main event loop, while ensuring that application can be terminated using Ctrl+C sequence.

    Args:
        app: Main application instance.

    Returns:
        Value that was set during exit call, e.g. ``0`` if called via :meth:`QApplication.quit`.
    """
    attach_sigint(app)
    return app.exec_()
