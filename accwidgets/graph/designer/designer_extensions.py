import enum
from typing import Union, Optional, Tuple, List, cast, Dict
import json

from qtpy.QtCore import QAbstractTableModel, Qt, QVariant, Slot, QItemSelection, QModelIndex, QObject
from qtpy.QtGui import QResizeEvent
from qtpy.QtDesigner import QDesignerFormWindowInterface
from qtpy.QtWidgets import (
    QDialog,
    QAction,
    QDialogButtonBox,
    QPushButton,
    QSpacerItem,
    QVBoxLayout,
    QTableView,
    QAbstractItemView,
    QSizePolicy,
    QHBoxLayout,
)

from accwidgets import graph as accgraph
from accwidgets.designer_base import WidgetsExtension


class AxisEditorTableModelColumnNames(enum.Enum):

    """Central enum to define column names."""

    axis_identifier = "Axis Identifier"
    axis_label = "Axis Label"
    axis_auto_range = "Auto Range"
    view_range_min = "View Range Min"
    view_range_max = "View Range Max"


class LayerEditorTmpValues:

    def __init__(self, plot: accgraph.ExPlotWidget):
        """
        We want to wait until the user clicks the 'DONE' button in the layer
        editing dialog, before we apply the values back to the actual plot
        we are editing. This way we can cancel our changes.

        For this, this class offers a way to store the potential values passed
        to the plots properties, which are involved when editing layers.
        """
        # we take the class that has the properties for auto-completion purposes
        self._plot: accgraph.ExPlotWidgetProperties = cast(accgraph.ExPlotWidgetProperties, plot)
        self.layer_ids: List[str] = []
        self.axis_labels: Dict[str, str] = {}
        self.axis_ranges: Dict[str, Union[str, Tuple[float, float]]] = {}
        self._setup()

    def apply(self):
        """Apply the current values to the plot"""
        self._plot.layerIDs = self.layer_ids
        self._plot.axisLabels = json.dumps(self.axis_labels)
        self._plot.axisRanges = json.dumps(self.axis_ranges)

    @property
    def plot(self) -> Union[accgraph.ExPlotWidgetProperties, accgraph.ExPlotWidget]:
        """The Plot the Table model is based on."""
        return self._plot

    def remove_layer(self, layer: Union[int, str]) -> None:
        """
        Removing a layer requires also removing potential entries in the other
        values which reference the removed layer. This function bundles this
        so the user does not have to delete those obsolete reference by hand.

        Args:
            layer: Identifier or index of the layer which should be removed
        """
        if isinstance(layer, int):
            layer = self.layer_ids[layer]
        self.layer_ids.remove(layer)
        for dct in [self.axis_labels, self.axis_ranges]:
            if cast(Dict, dct).get(layer) is not None:
                del cast(Dict, dct)[layer]

    def _setup(self):
        """Get all initial values from the plot, on which we operate on."""
        self.layer_ids = self._plot.layerIDs
        self.axis_labels = json.loads(self._plot.axisLabels)
        self.axis_ranges = json.loads(self._plot.axisRanges)


