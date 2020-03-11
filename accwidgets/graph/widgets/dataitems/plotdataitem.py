"""
Module contains different curves that can be added to a PlotItem based on PyQtGraph's PlotDataItem.
"""

from typing import Tuple, Dict, cast, Type, Union, Optional, List
from copy import copy
from enum import Flag, auto

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import QRectF, Signal, Qt, QPointF
from qtpy.QtWidgets import QGraphicsSceneMouseEvent
from qtpy.QtGui import QColor, QPen, QBrush

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import (
    LiveCurveDataModel,
    StaticCurveDataModel,
    EditableCurveDataModel,
)
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.datamodel.datastructures import DEFAULT_COLOR
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractBaseDataModel,
    AbstractDataModelBasedItemMeta,
)
from accwidgets.graph.datamodel.datastructures import CurveData
from accwidgets.graph.widgets.plotconfiguration import PlotWidgetStyle
from accwidgets.graph.widgets.plottimespan import CyclicPlotTimeSpan
from accwidgets.graph.util import deprecated_param_alias
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem

# params accepted by the plotdataitem and their fitting params in the curve-item
_PLOTDATAITEM_CURVE_PARAM_MAPPING = [
    ("pen", "pen"),
    ("shadowPen", "shadowPen"),
    ("fillLevel", "fillLevel"),
    ("fillBrush", "brush"),
    ("antialias", "antialias"),
    ("connect", "connect"),
    ("stepMode", "stepMode"),
]

# params accepted by the plotdataitem and their fitting params in the scatter-plot-item
_PLOTDATAITEM_SCATTER_PARAM_MAPPING = [
    ("symbolPen", "pen"),
    ("symbolBrush", "brush"),
    ("symbol", "symbol"),
    ("symbolSize", "size"),
    ("data", "data"),
    ("pxMode", "pxMode"),
    ("antialias", "antialias"),
]


class AbstractBasePlotCurve(DataModelBasedItem, pg.PlotDataItem, metaclass=AbstractDataModelBasedItemMeta):

    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: AbstractBaseDataModel,
            pen=DEFAULT_COLOR,
            **plotdataitem_kwargs,
    ):
        """Base class for different live data curves.

        Args:
            plot_item: plot item the curve should fit to
            data_model: Data Model the curve is based on
            pen: pen the curve should be drawn with, is part of the PlotDataItem
                 base class parameters
            **plotdataitem_kwargs: keyword arguments fo the base class

        Raises:
            ValueError: The passes data source is not usable as a source for data
        """
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        pg.PlotDataItem.__init__(self, pen=pen, **plotdataitem_kwargs)
        self.opts["connect"] = "finite"
        # Save drawn data for testing purposes
        self._data_item_data: CurveData
        if pen is not None:
            self.setPen(pen)

    @classmethod
    def from_plot_item(
            cls,
            plot_item: "ExPlotItem",
            data_source: UpdateSource,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **plotdataitem_kwargs,
    ) -> "AbstractBasePlotCurve":
        """Factory method for creating curve object fitting to the given plot item.

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plot item by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's data model's buffer should hold at max
            **plotdataitem_kwargs: keyword arguments for the items base class

        Returns:
            A new Curve which receives data from the passed data source.

        Raises:
            ValueError: The item does not fit the passed plot item's plotting style.
        """
        subclass = cls.get_subclass_fitting_plotting_style(plot_item=plot_item)
        data_model = subclass.data_model_type(
            data_source=data_source,
            buffer_size=buffer_size,
        )
        return subclass(
            plot_item=plot_item,
            data_model=data_model,
            **plotdataitem_kwargs,
        )


