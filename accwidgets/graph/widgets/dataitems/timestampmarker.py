"""Scrolling Bar Chart for live data plotting"""

import pyqtgraph as pg
from typing import List, Type, Union
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtCore import QRectF
from accwidgets.graph import (UpdateSource, LiveTimestampMarkerDataModel, StaticTimestampMarkerDataModel,
                              AbstractBaseDataModel, DEFAULT_BUFFER_SIZE, DataModelBasedItem,
                              PlotWidgetStyle)
from accwidgets.qt import AbstractQGraphicsItemMeta
from accwidgets._deprecations import deprecated_param_alias
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph import ExPlotItem

"""which plotting style is achieved by which class"""


class AbstractBaseTimestampMarker(DataModelBasedItem, pg.GraphicsObject, metaclass=AbstractQGraphicsItemMeta):

    def __init__(self,
                 *graphicsobjectargs,
                 data_model: AbstractBaseDataModel,
                 plot_item: "ExPlotItem"):
        """
        Base class for timestamp markers.

        Args:
            *graphicsobjectargs: Positional arguments for the :class:`~pyqtgraph.GraphicsObject` constructor
                                 (the base class of the marker).
            data_model: Data model serving the item.
            plot_item: Parent plot item.
        """
        pg.GraphicsObject.__init__(self, *graphicsobjectargs)
        DataModelBasedItem.__init__(self,
                                    data_model=data_model,
                                    parent_plot_item=plot_item)
        self._line_elements: List[pg.InfiniteLine] = []
        self.opts = {
            # pen width shared among all pens for the InfiniteLines
            "pen_width": 1,
        }

    @classmethod
    def from_plot_item(cls,  # type: ignore
                       *graphicsobjectargs,
                       plot_item: "ExPlotItem",
                       data_source: UpdateSource,
                       buffer_size: int = DEFAULT_BUFFER_SIZE) -> "AbstractBaseTimestampMarker":
        """
        Factory method for creating timestamp marker objects matching the given plot item.

        This function allows easier creation of proper items by using the right type.
        It only initializes the item but does not yet add it to the plot item.

        Args:
            *graphicsobjectargs: Positional arguments for the :class:`~pyqtgraph.GraphicsObject` constructor
                                 (the base class of the marker).
            plot_item: Plot item the item should fit to.
            data_source: Source the item receives data from.
            buffer_size: Amount of values that data model's buffer is able to accommodate.

        Returns:
            A new timestamp marker which receives data from the given data source.
        """
        subclass = cls.get_subclass_fitting_plotting_style(plot_item=plot_item)
        data_model = subclass.data_model_type(data_source=data_source,
                                              buffer_size=buffer_size)
        return subclass(*graphicsobjectargs,
                        plot_item=plot_item,
                        data_model=data_model)

    def flags(self):
        """
        Returns this item's flags. The flags describe what configurable features of the item are enabled and not.
        For example, if the flags include ``ItemIsFocusable``, the item can accept input focus.

        Since this class does only create infinite lines but does not paint itself,
        the right flags have to be set, so the class does not have to provide its own bounding rectangle
        (:attr:`QGraphicsItem.ItemHasNoContents`).
        """
        return QGraphicsItem.ItemHasNoContents

    def paint(self, p: QPainter, *args):
        """
        Overrides parent :meth:`~QGraphicsItem.paint`.
        Paint function must be implemented but this component paints nothing,
        only creates infinite lines.

        Args:
            p: QPainter that is used to paint this item
            *args: Any additional arguments that will be ignored.
        """
        pass

    def boundingRect(self) -> QRectF:
        """
        Overrides parent :meth:`~QGraphicsItem.boundingRect`.

        Since this component is not painting anything, it does not
        matter what we pass back (as long as it is in the boundaries
        of the internal bounding rectangle of the infinite lines).

        Returns:
            Bounding rectangle of the first line element.
        """
        try:
            return self._line_elements[0].boundingRect()
        except IndexError:
            return QRectF(0.0, 0.0, 0.0, 0.0)

    def _clear_infinite_lines(self):
        for line in self._line_elements:
            self.getViewBox().removeItem(line)
        self._line_elements.clear()

    def _add_line_at_position(self, x_position: float, color: str, label: str):
        pen = pg.mkPen(color=color, width=self.opts.get("pen_width"))
        infinite_line = pg.InfiniteLine(pos=x_position,
                                        pen=pen,
                                        label=label,
                                        labelOpts={
                                            "position": 0.95,
                                            "fill": (255, 255, 255, 200),
                                            "color": (0, 0, 0),
                                        })
        infinite_line.label.anchors = [(0.5, 0.5), (0.5, 0.5)]
        # When setting a parent, the new infinite line is automatically added
        # to the parent's scene. This makes sure all created infinite lines
        # are properly removed when the parent is removed from a scene.
        infinite_line.setParentItem(self)
        self._line_elements.append(infinite_line)


