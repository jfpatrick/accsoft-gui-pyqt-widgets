"""
Module contains different curves that can be added to a PlotItem based on PyQtGraph's PlotDataItem.
"""

from copy import copy
from enum import IntEnum, Flag, auto
from typing import Tuple, Dict, cast, Type, Union, Optional, List, TYPE_CHECKING

import numpy as np
import pyqtgraph as pg
from accwidgets._deprecations import deprecated_param_alias
from accwidgets.graph import (UpdateSource, LiveCurveDataModel, StaticCurveDataModel, EditableCurveDataModel,
                              DEFAULT_BUFFER_SIZE, DEFAULT_COLOR, DataModelBasedItem, AbstractBaseDataModel,
                              CurveData, PlotWidgetStyle, CyclicPlotTimeSpan)
from accwidgets.qt import AbstractQGraphicsItemMeta
from qtpy.QtCore import QRectF, Signal, Qt, QPointF
from qtpy.QtGui import QColor, QPen, QBrush
from qtpy.QtWidgets import QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent

if TYPE_CHECKING:
    from accwidgets.graph import ExPlotItem


# params accepted by the plotdataitem and their fitting params in the curve-item
# (see PlotDataItem.updateItems updateItems for reference)
_PLOTDATAITEM_CURVE_PARAM_MAPPING = [
    ("pen", "pen"),
    ("shadowPen", "shadowPen"),
    ("fillLevel", "fillLevel"),
    ("fillOutline", "fillOutline"),
    ("fillBrush", "brush"),
    ("antialias", "antialias"),
    ("connect", "connect"),
    ("stepMode", "stepMode"),
    ("skipFiniteCheck", "skipFiniteCheck"),
]

# params accepted by the plotdataitem and their fitting params in the scatter-plot-item
# (see PlotDataItem.updateItems updateItems for reference)
_PLOTDATAITEM_SCATTER_PARAM_MAPPING = [
    ("symbolPen", "pen"),
    ("symbolBrush", "brush"),
    ("symbol", "symbol"),
    ("symbolSize", "size"),
    ("data", "data"),
    ("pxMode", "pxMode"),
    ("antialias", "antialias"),
]


class AbstractBasePlotCurve(DataModelBasedItem, pg.PlotDataItem, metaclass=AbstractQGraphicsItemMeta):

    def __init__(self,
                 plot_item: "ExPlotItem",
                 data_model: AbstractBaseDataModel,
                 pen=DEFAULT_COLOR,
                 **plotdataitem_kwargs):
        """
        Base class for all curve items.

        Args:
            plot_item: Plot item the curve should fit to.
            data_model: Data model the curve is based on.
            pen: Pen the curve should be drawn with (it is a part of the :class:`~pyqtgraph.PlotDataItem`
                 base class arguments).
            **plotdataitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotDataItem` constructor.
        """
        DataModelBasedItem.__init__(self,
                                    data_model=data_model,
                                    parent_plot_item=plot_item)
        pg.PlotDataItem.__init__(self, pen=pen, **plotdataitem_kwargs)
        self.opts["connect"] = "finite"
        # Save drawn data for testing purposes
        self._data_item_data: CurveData
        if pen is not None:
            self.setPen(pen)

    @classmethod
    def from_plot_item(cls,
                       plot_item: "ExPlotItem",
                       data_source: UpdateSource,
                       buffer_size: int = DEFAULT_BUFFER_SIZE,
                       **plotdataitem_kwargs) -> "AbstractBasePlotCurve":
        """
        Factory method for creating curve object matching the given plot item.

        This function allows easier creation of proper items by using the right type.
        It only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: Plot item the item should fit to.
            data_source: Source the item receives data from.
            buffer_size: Amount of values that data model's buffer is able to accommodate.
            **plotdataitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotDataItem` constructor.

        Returns:
            A new curve which receives data from the given data source.

        Raises:
            ValueError: The item does not fit the passed plot item's plotting style.
        """
        subclass = cls.get_subclass_fitting_plotting_style(plot_item=plot_item)
        data_model = subclass.data_model_type(data_source=data_source, buffer_size=buffer_size)
        return subclass(plot_item=plot_item, data_model=data_model, **plotdataitem_kwargs)