class LayerEditorTableModel(QAbstractTableModel):

    default_axes: Tuple[str, str] = ("x", "y")
    axis_auto_range_key: str = "auto"
    default_view_range: Tuple[int, int] = (0, 1)

    def __init__(self, plot: accgraph.ExPlotWidget, parent: QObject = None):
        """
        Data Model for the Layer Editing Table of Plot Widgets.

        Args:
            plot: Plot the data model is based on
            parent: Parent Widget
        """
        super(QAbstractTableModel, self).__init__(parent=parent)
        self._tmp = LayerEditorTmpValues(plot)
        self.columns: Tuple[AxisEditorTableModelColumnNames, ...] = (
            AxisEditorTableModelColumnNames.axis_identifier,
            AxisEditorTableModelColumnNames.axis_label,
            AxisEditorTableModelColumnNames.axis_auto_range,
            AxisEditorTableModelColumnNames.view_range_min,
            AxisEditorTableModelColumnNames.view_range_max,
        )

    def apply_to_plot(self) -> None:
        """
        Apply the current values of the temporary value storage to
        the plot it is based on.
        """
        self._tmp.apply()

    @property
    def plot(self) -> Union[accgraph.ExPlotWidgetProperties, accgraph.ExPlotWidget]:
        """The Plot the Table model is based on."""
        return self._tmp.plot

    @plot.setter
    def plot(self, new_plot: accgraph.ExPlotWidget) -> None:
        """
        The Plot the Table model is based on.

        Args:
            new_plot: Plot which will replace the old plot in the table model
        """
        self.beginResetModel()
        self._tmp = LayerEditorTmpValues(new_plot)
        self.endResetModel()

    @property
    def all_axes(self) -> List[str]:
        """All axes of the plot, including default and additional ones"""
        return list(self.default_axes) + self._tmp.layer_ids

    # Implementation of Interfaces etc.

    def flags(self, index: QModelIndex) -> int:
        """
        Flags to render the table cell editable / selectable / enabled.

        Args:
            index: Position of the cell.

        Returns:
            Flags how to render the cell.
        """
        column = self.columns[index.column()]
        row = index.row()
        if column == AxisEditorTableModelColumnNames.axis_identifier and row <= 1:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if (
            column in (AxisEditorTableModelColumnNames.view_range_min, AxisEditorTableModelColumnNames.view_range_max)
            and self._get_axis_auto_range(axis=self.all_axes[index.row()])
        ):
            # If auto range is enabled for the axis, disable manual range cells
            return Qt.ItemIsSelectable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def rowCount(self, _: QModelIndex = None) -> int:
        """Row Count for the table = default x axis, default y axis, y axes of layers."""
        return len(self.all_axes)

    def columnCount(self, _: QModelIndex = None) -> int:
        """Column Count for the Table."""
        return len(self.columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> str:
        """Return the columns name.

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
            return self.columns[section].value
        elif orientation == Qt.Vertical and section < self.rowCount():
            return str(section)
        return ""

    def append(self):
        """Append a new layer to the plot."""
        self.beginInsertRows(QModelIndex(), len(self.all_axes), len(self.all_axes))
        self._tmp.layer_ids.append(self._next_layer_id())
        self.endInsertRows()

    def _next_layer_id(self) -> str:
        i = 0
        while f"y_{i}" in self._tmp.layer_ids:
            i += 1
        return f"y_{i}"

    def remove_at_index(self, index: QModelIndex) -> None:
        """
        Remove a layer in the data model by a given index.

        Args:
            index: Index of row, which represents the layer which should be removed.
        """
        layer_index = index.row() - len(self.default_axes)
        if layer_index >= 0:
            self.beginRemoveRows(QModelIndex(), index.row(), index.row())
            self._tmp.remove_layer(layer_index)
            self.endRemoveRows()

    def data(
            self,
            index: QModelIndex,
            role: Qt.ItemDataRole = Qt.DisplayRole,
    ) -> Union[QVariant, str, float, float]:
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
            return self._get_data(index=index)
        return QVariant()

    def setData(
            self,
            index: QModelIndex,
            value=Union[float, str],
            role: Qt.ItemDataRole = Qt.EditRole,
    ) -> bool:
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
            self._set_data(value=value, index=index)
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    # Getter and Setter for Column Values:

    def _get_data(self, index: QModelIndex) -> Union[QVariant, str, float, bool]:
        column_name = self.columns[index.column()]
        axis = self.all_axes[index.row()]
        if column_name == AxisEditorTableModelColumnNames.axis_identifier:
            return axis
        if column_name == AxisEditorTableModelColumnNames.axis_label:
            return self._get_axis_label(axis=axis)
        if column_name == AxisEditorTableModelColumnNames.axis_auto_range:
            return self._get_axis_auto_range(axis=axis)
        if column_name == AxisEditorTableModelColumnNames.view_range_min:
            return self._get_view_range(axis=axis)[0]
        if column_name == AxisEditorTableModelColumnNames.view_range_max:
            return self._get_view_range(axis=axis)[1]
        return QVariant()

    def _set_data(self, index: QModelIndex, value: Union[float, str, bool, QVariant]) -> None:
        if isinstance(value, QVariant):
            value = value.toString()
        column = self.columns[index.column()]
        axis = self.all_axes[index.row()]
        if column == AxisEditorTableModelColumnNames.axis_identifier:
            self._set_axis_identifier(axis=axis, identifier=cast(str, value))
        if column == AxisEditorTableModelColumnNames.axis_label:
            self._set_axis_label(axis=axis, label=cast(str, value))
        if column == AxisEditorTableModelColumnNames.axis_auto_range:
            self._set_axis_auto_range(axis=axis, auto_range=cast(bool, value))
        if column == AxisEditorTableModelColumnNames.view_range_min:
            self._set_view_range(axis=axis, vr_min=cast(float, value))
        if column == AxisEditorTableModelColumnNames.view_range_max:
            self._set_view_range(axis=axis, vr_max=cast(float, value))

    def _set_axis_identifier(self, axis: str, identifier: str) -> None:
        # Make sure the identifier is not yet taken by another layer
        id_reserved = identifier in self.default_axes
        id_taken = self._tmp.layer_ids.count(identifier) != 0
        if not (id_reserved or id_taken):
            old_label = self._tmp.axis_labels.get(axis)
            old_range = self._tmp.axis_ranges.get(axis)
            if old_label is not None:
                self._tmp.axis_labels[identifier] = old_label
                del self._tmp.axis_labels[axis]
            if old_range is not None:
                self._tmp.axis_ranges[identifier] = old_range
                del self._tmp.axis_ranges[axis]
            self._tmp.layer_ids = [identifier if x == axis else x for x in self._tmp.layer_ids]

    def _get_axis_label(self, axis: str) -> str:
        axes_labels = self._tmp.axis_labels
        if axis in self._tmp.layer_ids:
            label = axes_labels.get(axis, "")
        elif axis == self.default_axes[0]:
            label = axes_labels.get("bottom", axes_labels.get("top", ""))
        elif axis == self.default_axes[1]:
            label = axes_labels.get("left", axes_labels.get("right", ""))
        return label

    def _set_axis_label(self, axis: str, label: str) -> None:
        label = label.strip()
        if axis in self._tmp.layer_ids:
            self._tmp.axis_labels.update({axis: label})
        elif axis == self.default_axes[0]:
            self._tmp.axis_labels.update({"bottom": label})
            self._tmp.axis_labels.update({"top": label})
        elif axis == self.default_axes[1]:
            self._tmp.axis_labels.update({"left": label})
            self._tmp.axis_labels.update({"right": label})

    def _get_axis_auto_range(self, axis: str) -> bool:
        return self._tmp.axis_ranges.get(axis) == self.axis_auto_range_key

    def _set_axis_auto_range(self, axis: str, auto_range: bool) -> None:
        if auto_range:
            self._tmp.axis_ranges.update({axis: self.axis_auto_range_key})
        elif auto_range != self._tmp.axis_ranges.get(axis):
            self._tmp.axis_ranges.update({axis: self.default_view_range})

    def _get_view_range(self, axis: str) -> Tuple[float, float]:
        view_range = self._tmp.axis_ranges.get(axis, self.default_view_range)
        if view_range == self.axis_auto_range_key:
            return self.default_view_range
        return cast(Tuple[float, float], view_range)

    def _set_view_range(
            self,
            axis: str,
            vr_min: Optional[float] = None,
            vr_max: Optional[float] = None,
    ) -> None:
        current_range = list(self._tmp.axis_ranges.get(axis, self.default_view_range))
        if vr_min is not None:
            current_range[0] = vr_min
        if vr_max is not None:
            current_range[1] = vr_max
        self._tmp.axis_ranges[axis] = cast(Tuple[float, float], tuple(current_range))


class PlotLayerEditingDialog(QDialog):

    def __init__(self, plot: accgraph.ExPlotWidget, parent: QObject = None):
        """
        Dialog displaying a table to the user for editing the plots layers.

        Args:
            plot: Plot that will be the base of the tables data model
            parent: Parent item for the dialog
        """
        super().__init__(parent)
        self.plot: accgraph.ExPlotWidget = plot
        self.setup_ui()
        self.layer_table_model = LayerEditorTableModel(self.plot)
        self.layer_table_view.setModel(self.layer_table_model)
        self.layer_table_model.plot = plot
        # self.table_view.resizeColumnsToContents()
        self.add_button.clicked.connect(self.add_layer)
        self.remove_button.clicked.connect(self.remove_selected_layer)
        self.remove_button.setEnabled(False)
        self.layer_table_view.selectionModel().selectionChanged.connect(
            self.handleSelectionChange)
        plot_name = " ".join([s.capitalize() for s in self.plot.plotItem.plot_config.plotting_style.name.split("_")])
        self.setWindowTitle(f"Edit Axes of {plot_name}")
        self.resize(600, 300)
        self.show()

    def setup_ui(self) -> None:
        """Setup the content of the dialog."""
        # Table and Vertical Layout
        self.vertical_layout = QVBoxLayout(self)
        self.layer_table_view = QTableView(self)
        self.layer_table_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.layer_table_view.setProperty("showDropIndicator", False)
        self.layer_table_view.setDragDropOverwriteMode(False)
        self.layer_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.layer_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layer_table_view.setSortingEnabled(False)
        self.layer_table_view.verticalHeader().setVisible(False)
        self.vertical_layout.addWidget(self.layer_table_view)
        # Add and Remove Button
        self.add_remove_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)
        self.add_remove_layout.addItem(spacer)
        self.add_button = QPushButton("Add Axis", self)
        self.add_remove_layout.addWidget(self.add_button)
        self.remove_button = QPushButton("Remove Axis", self)
        self.add_remove_layout.addWidget(self.remove_button)
        self.vertical_layout.addLayout(self.add_remove_layout)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.addButton(QDialogButtonBox.Cancel)
        self.button_box.addButton(QDialogButtonBox.Apply)
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self.saveChanges)
        self.button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.vertical_layout.addWidget(self.button_box)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        There seems to be no built in functionality to strech columns
        equally, so we have to implement it ourself on a resive event.

        Args:
            event: Resizing Event
        """
        column_count = self.layer_table_view.model().columnCount()
        for i in range(column_count):
            self.layer_table_view.setColumnWidth(i, int(self.width() / column_count) - 5)
        super().resizeEvent(event)

    @Slot()
    def add_layer(self):
        """Add a new layer to the plot."""
        self.layer_table_model.append()

    @Slot()
    def remove_selected_layer(self):
        """Remove a layer at index, where the view's selection currently is placed"""
        self.layer_table_model.remove_at_index(self.layer_table_view.currentIndex())

    @Slot()
    def saveChanges(self):
        """
        When hitting the Done button we have to set these properties
        explicitly in order for them to be correctly saved in UI Files.
        Before we do that, we have to tell the table data model as well, that
        we have to apply our temporary values to the actual plot.
        """
        self.layer_table_model.apply_to_plot()
        formWindow = QDesignerFormWindowInterface.findFormWindow(self.plot)
        if formWindow:
            formWindow.cursor().setProperty("layerIDs", self.plot.layerIDs)
            formWindow.cursor().setProperty("axisRanges", self.plot.axisRanges)
            formWindow.cursor().setProperty("axisLabels", self.plot.axisLabels)
        self.accept()

    @Slot(QItemSelection, QItemSelection)
    def handleSelectionChange(self, _selected: QItemSelection, _deselected: QItemSelection):
        """
        Depending on which layer is selected, enable or disable the remove button.

        Args:
            _selected: Current selection (not used in implementation)
            _deselected: Selection previous to the current one (not used in implementation)
        """
        removable = self.layer_table_view.selectionModel().hasSelection() \
            and self.layer_table_view.selectionModel().currentIndex().row() \
            >= len(LayerEditorTableModel.default_axes)
        self.remove_button.setEnabled(removable)


class PlotLayerExtension(WidgetsExtension):

    def __init__(self, widget: accgraph.ExPlotWidget):
        """
        Task Menu Extension for Editing a Plots Layer through a dialog.

        Args:
            widget: Plot Widget the extension is associated with
        """
        super().__init__(widget)
        self.edit_layer_action = QAction("Edit Axes...", self.widget)
        self.edit_layer_action.triggered.connect(self.edit_curves)

    def edit_curves(self, _):
        """Creates a new PlotLayerEditingDialog and starts its event loop."""
        edit_curves_dialog = PlotLayerEditingDialog(self.widget, parent=self.widget)
        edit_curves_dialog.exec_()

    def actions(self):
        """Actions associated with this extension."""
        return [self.edit_layer_action]
