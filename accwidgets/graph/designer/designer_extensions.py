import json
import warnings
from sys import float_info
from dataclasses import dataclass
from typing import Union, Optional, Tuple, List, cast, Dict, Any
from qtpy.QtCore import Qt, QModelIndex, QObject, QVariant, QLocale
from qtpy.QtWidgets import QAction, QWidget, QDoubleSpinBox, QStyleOptionViewItem, QStyledItemDelegate
from accwidgets.graph import ExPlotWidget, ExPlotWidgetProperties
from accwidgets._designer_base import WidgetsExtension, get_designer_cursor
from accwidgets.qt import (AbstractTableModel, TableViewColumnResizer, AbstractTableDialog,
                           BooleanPropertyColumnDelegate)


@dataclass
class LayerTableRow:
    """View model class for the Plot layer table."""
    axis_id: str
    axis_label: Optional[str] = None
    auto_range: bool = True
    min_range: Optional[float] = None
    max_range: Optional[float] = None


class PlotLayerTableModel(AbstractTableModel[LayerTableRow]):

    DEFAULT_VIEW_RANGE: Tuple[float, float] = (0.0, 1.0)

    def __init__(self, data: List[LayerTableRow], parent: Optional[QObject] = None):
        """
        Model for layer editor dialog.

        Args:
            data: Initial data.
            parent: Owning object.
        """
        AbstractTableModel.__init__(self, data=data, parent=parent)

    def create_row(self) -> LayerTableRow:
        next_idx = self.rowCount() - 2  # Assuming 2 always occupied by x, y

        def id_template(idx: int):
            return f"y_{idx}"

        def id_exists(idx: int):
            return any(row.axis_id == id_template(idx) for row in self._data)

        while id_exists(next_idx):
            next_idx += 1
        return LayerTableRow(axis_id=id_template(next_idx))

    def columnCount(self, *_, **__):
        return 5

    def column_name(self, section: int) -> str:
        if section == 0:
            return "Axis Identifier"
        elif section == 1:
            return "Axis Label"
        elif section == 2:
            return "Auto Range"
        elif section == 3:
            return "View Range Min"
        elif section == 4:
            return "View Range Max"
        raise ValueError(f"Unexpected column {section}")

    def get_cell_data(self, index: QModelIndex, row: LayerTableRow) -> Any:
        section = index.column()
        if section == 0:
            return row.axis_id
        elif section == 1:
            return row.axis_label
        elif section == 2:
            return row.auto_range
        elif section == 3:
            return row.min_range if row.min_range is not None else "Auto"
        elif section == 4:
            return row.max_range if row.max_range is not None else "Auto"
        raise ValueError(f"Unexpected column {section}")

    def set_cell_data(self, index: QModelIndex, row: LayerTableRow, value: Any) -> bool:
        section = index.column()
        if section == 0:
            row.axis_id = str(value)
        elif section == 1:
            row.axis_label = str(value)
        elif section == 2:
            row.auto_range = bool(value)
            if row.auto_range:
                row.max_range = row.min_range = None
            else:
                if row.min_range is None:
                    row.min_range = self.DEFAULT_VIEW_RANGE[0]
                if row.max_range is None:
                    row.max_range = self.DEFAULT_VIEW_RANGE[1]
        elif section == 3:
            row.min_range = float(value)
        elif section == 4:
            row.max_range = float(value)
        else:
            return False
        return True

    def flags(self, index: QModelIndex):
        column = index.column()
        row = index.row()
        if column == 0 and row <= 1:
            # Forbid editing default axis IDs
            return Qt.ItemIsSelectable
        if column in [3, 4] and self._data[row].auto_range:
            # Forbid editing range, when set to auto
            return Qt.ItemIsSelectable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def notify_change(self, start: QModelIndex, end: QModelIndex, action_type: AbstractTableModel.ChangeType):
        if action_type == self.ChangeType.UPDATE_ITEM and start.column() == 2:
            # Update range cells as well
            super().notify_change(start=start,
                                  end=end.siblingAtColumn(end.model().columnCount() - 1),
                                  action_type=action_type)
        else:
            super().notify_change(start=start, end=end, action_type=action_type)

    def validate(self):
        """Note! This method has a side effect of filling in ranges, when they are set default and not modified"""
        used_ids = set()
        for idx, item in enumerate(self._data):
            if not item.axis_id:
                raise ValueError(f'Row #{idx+1} is lacking "Axis Identifier".')
            if item.axis_id in used_ids:
                raise ValueError(f'Axis Identifier "{item.axis_id}" is being used more than once.')
            if not item.auto_range:
                if item.min_range is None:
                    item.min_range = self.DEFAULT_VIEW_RANGE[0]
                if item.max_range is None:
                    item.max_range = self.DEFAULT_VIEW_RANGE[1]
                if item.min_range > item.max_range:
                    raise ValueError(f"Row #{idx+1} has inverted view range (max < min).")
                if item.min_range == item.max_range:
                    raise ValueError(f"Row #{idx+1} has zero view range (max = min).")
            used_ids.add(item.axis_id)