class LivePlotCurve(AbstractBasePlotCurve):

    data_model_type = LiveCurveDataModel

    @deprecated_param_alias(data_source="data_model")
    def __init__(self,
                 plot_item: "ExPlotItem",
                 data_model: Union[UpdateSource, LiveCurveDataModel],
                 buffer_size: int = DEFAULT_BUFFER_SIZE,
                 pen=DEFAULT_COLOR,
                 **plotdataitem_kwargs):
        """
        Abstract base class for all curves receiving live data, such as scrolling or cyclic plot curves.

        Args:
            plot_item: Plot item the curve is created for.
            data_model: Either an :class:`UpdateSource` or an already initialized data model.
            buffer_size: Amount of values that data model's buffer is able to accommodate. It used only
                         when ``data_model`` argument is a :class:`UpdateSource` and thus a new data model
                         object is initialized.
            pen: Pen the curve should be drawn with (it is a part of the :class:`~pyqtgraph.PlotDataItem`
                 base class arguments).
            **plotdataitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotDataItem` constructor.

        Raises:
            TypeError: ``data_model`` is neither :class:`UpdateSource`, nor a data model object.
        """
        if isinstance(data_model, UpdateSource):
            data_model = LiveCurveDataModel(data_source=data_model,
                                            buffer_size=buffer_size)
        if data_model is not None:
            super().__init__(plot_item=plot_item,
                             data_model=data_model,
                             pen=pen,
                             **plotdataitem_kwargs)
        else:
            raise TypeError(f"Need either data source or data model to create a {type(self).__name__} instance")

    @classmethod
    def clone(cls: Type["LivePlotCurve"],
              object_to_create_from: "LivePlotCurve",
              **plotdataitem_kwargs) -> "LivePlotCurve":
        """
        Clone graph item from an existing one. The data model is shared, but the new graph item
        is relying on the style of the old graph's parent plot item. If this style has changed
        since the creation of the old graph item, the new graph item will also have the new style.

        Args:
            object_to_create_from: Source object.
            **plotdataitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotDataItem` constructor.

        Returns:
            New live data curve with the data model from the old one.
        """
        item_class = LivePlotCurve.get_subclass_fitting_plotting_style(
            plot_item=object_to_create_from._parent_plot_item)
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(plotdataitem_kwargs)
        return cast(Type[LivePlotCurve], item_class)(
            plot_item=object_to_create_from._parent_plot_item,
            data_model=object_to_create_from._data_model,
            **kwargs,
        )

    @property
    def last_timestamp(self) -> float:
        """Last timestamp received by the curve."""
        return self._parent_plot_item.last_timestamp

    def _set_data(self, x: np.ndarray, y: np.ndarray):
        """ Set data of the inner curve and scatter plot

        PyQtGraph prints RuntimeWarning when the data that is passed to the
        ScatterPlotItem contains NaN values -> for this purpose we strip
        all indices containing NaNs, since it won't make any visual difference,
        because nans won't appear as symbols in the scatter plot.
        The CurvePlotItem will receive the data as usual.

        Args:
            x: x values that are passed to the items
            y: y values that are passed to the items
        """
        # For arguments like symbolPen which have to be transformed to pen and send to the ScatterPlot
        if (self.opts.get("pen") is not None
                or (self.opts.get("fillBrush") is not None
                    and self.opts.get("fillLevel") is not None)):
            curve_arguments: Dict = {}
            for orig_key, curve_key in _PLOTDATAITEM_CURVE_PARAM_MAPPING:
                curve_arguments[curve_key] = self.opts[orig_key]
            self.curve.setData(x=x, y=y, **curve_arguments)
            self.curve.show()
        else:
            self.curve.hide()
        if self.opts.get("symbol") is not None:
            data_x_wo_nans, data_y_wo_nans = LivePlotCurve._without_nan_values(x_values=x, y_values=y)
            scatter_arguments: Dict = {}
            for orig_key, scatter_key in _PLOTDATAITEM_SCATTER_PARAM_MAPPING:
                try:
                    scatter_arguments[scatter_key] = self.opts[orig_key]
                except KeyError:
                    pass
            self.scatter.setData(x=data_x_wo_nans, y=data_y_wo_nans, **scatter_arguments)
            self.scatter.show()
        else:
            self.scatter.hide()

    @staticmethod
    def _without_nan_values(x_values: np.ndarray, y_values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """ Get (if necessary) copies of the array without NaNs

        Strip arrays of x and y values from nan values. If one of the arrays
        has the value nan at the index n, in both arrays the value at index n
        will be removed. This will make sure both arrays will have the same
        length at the end again.

        Args:
            x_values: x-values that should be stripped from NaNs
            y_values: y-values that should be stripped from NaNs

        Returns:
            Copies of the arrays without any nans. If no NaN's are contained,
            the original arrays are returned.
        """
        if x_values.size != y_values.size:
            raise ValueError("The passed arrays have to be the same length.")
        x_nans = np.isnan(x_values)
        y_nans = np.isnan(y_values)
        combined_nans = x_nans | y_nans
        if True in combined_nans:
            return x_values[~combined_nans], y_values[~combined_nans]
        else:
            return x_values, y_values


class CyclicPlotCurve(LivePlotCurve):

    supported_plotting_style = PlotWidgetStyle.CYCLIC_PLOT

    @deprecated_param_alias(data_source="data_model")
    def __init__(self,
                 plot_item: "ExPlotItem",
                 data_model: Union[UpdateSource, LiveCurveDataModel],
                 buffer_size: int = DEFAULT_BUFFER_SIZE,
                 pen=DEFAULT_COLOR,
                 **plotdataitem_kwargs):
        """
        Curve item for the :class:`CyclicPlotWidget`.

        Displays data as a cyclic plot widget similar to a heart rate monitor. The graph itself
        stays fixed in position and has a fixed length. As soon as the drawing reaches the end,
        the graph gets redrawn from the left hand side. The old curve gets incrementally
        overwritten by the new values. The x-values of all lines in the graph will
        be adjusted so the visible curve does not move.

        Args:
            plot_item: Plot item the curve should fit to.
            data_model: Either an :class:`UpdateSource` or an already initialized data model.
            buffer_size: Amount of values that data model's buffer is able to accommodate. It used only
                         when ``data_model`` argument is a :class:`UpdateSource` and thus a new data model
                         object is initialized.
            pen: Pen the curve should be drawn with (it is a part of the :class:`~pyqtgraph.PlotDataItem`
                 base class arguments).
            **plotdataitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotDataItem` constructor.
        """
        super().__init__(plot_item=plot_item,
                         data_model=data_model,
                         buffer_size=buffer_size,
                         pen=pen,
                         **plotdataitem_kwargs)
        # Curves after clipping (data actually drawn)
        self._clipped_curve_old: CurveData = CurveData(np.array([]),
                                                       np.array([]),
                                                       check_validity=False)
        self._clipped_curve_new: CurveData = CurveData(np.array([]),
                                                       np.array([]),
                                                       check_validity=False)

    def update_item(self):
        self._update_new_curve_data_item()
        if cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).cycle > 0:
            self._update_old_curve_data_item()
        self._redraw_curve()

    def _redraw_curve(self):
        """ Redraw the curve with the current data

        For drawing the new and old curve a single PlotCurveItem is used.
        The cut between both curves is achieved with a np.nan value as a
        separator in combination with finite connection passed to the
        PlotCurveItem.
        """
        data_x: np.ndarray = np.array([])
        data_y: np.ndarray = np.array([])
        if (
            self._clipped_curve_new.x.size != 0
            and self._clipped_curve_new.y.size != 0
        ):
            data_x = np.concatenate((data_x, self._clipped_curve_new.x))
            data_y = np.concatenate((data_y, self._clipped_curve_new.y))
        if (
            self._clipped_curve_old.x.size != 0
            and self._clipped_curve_old.y.size != 0
        ):
            if data_x.size != 0 and data_y.size != 0:
                data_x = np.concatenate((data_x, np.array([np.nan])))
                data_y = np.concatenate((data_y, np.array([np.nan])))
            data_x = np.concatenate((data_x, self._clipped_curve_old.x))
            data_y = np.concatenate((data_y, self._clipped_curve_old.y))
        if data_x.size != 0 and data_y.size != 0:
            self.clear()
            self._set_data(x=data_x, y=data_y)

    def _update_new_curve_data_item(self):
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of e.g. inaccurate timestamp)
        """
        start = self._parent_plot_item.time_span.start
        end = self._parent_plot_item.last_timestamp
        x_values, y_values = self._data_model.subset_for_xrange(start=start, end=end, interpolated=True)
        self._clipped_curve_new = CurveData(
            x=x_values - cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).curr_offset,
            y=y_values,
            check_validity=False,
        )

    def _update_old_curve_data_item(self):
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of e.g. inaccurate timestamp)
        """
        start = self._parent_plot_item.last_timestamp - self._parent_plot_item.time_span.time_span.size
        end = cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).prev_end
        x_values, y_values = self._data_model.subset_for_xrange(start=start, end=end, interpolated=True)
        self._clipped_curve_old = CurveData(
            x=x_values - cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).prev_offset,
            y=y_values,
            check_validity=False,
        )


