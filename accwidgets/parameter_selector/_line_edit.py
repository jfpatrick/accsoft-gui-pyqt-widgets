import qtawesome as qta
from typing import Optional, Any
from qtpy.QtGui import QPalette
from qtpy.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QSizePolicy, QPushButton, QDialog, QStyledItemDelegate,
                            QStyleOptionViewItem)
from qtpy.QtCore import (Signal, Slot, Property, QPersistentModelIndex, QAbstractTableModel, QModelIndex,
                         QSignalBlocker, QLocale, QEvent, QTimer, QObject)
from accwidgets.qt import _STYLED_ITEM_DELEGATE_INDEX
from ._dialog import ParameterSelectorDialog


class ParameterLineEdit(QWidget):

    valueChanged = Signal(str)
    """
    Fires whenever a value changes in the text field.

    :type: pyqtSignal
    """

    def __init__(self, parent: Optional[QWidget] = None, value: str = ""):
        """
        Text field for entering parameter names that has a side button to open dialog to search for parameter
        names interactively.

        Args:
            parent: Owning object.
            value: Predefined text in the field.
        """
        super().__init__(parent)
        self._enable_protocols = False
        self._enable_fields = True
        layout = QHBoxLayout()
        self._line_edit = QLineEdit(value)
        self._line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self._line_edit.setPlaceholderText("device/property#field")
        self._line_edit.textChanged.connect(self.valueChanged)
        self._btn = QPushButton()
        self._btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        self._btn.setMaximumWidth(24)
        self._btn.setMinimumWidth(24)
        self._update_icon()
        self._btn.clicked.connect(self._open_dialog)
        layout.addWidget(self._line_edit)
        layout.addWidget(self._btn)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setTabOrder(self._line_edit, self._btn)
        self.setFocusProxy(self._line_edit)

    @Slot()
    def clear(self):
        """
        Clear text field. This does not have influence over the :class:`ParameterSelectorDialog` dialog
        that has already been open.
        """
        self._line_edit.clear()
        self.valueChanged.emit(self.value)

    def _get_value(self) -> str:
        return self._line_edit.text()

    def _set_value(self, new_val: str):
        self._line_edit.setText(new_val)

    value = Property(str, fget=_get_value, fset=_set_value)
    """
    Text value displayed in the field. Setting this value will also affect the initial behavior
    of the :class:`ParameterSelectorDialog` dialog, when opened.
    """

    def _get_enable_protocols(self) -> bool:
        return self._enable_protocols

    def _set_enable_protocols(self, new_val: bool):
        self._enable_protocols = new_val

    enableProtocols = Property(bool, fget=_get_enable_protocols, fset=_set_enable_protocols)
    """Display protocol combobox in the :class:`ParameterSelectorDialog` dialog."""

    def _get_enable_fields(self) -> bool:
        return self._enable_fields

    def _set_enable_fields(self, new_val: bool):
        self._enable_fields = new_val

    enableFields = Property(bool, fget=_get_enable_fields, fset=_set_enable_fields)
    """
    Enable selection of fields in the :class:`ParameterSelectorDialog` dialog. When :obj:`False`, parameter
    selection happens only down to device property granularity.
    """

    def _get_placeholder_text(self) -> str:
        return self._line_edit.placeholderText()

    def _set_placeholder_text(self, new_val: str):
        self._line_edit.setPlaceholderText(new_val)

    placeholderText = Property(str, fget=_get_placeholder_text, fset=_set_placeholder_text)
    """Widget's placeholder text that is display as a grayed-out text as long as the input is empty."""

    def _open_dialog(self):
        dialog = ParameterSelectorDialog(initial_value=self._line_edit.text(),
                                         enable_protocols=self.enableProtocols,
                                         enable_fields=self.enableFields,
                                         parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._line_edit.setText(dialog.value)

    def event(self, event: QEvent) -> bool:
        """
        This event handler is reimplemented to react to the external style change, e.g. via QSS, to adjust
        colors painted in the button icon.

        This is the main event handler; it handles event ``event``. You can reimplement this function in a
        subclass, but we recommend using one of the specialized event handlers instead.

        Args:
            event: Handled event.

        Returns:
            :obj:`True` if the event was recognized, otherwise it returns :obj:`False`. If the recognized event
            was accepted (see :meth:`QEvent.accepted`), any further processing such as event propagation to the
            parent widget stops.
        """
        res = super().event(event)
        if event.type() == QEvent.StyleChange:
            # Update this at the end of the event loop, when palette has been synchronized with the updated style
            QTimer.singleShot(0, self._update_icon)
        return res

    def _update_icon(self):
        self._btn.setIcon(qta.icon("fa.search", color=self.palette().color(QPalette.Text)))
        # self.setIcon(qta.icon("mdi.format-list-bulleted-type", color=self.palette().color(QPalette.Text)))


class ParameterLineEditColumnDelegate(QStyledItemDelegate):

    def __init__(self, parent: Optional[QObject] = None,
                 enable_protocols: bool = False,
                 enable_fields: bool = True,
                 placeholder: Optional[str] = None):
        """
        Delegate to render a  :class:`ParameterLineEdit` widget in the cell.

        Args:
            parent: Owning object.
            enable_protocols: Allow selecting protocols.
            enable_fields: Allow selecting fields.
            placeholder: Placeholder text for the :class:`ParameterLineEdit`. :obj:`None` will leave the default value.
        """
        super().__init__(parent)
        self._enable_protocols = enable_protocols
        self._enable_fields = enable_fields
        self._placeholder = placeholder

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = ParameterLineEdit(parent)
        editor.valueChanged.connect(self._val_changed)
        editor.enableProtocols = self._enable_protocols
        editor.enableFields = self._enable_fields
        if self._placeholder is not None:
            editor.placeholderText = self._placeholder
        setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))
        return editor

    def setEditorData(self, editor: ParameterLineEdit, index: QModelIndex):
        if not isinstance(editor, ParameterLineEdit):
            return

        blocker = QSignalBlocker(editor)
        editor.value = index.data()
        blocker.unblock()

        if getattr(editor, _STYLED_ITEM_DELEGATE_INDEX, None) != index:
            setattr(editor, _STYLED_ITEM_DELEGATE_INDEX, QPersistentModelIndex(index))

    def setModelData(self, editor: ParameterLineEdit, model: QAbstractTableModel, index: QModelIndex):
        if not isinstance(editor, ParameterLineEdit):
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
