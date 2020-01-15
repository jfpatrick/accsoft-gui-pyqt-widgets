"""Scrolling Bar Chart for live data plotting"""

from typing import List, Type, Optional

import pyqtgraph as pg
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtCore import QRectF

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import LiveTimestampMarkerDataModel, StaticTimestampMarkerDataModel
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta,
)
from accwidgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem

"""which plotting style is achieved by which class"""


class AbstractBaseTimestampMarker(DataModelBasedItem, pg.GraphicsObject, metaclass=AbstractDataModelBasedItemMeta):

    def __init__(
            self,
            *graphicsobjectargs,
            data_model: LiveTimestampMarkerDataModel,
            plot_item: "ExPlotItem",
    ):
        """ Base class for an InfiniteLine based marking of specific timestamps

        Args:
            *graphicsobjectargs: Positional arguments for baseclass GraphicsObject
            data_source: source for data updates
            plot_item: PlotItem this item will be added to
        """
        pg.GraphicsObject.__init__(self, *graphicsobjectargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        self._line_elements: List[pg.InfiniteLine] = []
        self.opts = {
            # pen width shared among all pens for the InfiniteLines
            "pen_width": 1,
        }

    @classmethod
    def from_plot_item(
            cls,
            *graphicsobjectargs,
            plot_item: "ExPlotItem",
            data_source: UpdateSource,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
    ) -> "AbstractBaseTimestampMarker":
        """Factory method for creating curve object fitting to the given plot item.

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plot item by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            *graphicsobjectargs: Arguments for base class
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's data model's buffer should hold at max

        Returns:
            the created item
        """
        subclass = cls.get_subclass_fitting_plotting_style(plot_item=plot_item)
        data_model = subclass.data_model_type(
            data_source=data_source,
            buffer_size=buffer_size,
        )
        return subclass(
            *graphicsobjectargs,
            plot_item=plot_item,
            data_model=data_model,
        )

    def flags(self):
        """
        Since this class does only create InfiniteLines but does not paint itself,
        the right QtGraphicsItem Flags have to be set, so the class does not have
        to provide its own Bounding Rectangle.

        ItemHasNoContents -> we do not have to provide a bounding rectangle
                             for the ViewBox
        """
        return QGraphicsItem.ItemHasNoContents

    def paint(self, p: QPainter, *args) -> None:
        """
        Overrides base's paint().
        paint function has to be implemented but this component only
        creates InfiniteLines and does not paint anything, so we can pass

        Args:
            p: QPainter that is used to paint this item
        """
        pass

    def boundingRect(self) -> QRectF:
        """
        Overrides base's boundingRect().
        Since this component is not painting anything, it does not
        matter what we pass back as long as it is in the boundaries
        of the internal InfiniteLines Bounding Rectangle

        Returns:
            Bounding Rectangle of the first line element
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
        infinite_line = pg.InfiniteLine(
            pos=x_position,
            pen=pen,
            label=label,
            labelOpts={
                "position": 0.95,
                "fill": (255, 255, 255, 200),
                "color": (0, 0, 0),
            },
        )
        infinite_line.label.anchors = [(0.5, 0.5), (0.5, 0.5)]
        # When setting a parent, the new infinite line is automatically added
        # to the parent's scene. This makes sure all created infinite lines
        # are properly removed when the parent is removed from a scene.
        infinite_line.setParentItem(self)
        self._line_elements.append(infinite_line)


class LiveTimestampMarker(AbstractBaseTimestampMarker):

    data_model_type = LiveTimestampMarkerDataModel

    def __init__(
            self,
            *graphicsobjectargs,
            plot_item: "ExPlotItem",
            data_source: Optional[UpdateSource] = None,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            data_model: Optional[LiveTimestampMarkerDataModel] = None,
    ):
        """
        Live Timestamp Marker Item, abstract base class for all live
        data timestamp marker like the scrolling timestamp marker.
        Either Data Source of data model have to be set.

        Args:
            *graphicsobjectargs: Positional arguments for baseclass GraphicsObject
            plot_item: Plot Item the curve is created for
            data_source: Source updates are passed through
            buffer_size: Buffer Size.
            data_model: If a valid data model is passed, data source and buffer
                        size are ignored
        """
        if (data_model is None or not isinstance(data_model, LiveTimestampMarkerDataModel)) and data_source is not None:
            data_model = LiveTimestampMarkerDataModel(
                data_source=data_source,
                buffer_size=buffer_size,
            )
        if data_model is not None:
            super().__init__(
                *graphicsobjectargs,
                plot_item=plot_item,
                data_model=data_model,
            )

    @classmethod
    def clone(
            cls: Type["LiveTimestampMarker"],
            *graphicsobjectargs,
            object_to_create_from: "LiveTimestampMarker",
    ):
        """
        Recreate graph item from existing one. The datamodel is shared, but the new graph item
        is fitted to the old graph item's parent plot item's style. If this one has changed
        since the creation of the old graph item, the new graph item will have the new style.

        Args:
            *graphicsobjectargs: Positional arguments for the GraphicsObject base class
            object_to_create_from: object which f.e. datamodel should be taken from

        Returns:
            New live data curve with the datamodel from the old passed one
        """
        item_class: Type = LiveTimestampMarker.get_subclass_fitting_plotting_style(
            plot_item=object_to_create_from._parent_plot_item)
        return item_class(
            *graphicsobjectargs,
            plot_item=object_to_create_from._parent_plot_item,
            data_model=object_to_create_from._data_model,
        )


class ScrollingTimestampMarker(LiveTimestampMarker):

    """
    Static Time Stamp Markers. These are vertical lines with labels on top
    which mark specific x-values. New arriving data will replace the old
    one entirely.
    """

    supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        curve_x, colors, labels = self._data_model.subset_for_xrange(
            start=self._parent_plot_item.time_span.start,
            end=self._parent_plot_item.time_span.end,
        )
        if curve_x.size == colors.size == labels.size and curve_x.size > 0:
            self._clear_infinite_lines()
            for x_value, color, label in zip(curve_x, colors, labels):
                self._add_line_at_position(x_position=x_value, color=color, label=label)


class StaticTimestampMarker(AbstractBaseTimestampMarker):

    """
    Infinite Lines that display live data that marks specific timestamps with a
    vertical colored line and a label.
    """

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticTimestampMarkerDataModel

    def update_item(self) -> None:
        """Update item with the entire saved in the data model."""
        curve_x, colors, labels = self._data_model.full_data_buffer
        if curve_x.size == colors.size == labels.size and curve_x.size > 0:
            self._clear_infinite_lines()
            for x_value, color, label in zip(curve_x, colors, labels):
                self._add_line_at_position(x_position=x_value, color=color, label=label)