class LivePlotCurve(AbstractBasePlotCurve):

    data_model_type = LiveCurveDataModel

    @deprecated_param_alias(data_source="data_model")
    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: Union[UpdateSource, LiveCurveDataModel],
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            pen=DEFAULT_COLOR,
            **plotdataitem_kwargs,
    ):
        """
        Live Plot Curve, abstract base class for all live data curves like
        the scrolling and cyclic curve. Either Data Source of data model have
        to be set.

        Args:
            plot_item: Plot Item the curve is created for
            data_model: Either an Update Source or a already initialized data
                        model
            buffer_size: Buffer size, which will be passed to the data model,
                         will only be used if the data_model is only an Update
                         Source.
            **plotdataitem_kwargs: Further Keyword Arguments for the PlotDataItem
        """
        if isinstance(data_model, UpdateSource):
            data_model = LiveCurveDataModel(
                data_source=data_model,
                buffer_size=buffer_size,
            )
        if data_model is not None:
            super().__init__(
                plot_item=plot_item,
                data_model=data_model,
                pen=pen,
                **plotdataitem_kwargs,
            )
        else:
            raise TypeError("Need either data source or data model to create "
                            f"a {type(self).__name__} instance")

    @classmethod
    def clone(
            cls: Type["LivePlotCurve"],
            object_to_create_from: "LivePlotCurve",
            **plotdataitem_kwargs,
    ) -> "LivePlotCurve":
        """
        Clone graph item from existing one. The data model is shared, but the new graph item
        is fitted to the old graph item's parent plot item's style. If this one has changed
        since the creation of the old graph item, the new graph item will have the new style.

        Args:
            object_to_create_from: object which f.e. data model should be taken from
            **plotdataitem_kwargs: Keyword arguments for the PlotDataItem base class

        Returns:
            New live data curve with the data model from the old passed one
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

    def _set_data(self, x: np.ndarray, y: np.ndarray) -> None:
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
        curve_arguments: Dict = {}
        for orig_key, curve_key in _PLOTDATAITEM_CURVE_PARAM_MAPPING:
            curve_arguments[curve_key] = self.opts[orig_key]
        scatter_arguments: Dict = {}
        for orig_key, scatter_key in _PLOTDATAITEM_SCATTER_PARAM_MAPPING:
            if orig_key in self.opts:
                scatter_arguments[scatter_key] = self.opts[orig_key]
        if (self.opts.get("pen") is not None
                or (self.opts.get("brush") is not None
                    and self.opts.get("fillLevel") is not None)):
            self.curve.setData(x=x, y=y, **curve_arguments)
            self.curve.show()
        else:
            self.curve.hide()
        if self.opts.get("symbol") is not None:
            data_x_wo_nans, data_y_wo_nans = LivePlotCurve._without_nan_values(x_values=x, y_values=y)
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
    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: Union[UpdateSource, LiveCurveDataModel],
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            pen=DEFAULT_COLOR,
            **plotdataitem_kwargs,
    ):
        """
        PlotDataItem extension for the Cyclic Plotting Style

        Displays data as a cyclic plot widget similar to a heart rate
        monitor. The graph itself stays fixed in position and has a fixed length
        that it does not exceed. As soon as the drawing reaches the end, the graph
        gets redrawn beginning from the start. The old curve gets incrementally
        overwritten by the new values. The x-values of all lines in the graph will
        be shifted backwards according to the time span length (like x % time_span_length)
        so the area with the curve does not move.

        Args:
            plot_item: plot item the curve should fit to
            data_model: Either an Update Source or a already initialized data
                        model
            buffer_size: Buffer size, which will be passed to the data model,
                         will only be used if the data_model is only an Update
                         Source.
            pen: pen the curve should be drawn with, is part of the PlotDataItem
                 base class parameters
            **plotdataitem_kwargs: keyword arguments fo the base class

        Raises:
            ValueError: The passes data source is not usable as a source for data
        """
        super().__init__(
            plot_item=plot_item,
            data_model=data_model,
            buffer_size=buffer_size,
            pen=pen,
            **plotdataitem_kwargs,
        )
        # Curves after clipping (data actually drawn)
        self._clipped_curve_old: CurveData = CurveData(np.array([]), np.array([]))
        self._clipped_curve_new: CurveData = CurveData(np.array([]), np.array([]))

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        self._update_new_curve_data_item()
        if cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).cycle > 0:
            self._update_old_curve_data_item()
        self._redraw_curve()

    def _redraw_curve(self) -> None:
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

    def _update_new_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        start = self._parent_plot_item.time_span.start
        end = self._parent_plot_item.last_timestamp
        x_values, y_values = self._data_model.subset_for_xrange(start=start, end=end, interpolated=True)
        self._clipped_curve_new = CurveData(
            x=x_values - cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).curr_offset,
            y=y_values,
        )

    def _update_old_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        start = self._parent_plot_item.last_timestamp - self._parent_plot_item.time_span.time_span.size
        end = cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).prev_end
        x_values, y_values = self._data_model.subset_for_xrange(start=start, end=end, interpolated=True)
        self._clipped_curve_old = CurveData(
            x=x_values - cast(CyclicPlotTimeSpan, self._parent_plot_item.time_span).prev_offset,
            y=y_values,
        )


class ScrollingPlotCurve(LivePlotCurve):
    """ Scrolling Plot Curve

    A single curve scrolling towards newer timestamps as new values arrive.
    The shown range has always the same length.
    """

    supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
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
        self._data_item_data = CurveData(x=curve_x, y=curve_y)


class StaticPlotCurve(AbstractBasePlotCurve):

    """
    Curve Item for displaying static data, where new arriving data replaces
    the old one entirely.

    One example use case would be displaying waveform plots.
    """

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticCurveDataModel

    def update_item(self) -> None:
        """Get the full data of the data buffer and display it."""
        self.setData(*self._data_model.full_data_buffer)


class EditablePlotCurve(AbstractBasePlotCurve):

    """Curve Item for displaying editable data."""

    supported_plotting_style = PlotWidgetStyle.EDITABLE
    data_model_type = EditableCurveDataModel

    sig_selection_changed = Signal(CurveData)
    """
    Signal informing about any changes to the current selection. If the emitted
    data is empty, the current selection was unselected. The signal will also
    be emitted, if the current selection has been moved around by dragging.
    """

    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: AbstractBaseDataModel,
            pen=DEFAULT_COLOR,
            **plotdataitem_kwargs,
    ):
        """Base class for different live data curves.

        Args:
            plot_item: plot item the curve should fit to
            data_model: Data Model the curve is based on
            pen: pen the curve should be drawn with, is part of the PlotDataItem
                 base class parameters
            **plotdataitem_kwargs: keyword arguments fo the base class

        Raises:
            ValueError: The passes data source is not usable as a source for data
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

    def select(self, selection: QRectF) -> None:
        """
        Select data from the curve using the passed rectangle. The rectangle
        coordinates are given in scene coordinates.

        Args:
            selection: rectangle for selecting new points
        """
        self._update_selected_indices(selection)
        if self._selected_indices is not None and len(self._selected_indices) > 0:
            x, y = self.getData()
            x_selection = x[self._selected_indices]
            y_selection = y[self._selected_indices]
            self._selection.setData(x_selection, y_selection)
            self._stylize_selection_marker()
            self._selection.sig_selection_moved.connect(self._selection_edited)
            # Inform about selection changes
            self.sig_selection_changed.emit(CurveData(x_selection, y_selection))
        else:
            self.unselect()

    def unselect(self) -> None:
        """Unselect prior done selections."""
        self._update_selected_indices(None)
        self._selection.setData([], [])
        # Inform about point being unselected
        self.sig_selection_changed.emit(CurveData([], []))
        try:
            self._selection.sig_selection_moved.disconnect(self._selection_edited)
        except TypeError:
            # If no selection has been made in selection mode no signal was
            # connected
            pass

    def update_item(self) -> None:
        """Get the full data of the data buffer and display it."""
        self.setData(*self._data_model.full_data_buffer)

    @property
    def selection(self) -> "DataSelectionMarker":
        """Marker item for the currently selected data."""
        return self._selection

    # ~~~~~~~~~~~~~~~ Wrapped from data model ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def send_current_state(self) -> bool:
        """Send the state back through the update source.

        Returns:
            True if there was a state to send
        """
        return self._editable_model.send_current_state()

    @property
    def undoable(self) -> bool:
        """Is there an older state we can roll back to?"""
        return self._editable_model.undoable

    @property
    def redoable(self) -> bool:
        """Is there a newer state we can jump to?"""
        return self._editable_model.redoable

    def undo(self) -> None:
        """Jump to the next older state."""
        self._editable_model.undo()

    def redo(self) -> None:
        """Jump to the next newer state."""
        self._editable_model.redo()

    # ~~~~~~~~~~~~~~~~~~~~ Private ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _update_selected_indices(self, selection: Optional[QRectF]) -> None:
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

    def _stylize_selection_marker(self) -> None:
        """
        Style the selected points with different colors so they are easily
        visible.
        """
        sym = self.opts.get("symbol")
        if sym:
            self._selection.setBrush(None)
            self._selection.setSymbol(sym)
        else:
            self._selection.setBrush("w")
        # We need a minimum size so we can comfortably drag it with the mouse
        sym_size = max(self.opts["symbolSize"] + 2, 5)
        self._selection.setSize(sym_size)
        pen_color = pg.mkPen(self.opts["symbolPen"]).color()
        sym_pen = pg.mkPen(DataSelectionMarker.complementary(pen_color))
        sym_pen.setWidth(3)
        self._selection.setPen(sym_pen)

    def _selection_edited(self, data: np.ndarray) -> None:
        """Apply the editing of the DataSelectionMarker to the this curve

        Args:
            data: data to apply to this curve from the selection marker
        """
        orig = np.array(self.getData())
        orig[0][self._selected_indices] = data[0]
        orig[1][self._selected_indices] = data[1]
        # we do not want to set the view data directly but go the route through
        # the data model, the view will be updated automatically through the
        # connection between the view and the model
        self._editable_model.handle_editing(CurveData(*orig))
        # Inform about selection movement to the outside
        self.sig_selection_changed.emit(CurveData(*data))

    @property
    def _editable_model(self) -> EditableCurveDataModel:
        """Accessing the datamodel through this saves you from casting."""
        return cast(EditableCurveDataModel, self.model())