class ScrollingPlotCurve(LivePlotCurve):
    """
    Curve item for the :class:`ScrollingPlotWidget`.

    This curves acts as a FIFO queue, rendering new data points on the right hand side and
    removing them from the left, as soon as they reach the capacity of the data model's buffer.
    """

    supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    def update_item(self):
        if self.opts.get("pen", None) is not None:
            # Subset for curve is clipped
            curve_x, curve_y = self._data_model.subset_for_xrange(
                start=self._parent_plot_item.time_span.start,
                end=self._parent_plot_item.time_span.end,
                interpolated=True,
            )
        else:
            # Clipping is not used for scatter plot
            curve_x, curve_y = self._data_model.subset_for_xrange(start=self._parent_plot_item.time_span.start,
                                                                  end=self._parent_plot_item.time_span.end)
        self._set_data(x=curve_x, y=curve_y)
        self._data_item_data = CurveData(x=curve_x,
                                         y=curve_y,
                                         check_validity=False)


class StaticPlotCurve(AbstractBasePlotCurve):
    """
    Curve item for the :class:`StaticPlotWidget`.

    Static curves always have their entire buffer overwritten instead of appending it from any side.
    It is useful for rendering waveform plots.
    """

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticCurveDataModel

    def update_item(self):
        """Get the full data of the data buffer and display it."""
        self.setData(*self._data_model.full_data_buffer)