class LiveTimestampMarker(AbstractBaseTimestampMarker):

    data_model_type = LiveTimestampMarkerDataModel

    @deprecated_param_alias(data_source="data_model")
    def __init__(self,
                 *graphicsobjectargs,
                 plot_item: "ExPlotItem",
                 data_model: Union[UpdateSource, LiveTimestampMarkerDataModel],
                 buffer_size: int = DEFAULT_BUFFER_SIZE):
        """
        Base class for live timestamp markers.

        Args:
            *graphicsobjectargs: Positional arguments for the :class:`~pyqtgraph.GraphicsObject` constructor
                                 (the base class of the marker).
            plot_item: Parent plot item.
            data_model: Either an update source or an already intialized data model.
            buffer_size: Amount of values that data model's buffer is able to accommodate.
        """
        if isinstance(data_model, UpdateSource):
            data_model = LiveTimestampMarkerDataModel(data_source=data_model,
                                                      buffer_size=buffer_size)
        if data_model is not None:
            super().__init__(*graphicsobjectargs,
                             plot_item=plot_item,
                             data_model=data_model)
        else:
            raise TypeError("Need either data source or data model to create "
                            f"a {type(self).__name__} instance")

    @classmethod
    def clone(cls: Type["LiveTimestampMarker"],
              *graphicsobjectargs,
              object_to_create_from: "LiveTimestampMarker"):
        """
        Clone graph item from an existing one. The data model is shared, but the new graph item
        is relying on the style of the old graph's parent plot item. If this style has changed
        since the creation of the old graph item, the new graph item will also have the new style.

        Args:
            *graphicsobjectargs: Positional arguments for the :class:`~pyqtgraph.GraphicsObject` constructor
                                 (the base class of the marker).
            object_to_create_from: Source object.

        Returns:
            New live timestamp marker with the data model from the old one.
        """
        item_class: Type = LiveTimestampMarker.get_subclass_fitting_plotting_style(
            plot_item=object_to_create_from._parent_plot_item)
        return item_class(*graphicsobjectargs,
                          plot_item=object_to_create_from._parent_plot_item,
                          data_model=object_to_create_from._data_model)


class ScrollingTimestampMarker(LiveTimestampMarker):
    """Timestamp marker to display live data in a :class:`ScrollingPlotWidget`."""

    supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    def update_item(self):
        curve_x, colors, labels = self._data_model.subset_for_xrange(start=self._parent_plot_item.time_span.start,
                                                                     end=self._parent_plot_item.time_span.end)
        if curve_x.size == colors.size == labels.size and curve_x.size > 0:
            self._clear_infinite_lines()
            for x_value, color, label in zip(curve_x, colors, labels):
                self._add_line_at_position(x_position=x_value, color=color, label=label)


class StaticTimestampMarker(AbstractBaseTimestampMarker):
    """Timestamp marker to display live data in a :class:`StaticPlotWidget`."""

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticTimestampMarkerDataModel

    def update_item(self):
        """Update item with the entire saved in the data model."""
        curve_x, colors, labels = self._data_model.full_data_buffer
        if curve_x.size == colors.size == labels.size and curve_x.size > 0:
            self._clear_infinite_lines()
            for x_value, color, label in zip(curve_x, colors, labels):
                self._add_line_at_position(x_position=x_value, color=color, label=label)