class DragDirection(Flag):
    """
    Enumeration for defining in the direction in which points in a
    DataSelectionMarker should be draggable.
    """
    X = auto()
    Y = auto()


class DataSelectionMarker(pg.ScatterPlotItem):

    sig_selection_moved = Signal(np.ndarray)
    """
    As soon as a move was done successfully, this signal will emit the new
    position of the data displayed by this marker.
    """

    def __init__(self,
                 direction: DragDirection = DragDirection.Y,
                 label_points: bool = False,
                 *args,
                 **kwargs):
        """
        Data selection markers are scatter plots, that can be moved around.

        Args:
            direction: In which direction should the points be draggable
            label_points: Label each points position individually
            args: Positional arguments for the ScatterPlotItem
            kwargs: Keyword arguments for the ScatterPlotItem
        """
        self._point_labels: List[pg.TestItem] = []
        self._points_labeled = label_points
        super().__init__(*args, **kwargs)
        self._drag_direction = direction
        # State of the current drag event
        self._drag_start: Optional[QPointF] = None
        self._drag_point: Optional[pg.SpotItem] = None
        self._original_data: Optional[np.ndarray] = None

    def mouseDragEvent(self, ev: QGraphicsSceneMouseEvent):
        """Custom mouse drag event for moving the selection around.
        If there are no points under the drag events starting position, it
        will be ignored.

        Args:
            ev: mouse drag event to move the selection
        """
        if ev.button() != Qt.LeftButton:
            ev.ignore()
            return
        if ev.isStart():
            self._original_data = np.array(self.getData())
            try:
                self._drag_point = self.pointsAt(ev.buttonDownPos())[0]
                self._drag_start = -1 * ev.buttonDownPos()
                ev.accept()
            except IndexError:
                pass
            return
        elif ev.isFinish():
            self._drag_start = None
            self.sig_selection_moved.emit(np.array(self.getData()))
            return
        # Event is currently running
        if self._drag_point is None:
            ev.ignore()
            return
        else:
            data = np.copy(self._original_data)
            apply_x = self._drag_direction & DragDirection.X
            apply_y = self._drag_direction & DragDirection.Y
            x_offset = ev.pos().x() + cast(QPointF, self._drag_start).x() if apply_x else 0.0
            y_offset = ev.pos().y() + cast(QPointF, self._drag_start).y() if apply_y else 0.0
            if x_offset or y_offset:
                data[0] += x_offset if apply_x else 0.0
                data[1] += y_offset if apply_y else 0.0
                self.setData(data[0, :], data[1, :])

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
                **kwargs) -> None:
        """Extend setData with setting labels for each point

        If there is only one unnamed argument, it will be interpreted like the 'spots' argument.
        If there are two unnamed arguments, they will be interpreted as sequences of x and y values.

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
        if self._points_labeled:
            self._add_labels()
        else:
            self._remove_labels()

    @property
    def points_labeled(self) -> bool:
        """Is each selected points position decorated with and label"""
        return self._points_labeled

    @points_labeled.setter
    def points_labeled(self, label_points: bool) -> None:
        """Is each selected points position decorated with and label"""
        self._points_labeled = label_points

    @property
    def drag_direction(self) -> DragDirection:
        """In which direction should the points be draggable"""
        return self._drag_direction

    @drag_direction.setter
    def drag_direction(self, direction: DragDirection):
        """In which direction should the points be draggable"""
        self._drag_direction = direction

    def _add_labels(self) -> None:
        """
        For each point, add a label showing the position of the point in the
        direction it can be dragged in.
        """
        self._remove_labels()
        for data in self.data:
            text = self._point_label(x=data["x"],
                                     y=data["y"])
            label = pg.TextItem(text,
                                anchor=(0.5, -0.5))
            label.setParentItem(self)
            label.setPos(data["x"], data["y"])
            self._point_labels.append(label)

    def _remove_labels(self) -> None:
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
        if self._drag_direction & DragDirection.X:
            label.append("x: {:.3}".format(x))
        if self._drag_direction & DragDirection.Y:
            label.append("y: {:.3}".format(y))
        return ", ".join(label)

    @staticmethod
    def complementary(color: QColor) -> QColor:
        """
        Get the complementary QColor to a given color. For (nearly) white, grey
        and black colors, red is returned as the complementary color and not
        another greyish color
        """
        rgb = [color.red(), color.green(), color.blue()]
        # Color is somewhat greyish
        if max(rgb) - min(rgb) < 10:
            return pg.mkColor("r")
        return QColor(
            255 - color.red(),
            255 - color.green(),
            255 - color.blue(),
            color.alpha(),
        )