class RangeColumnDelegate(QStyledItemDelegate):
    """Delegate to allow editing ranges with decimal values that can go down to 1e-6."""

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor = QDoubleSpinBox(parent)
        editor.setDecimals(7)
        editor.setMinimum(-float_info.max)
        editor.setMaximum(float_info.max)
        return editor

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex):
        if not isinstance(editor, QDoubleSpinBox):
            return
        editor.setValue(index.data())

    def setModelData(self, editor: QDoubleSpinBox, model: AbstractTableModel, index: QModelIndex):
        if not isinstance(editor, QDoubleSpinBox):
            return
        model.setData(index, editor.value())

    def displayText(self, value: QVariant, locale: QLocale) -> str:
        return value if isinstance(value, str) else locale.toString(value)


class PlotLayerEditingDialog(AbstractTableDialog[LayerTableRow, PlotLayerTableModel]):

    DEFAULT_AXES: List[str] = ["x", "y"]
    AXIS_AUTO_RANGE_KEY = "auto"

    def __init__(self, plot: ExPlotWidget, parent: QObject = None):
        """
        Dialog displaying a table to the user for editing the plots layers.

        Args:
            plot: Plot that will be the base of the tables data model
            parent: Parent item for the dialog
        """
        super().__init__(table_model=PlotLayerTableModel(self._unpack_json(plot)), parent=parent)
        # self.layer_table_model = LayerEditorTableModel(self.plot)
        self.plot = plot

        plot_name = " ".join([s.capitalize() for s in plot.plotItem.plot_config.plotting_style.name.split("_")])
        self.setWindowTitle(f"Edit Axes of {plot_name}")

        self.table.setItemDelegateForColumn(2, BooleanPropertyColumnDelegate(self.table))
        self.table.setItemDelegateForColumn(3, RangeColumnDelegate(self.table))
        self.table.setItemDelegateForColumn(4, RangeColumnDelegate(self.table))
        self.table.set_persistent_editor_for_column(2)

        TableViewColumnResizer.install_onto(self.table)
        self.resize(600, 300)

    def on_save(self):
        cursor = get_designer_cursor(self.plot)
        if cursor:
            cursor.setProperty("layerIDs", self._pack_ids())
            cursor.setProperty("axisRanges", self._pack_ranges())
            cursor.setProperty("axisLabels", self._pack_labels())
        else:
            warnings.warn("Unable to save edited data back to widget")

    def _pack_ids(self) -> List[str]:
        ids = {row.axis_id for row in self._table_model._data}
        ids.difference_update(set(self.DEFAULT_AXES))
        return list(ids)

    def _pack_ranges(self) -> str:
        res: Dict[str, Union[str, Tuple[Optional[float], Optional[float]]]] = {}
        for row in self._table_model._data:
            if row.auto_range:
                res[row.axis_id] = self.AXIS_AUTO_RANGE_KEY
            else:
                res[row.axis_id] = row.min_range, row.max_range
        return json.dumps(res)

    def _pack_labels(self) -> str:
        res = {}
        for row in self._table_model._data:
            if row.axis_id == self.DEFAULT_AXES[0]:
                res.update({
                    "bottom": row.axis_label,
                    "top": row.axis_label,
                })
            elif row.axis_id == self.DEFAULT_AXES[1]:
                res.update({
                    "left": row.axis_label,
                    "right": row.axis_label,
                })
            else:
                res[row.axis_id] = row.axis_label
        return json.dumps(res)

    def _unpack_json(self, plot: ExPlotWidget) -> List[LayerTableRow]:
        props = cast(ExPlotWidgetProperties, plot)
        axis_labels: Dict[str, Any] = json.loads(props.axisLabels)
        axis_ranges: Dict[str, Any] = json.loads(props.axisRanges)

        res = []
        for axis_id in self.DEFAULT_AXES + props.layerIDs:
            label: str
            if axis_id == self.DEFAULT_AXES[0]:
                label = axis_labels.get("bottom", axis_labels.get("top", ""))
            elif axis_id == self.DEFAULT_AXES[1]:
                label = axis_labels.get("left", axis_labels.get("right", ""))
            else:
                label = axis_labels.get(axis_id, "")
            range: Union[Tuple[float, float], str] = axis_ranges.get(axis_id, (0.0, 1.0))
            is_auto_range = range == "auto"
            range_min: Optional[float]
            range_max: Optional[float]
            if is_auto_range:
                range_min = None
                range_max = None
            else:
                range_min, range_max = cast(Tuple[float, float], range)
            res.append(LayerTableRow(axis_id=axis_id,
                                     axis_label=label,
                                     auto_range=is_auto_range,
                                     max_range=range_max,
                                     min_range=range_min))
        return res


class PlotLayerExtension(WidgetsExtension):

    def __init__(self, widget: ExPlotWidget):
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
        dialog = PlotLayerEditingDialog(self.widget, parent=self.widget)
        dialog.exec_()

    def actions(self):
        """Actions associated with this extension."""
        return [self.edit_layer_action]