class EditablePlotCurve(AbstractBasePlotCurve):

    supported_plotting_style = PlotWidgetStyle.EDITABLE
    data_model_type = EditableCurveDataModel

    sig_selection_changed = Signal()
    """
    Signal informing about any changes to the current selection. If the emitted
    data is empty, the current selection is considered unselected. The signal will also
    be emitted, if the current selection has been moved around by dragging.
    """

    def __init__(self,
                 plot_item: "ExPlotItem",
                 data_model: AbstractBaseDataModel,
                 pen=DEFAULT_COLOR,
                 **plotdataitem_kwargs):
        """
        Curve item for the :class:`EditablePlotWidget`.

        This curve is not updating live, but rather allows to see a static data set and edit it by hand.

        Args:
            plot_item: Plot item the curve should fit to.
            data_model: Data model the curve is based on.
            pen: Pen the curve should be drawn with (it is a part of the :class:`~pyqtgraph.PlotDataItem`
                 base class arguments).
            **plotdataitem_kwargs: Keyword arguments for the :class:`~pyqtgraph.PlotDataItem` constructor.
        """
        AbstractBasePlotCurve.__init__(self,
                                       plot_item=plot_item,
                                       data_model=data_model,
                                       pen=pen,
                                       **plotdataitem_kwargs)
        # We will use a separate scatter plot item for interaction with the
        # data instead of using the scatter plot item child of the PlotDataItem
        self._selection = DataSelectionMarker(direction=DragDirection.Y)
        self._selection.setParentItem(self)
        self._selected_indices: Optional[np.ndarray] = None

    def select(self, selection: QRectF):
        """
        Select data from the curve using the passed rectangle. The rectangle
        coordinates are given in scene coordinates.

        Args:
            selection: Rectangle for selecting new points.
        """
        self._update_selected_indices(selection)
        if not self._selection_indices_empty:
            x, y = self.getData()
            x_selection = x[self._selected_indices]
            y_selection = y[self._selected_indices]
            self._stylize_selection_marker()
            self._reconnect_to_selection()
            self._selection.setData(x_selection, y_selection)
            self.sig_selection_changed.emit()
        else:
            self.unselect()

    def unselect(self):
        """Remove selections done previously via :meth:`select`."""
        self._update_selected_indices(None)
        # Inform about point being unselected
        self._disconnect_from_selection()
        self._selection.setData([], [])
        self.sig_selection_changed.emit()

    def update_item(self):
        """Get the full data of the data buffer and display it."""
        self.setData(*self._data_model.full_data_buffer)
        self.sig_selection_changed.emit()

    @property
    def selection(self) -> "DataSelectionMarker":
        """Marker item for the currently selected data."""
        return self._selection

    @property
    def selection_data(self) -> Optional[CurveData]:
        """Currently selected data."""
        if self._selection:
            return self._selection.curve_data
        return None

    def replace_selection(self, replacement: CurveData):
        """
        Replace the current selection with the ``replacement``.
        To select data from the plot, use :meth:`select`. After the replacement is
        completed, the selection will be unselected.

        Args:
            replacement: Data which should replace the current selection.
        """
        indices = np.nonzero(self._selected_indices)
        self._editable_model.replace_selection(indices, replacement)
        self.unselect()

    # ~~~~~~~~~~~~~~~ Wrapped from data model ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def send_current_state(self) -> bool:
        """
        Commit performed changes into the :attr:`~EditableCurveDataModel.data_source`.

        Returns:
            Whether change was successfully committed.
        """
        return self._editable_model.send_current_state()

    @property
    def sendable_state_exists(self) -> bool:
        """
        Check whether there are any changes that can be committed into the :attr:`~EditableCurveDataModel.data_source`.
        """
        return self._editable_model.sendable_state_exists

    @property
    def undoable(self) -> bool:
        """Check whether there is an older state that can be rolled back to."""
        return self._editable_model.undoable

    @property
    def redoable(self) -> bool:
        """Check whether there is a newer state that can be transitioned to."""
        return self._editable_model.redoable

    def undo(self):
        """Roll back to the next older state."""
        if self._editable_model.undo():
            self.unselect()

    def redo(self):
        """Transition to the next newer state."""
        if self._editable_model.redo():
            self.unselect()

    # ~~~~~~~~~~~~~~~~~~~~ Private ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _update_selected_indices(self, selection: Optional[QRectF]):
        """
        Update the selection of the data selection marker with a given
        selection rectangle

        Args:
            selection: A selected region as a rectangle or None for unselecting
                       all prior selected points
        """
        if selection:
            x0 = selection.left()
            x1 = selection.right()
            y0 = selection.top()
            y1 = selection.bottom()
            x_data, y_data = self.getData()
            sel = np.logical_and(np.logical_and(x0 <= x_data, x_data <= x1),
                                 np.logical_and(y0 <= y_data, y_data <= y1))
        else:
            x_data, y_data = self.getData()
            sel = np.zeros_like(x_data, dtype=bool)
        self._selected_indices = sel

    def _stylize_selection_marker(self):
        """
        Style the selected points with different colors so they are easily
        visible.
        """
        sym = self.opts.get("symbol")
        plot_bg_brush = self.scene().parent().backgroundBrush()
        if sym:
            self._selection.setBrush(None)
            self._selection.setSymbol(sym)
        else:
            self._selection.setBrush(plot_bg_brush)

        if self.opts["pen"] is not None:
            orig_pen = pg.mkPen(self.opts["pen"])
        elif self.opts["symbolBrush"] is not None:
            brush = self.opts["symbolBrush"]
            if isinstance(brush, QBrush):
                brush = brush.color()
            orig_pen = pg.mkPen(brush)
        elif self.opts["symbolPen"] is not None:
            orig_pen = pg.mkPen(self.opts["symbolPen"])
        else:
            orig_pen = pg.mkPen("w")

        # We need a minimum size so we can comfortably drag it with the mouse
        sym_size = max(self.opts["symbolSize"] + 2, 5)
        self._selection.setSize(sym_size)
        marker_pen = pg.mkPen(DataSelectionMarker.complementary(orig_pen.color(),
                                                                plot_bg_brush.color()))
        marker_pen.setWidth(3)
        self._selection.setPen(marker_pen)

    def _selection_moved(self, data: np.ndarray):
        """React to a change from the DataSelectionMarker, which is
        currently in progress. To fully accept the editing (with data model,
        history etc.), _selection_edited has to be called.

        Args:
            data: current editing state of the data selection marker
        """
        x, y = self.getData()
        x = np.copy(x)
        y = np.copy(y)
        for j, i in enumerate(np.flatnonzero(self._selected_indices)):
            x[i] = data[0][j]
            y[i] = data[1][j]
        self.setData(x, y)

    def _selection_edited(self, data: np.ndarray):
        """Apply the editing of the DataSelectionMarker to the this curve

        Compared to the _selection_moved function, this function will forward
        the passed state to the data model, which will add as a state to the
        curve's state history.

        We do not want to set the view data directly but go the route through
        the data model, the view will be updated automatically through the
        connection between the view and the model

        Args:
            data: data to apply to this curve from the selection marker
        """
        self._editable_model.handle_editing(CurveData(*self.getData(),
                                                      check_validity=False))

    def _reconnect_to_selection(self):
        """Disconnect and connect to selection marker."""
        self._disconnect_from_selection()
        self._connect_to_selection()

    def _connect_to_selection(self):
        """Connect to selection marker"""
        self._selection.sig_selection_edited.connect(self._selection_edited)
        self._selection.sig_selection_moved.connect(self._selection_moved)

    def _disconnect_from_selection(self):
        """Try to disconnect from selection marker"""
        try:
            self._selection.sig_selection_edited.disconnect(self._selection_edited)
            self._selection.sig_selection_moved.disconnect(self._selection_moved)
        except TypeError:
            # If no selection has been made in selection mode no signal was
            # connected
            pass

    @property
    def _selection_indices_empty(self) -> bool:
        """
        Checks if the current selection is empty according to the saved
        indices. This potentially requires updating them before checking.
        """
        return (self._selected_indices is None
                or not any(self._selected_indices))

    @property
    def _editable_model(self) -> EditableCurveDataModel:
        """Accessing the datamodel through this saves you from casting."""
        return cast(EditableCurveDataModel, self.model())


class DragDirection(Flag):
    """
    Flags for defining the direction in which points in a
    :class:`DataSelectionMarker` should be draggable.
    """
    X = auto()
    "Horizontal direction."

    Y = auto()
    "Vertical direction."


class PointLabelOptions(IntEnum):
    """
    Enumeration to specify when labels should be displayed for points on the graph.
    """
    NEVER = auto()
    """Never display labels."""

    HOVER = auto()
    """Display labels when hovering over the related point."""

    ALWAYS = auto()
    """Always display labels."""


class DataSelectionMarker(pg.ScatterPlotItem):

    sig_selection_edited = Signal(np.ndarray)
    """
    As soon as a move was done successfully, this signal will emit the new
    position of the data displayed by this marker.
    """

    sig_selection_moved = Signal(np.ndarray)
    """
    With every move this signal will be emitted. It is mainly for visualizing
    a work in progress editing in the original curve.
    """

    def __init__(self,
                 direction: DragDirection = DragDirection.Y,
                 label_points: Union[PointLabelOptions, bool] = PointLabelOptions.HOVER,
                 *args,
                 **kwargs):
        """
        Data selection markers are points (derived from scatter plots) that can be moved around.

        Args:
            direction: In which direction should the points be draggable.
            label_points: Labelling options for the plot.
            args: Positional arguments for the :class:`~pyqtgraph.ScatterPlotItem` constructor.
            kwargs: Keyword arguments for the :class:`~pyqtgraph.ScatterPlotItem` constructor.
        """
        self._point_labels: List[pg.TestItem] = []
        if isinstance(label_points, bool):
            label_points = PointLabelOptions.ALWAYS if label_points else PointLabelOptions.NEVER
        self._points_labeled: PointLabelOptions = label_points
        super().__init__(*args, **kwargs)
        self._drag_direction = direction
        # State of the current drag event
        self._drag_start: Optional[QPointF] = None
        self._drag_point: Optional[pg.SpotItem] = None
        self._original_data: Optional[np.ndarray] = None
        self._current_hover: Optional[pg.Point] = None
        self._drag_orig_hover: Optional[pg.Point] = None
        self.setAcceptHoverEvents(True)

    def hoverMoveEvent(self, ev: QGraphicsSceneHoverEvent):
        """
        Triggers label rendering for points if the mode is :attr:`PointLabelOptions.HOVER`.

        Args:
            ev: Hover event over the marker.
        """
        super().hoverMoveEvent(ev)
        if self._points_labeled != PointLabelOptions.HOVER:
            return
        points = self.pointsAt(ev.pos())
        if points:
            self._current_hover = points[0].pos()
            self._add_labels()
        else:
            self._current_hover = None
            self._remove_labels()
        ev.accept()

    def hoverLeaveEvent(self, ev: QGraphicsSceneHoverEvent):
        """
        Triggers label rendering for points if the mode is :attr:`PointLabelOptions.HOVER`.

        Args:
            ev: Hover event over the marker.
        """
        super().hoverMoveEvent(ev)
        if self._points_labeled == PointLabelOptions.HOVER:
            self._current_hover = None
            self._remove_labels()
            ev.accept()

    def mouseDragEvent(self, ev: QGraphicsSceneMouseEvent):
        """
        Custom mouse drag event for moving the selection around.
        If there are no points under the drag events starting position, it
        will be ignored.

        Args:
            ev: Mouse drag event to move the selection.
        """
        if ev.button() != Qt.LeftButton:
            ev.ignore()
            return
        if ev.isStart():
            self._original_data = np.array(self.getData())
            if self._current_hover is not None:
                self._drag_orig_hover = self._current_hover.copy()
            try:
                self._drag_point = self.pointsAt(ev.buttonDownPos())[0].pos()
                self._drag_start = -1 * ev.buttonDownPos()
                ev.accept()
            except IndexError:
                pass
            return
        elif ev.isFinish():
            self._drag_start = None
            self._drag_orig_hover = None
            self.sig_selection_edited.emit(np.array(self.getData()))
        else:
            data = np.copy(self._original_data)
            apply_x = self._drag_start is not None and self._drag_direction & DragDirection.X
            apply_y = self._drag_start is not None and self._drag_direction & DragDirection.Y
            x_offset = ev.pos().x() + cast(QPointF, self._drag_start).x() if apply_x else 0.0
            y_offset = ev.pos().y() + cast(QPointF, self._drag_start).y() if apply_y else 0.0
            if x_offset or y_offset:
                if apply_x:
                    data[0] += x_offset
                    if self._current_hover is not None and self._drag_orig_hover is not None:
                        self._current_hover.setX(self._drag_orig_hover.x() + x_offset)
                if apply_y:
                    data[1] += y_offset
                    if self._current_hover is not None and self._drag_orig_hover is not None:
                        self._current_hover.setY(self._drag_orig_hover.y() + y_offset)
                self.setData(data[0, :], data[1, :])
                self.setData(data[0, :], data[1, :])
                self.sig_selection_moved.emit(np.array(self.getData()))

    def setData(self,
                *args,
                pos: Union[Tuple, List, np.ndarray, None] = None,
                pxMode: Optional[bool] = None,
                symbol: Optional[str] = None,
                pen: Union[QPen, List[QPen], None] = None,
                brush: Union[QBrush, List[QBrush], None] = None,
                size: Union[float, List[float], None] = None,
                data: Optional[List[object]] = None,
                antialias: Optional[bool] = None,
                name: Optional[str] = None,
                **kwargs):
        """
        Extends :meth:`pyqtgraph.ScatterPlotItem.setData` with setting labels for each point.

        If there is only one positional argument, it will be interpreted as ``spots`` keyword argument.
        If there are two positional arguments, they will be interpreted as arrays of ``x`` and ``y`` values.

        Args:
            spots: Optional list of dicts. Each dict specifies parameters for a single spot:
                   {'pos': (x,y), 'size', 'pen', 'brush', 'symbol'}. This is just an alternate method
                   of passing in data for the corresponding arguments.
            x: 1D arrays of x values.
            y: 1D arrays of y values.
            pos: 2D structure of x,y pairs (such as Nx2 array or list of tuples)
            pxMode: If True, spots are always the same size regardless of scaling, and size is given in px.
                    Otherwise, size is in scene coordinates and the spots scale with the view.
                    Default is True
            symbol: can be one (or a list) of:
                    * 'o'  circle (default)
                    * 's'  square
                    * 't'  triangle
                    * 'd'  diamond
                    * '+'  plus
                    * any QPainterPath to specify custom symbol shapes. To properly obey the position and size,
                      custom symbols should be centered at (0,0) and width and height of 1.0. Note that it is also
                      possible to 'install' custom shapes by setting ScatterPlotItem.Symbols[key] = shape.
            pen: The pen (or list of pens) to use for drawing spot outlines.
            brush: The brush (or list of brushes) to use for filling spots.
            size: The size (or list of sizes) of spots. If *pxMode* is True, this value is in pixels. Otherwise,
                  it is in the item's local coordinate system.
            data: a list of python objects used to uniquely identify each spot.
            antialias: Whether to draw symbols with antialiasing. Note that if pxMode is True, symbols are
                       always rendered with antialiasing (since the rendered symbols can be cached, this
                       incurs very little performance cost)
            name: The name of this item. Names are used for automatically
                  generating LegendItem entries and by some exporters.
        """
        kwargs.update({
            "pos": pen,
            "pxMode": pxMode,
            "symbol": symbol,
            "pen": pen,
            "brush": brush,
            "size": size,
            "data": data,
            "antialias": antialias,
            "name": name,
        })
        # We want pyqtgraph's default behavior so we do not pass unset args
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        super().setData(*args, **kwargs)
        if self._points_labeled != PointLabelOptions.NEVER:
            self._add_labels()
        else:
            self._remove_labels()

    @property
    def curve_data(self) -> CurveData:
        """Data of the selection marker as curve data."""
        x, y = self.getData()
        return CurveData(x, y, check_validity=False)

    @property
    def points_labeled(self) -> PointLabelOptions:
        """Indicates how the selected points are labelled."""
        return self._points_labeled

    @points_labeled.setter
    def points_labeled(self, label_points: PointLabelOptions):
        self._points_labeled = label_points

    @property
    def drag_direction(self) -> DragDirection:
        """Indicates in which direction the points can be dragged."""
        return self._drag_direction

    @drag_direction.setter
    def drag_direction(self, direction: DragDirection):
        self._drag_direction = direction

    @staticmethod
    def complementary(color: QColor, plot_background: Optional[QColor] = None) -> QColor:
        """
        Get the complementary color to a given ``color``. For white, grey and black
        colors, red is returned as the complementary color. If the color does
        not provide enough contrast compared to the plot's background (when it is
        passed), we will lighten / darken it accordingly.

        Args:
            color: Color whose complementary color should be calculated.
            plot_background: Background color that is used to lighten / darken
                             the complementary color to offer enough contrast
                             to be visible.
        """
        rgb = [color.red(), color.green(), color.blue()]
        # Color is somewhat greyish -> we take red as the complementary
        if max(rgb) - min(rgb) < 10:
            return pg.mkColor("r")
        compl = QColor(
            255 - color.red(),
            255 - color.green(),
            255 - color.blue(),
            color.alpha(),
        )
        if plot_background:
            if DataSelectionMarker._contrast_ratio(plot_background, compl) < 4.0:
                if DataSelectionMarker._relative_luminance(plot_background) >= 0.5:
                    # We have a light background
                    lightness = compl.lightness() * 0.5
                else:
                    # We have a dark background
                    lightness = min(compl.lightness() * 2, 230)
                compl.setHsl(compl.hue(), compl.saturation(), int(round(lightness)))
        return compl

    def _add_labels(self):
        """
        For each point, add a label showing the position of the point in the
        direction it can be dragged in.

        Args:
            points: points which should be labeled. All points will be labeled
                    if no points are passed
        """
        self._remove_labels()
        for data in self.data:
            if (self._points_labeled == PointLabelOptions.HOVER
                    and (self._current_hover is None
                         or self._current_hover.x() != data["x"]
                         and self._current_hover.y() != data["y"])):
                continue
            text = self._point_label(x=data["x"],
                                     y=data["y"])
            label = pg.TextItem(text,
                                anchor=(0.5, self._get_label_y_anchor(data)))
            label.setParentItem(self)
            label.setPos(data["x"], data["y"])
            color = pg.getConfigOption("foreground")
            if not isinstance(color, QColor):
                try:
                    color = pg.mkColor(color)
                except Exception:  # noqa: B902
                    # Exception -> mkColor does not get more precise
                    color = None
            if color:
                label.setColor(color)
            self._point_labels.append(label)

    def _get_label_y_anchor(self, data: Dict):
        """Get a fitting anchor for the text label in y direction, so it is
        above / below the spot depending on its position"""
        plot = self.parentItem().scene().parent()
        vb_y_range: Optional[Tuple[float, float]] = None
        y_anker = -0.5
        for vb in plot.plotItem.view_boxes:
            if self.parentItem() in vb.addedItems:
                vb_y_range = vb.targetRange()[1]
        if vb_y_range is not None:
            y_min = vb_y_range[0]
            y_max = vb_y_range[1]
            if data["y"] < y_min + (y_max - y_min) / 2:
                y_anker += 2
        return y_anker

    def _remove_labels(self):
        """Remove all point labels"""
        for label in self._point_labels:
            label.setParentItem(None)
        self._point_labels.clear()

    def _point_label(self, x: float, y: float) -> str:
        """
        Show a label at the given position to inform the user about the offset
        of the current drag event.

        Returns:
            location of the passed point as string
        """
        label = []
        if self._drag_direction & DragDirection.X or self._points_labeled == PointLabelOptions.HOVER:
            label.append("x: {:.3}".format(x))
        if self._drag_direction & DragDirection.Y or self._points_labeled == PointLabelOptions.HOVER:
            label.append("y: {:.3}".format(y))
        return "\n".join(label)

    @staticmethod
    def _contrast_ratio(color_1: QColor, color_2: QColor) -> float:
        """ Calculate the contrast ratio between both given colors.
        The lighter / darker color do not have to be passed in a special order.
        Source: https://www.w3.org/TR/WCAG20/#contrast-ratiodef

        Args:
            color_1: First color of the pair
            color_2: Second color of the pair

        Returns:
            Values between 1 and 21, the higher the number, the higher the
            contrast.
        """
        luminance_1 = DataSelectionMarker._relative_luminance(color_1)
        luminance_2 = DataSelectionMarker._relative_luminance(color_2)
        if luminance_1 > luminance_2:
            return (luminance_1 + 0.05) / (luminance_2 + 0.05)
        return (luminance_2 + 0.05) / (luminance_1 + 0.05)

    @staticmethod
    def _relative_luminance(color: QColor) -> float:
        """Calculate the relative luminance for the given color.
        Source: https://www.w3.org/TR/WCAG20/#relativeluminancedef

        Args:
            color: color whose relative luminance should be calculated.

        Returns:
            0 for the darkest black and 1 for the lightest white
        """
        rgb: List[float] = []
        for component in [color.red(), color.green(), color.blue()]:
            c = component / 255
            if c <= 0.03928:
                rgb.append(c / 12.92)
            else:
                rgb.append(((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
