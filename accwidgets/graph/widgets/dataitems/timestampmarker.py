"""Scrolling Bar Chart for live data plotting"""

import sys
from typing import List, Union, Type

import pyqtgraph as pg
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtCore import QRectF

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import LiveTimestampMarkerDataModel
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accwidgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem

_PLOTTING_STYLE_TO_CLASS_MAPPING = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingTimestampMarker",
}
"""which plotting style is achieved by which class"""


class LiveTimestampMarker(DataModelBasedItem, pg.GraphicsObject, metaclass=AbstractDataModelBasedItemMeta):

    supported_plotting_styles: List[PlotWidgetStyle] = [*_PLOTTING_STYLE_TO_CLASS_MAPPING]
    """List of plotting styles which are supported by this class's create factory function"""

    def __init__(
        self,
        *graphicsobjectargs,
        data_source: Union[UpdateSource, LiveTimestampMarkerDataModel],
        plot_item: "ExPlotItem",
        buffer_size: int = DEFAULT_BUFFER_SIZE
    ):
        """ Base class for an InfiniteLine based marking of specific timestamps

        Args:
            *graphicsobjectargs: Positional arguments for baseclass GraphicsObject
            data_source: source for data updates
            plot_item: PlotItem this item will be added to
            buffer_size: Amount of entries the buffer is holding (not equal the amount of displayed entries)
        """
        if isinstance(data_source, LiveTimestampMarkerDataModel):
            data_model = data_source
        elif isinstance(data_source, UpdateSource):
            data_model = LiveTimestampMarkerDataModel(
                data_source=data_source,
                buffer_size=buffer_size
            )
        else:
            raise ValueError(
                f"Data Source of type {type(data_source)} can not be used as a source or model for data."
            )
        pg.GraphicsObject.__init__(self, *graphicsobjectargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        self._line_elements: List[pg.InfiniteLine] = []
        self.opts = {
            # pen width shared among all pens for the InfiniteLines
            "pen_width": 1
        }

    @staticmethod
    def from_plot_item(
        *graphicsobjectargs,
        data_source: UpdateSource,
        plot_item: "ExPlotItem",
        buffer_size: int = DEFAULT_BUFFER_SIZE
    ) -> "LiveTimestampMarker":
        """Factory method for creating line object fitting the passed plot"""
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_item.plot_config,
            supported_styles=LiveTimestampMarker.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = _PLOTTING_STYLE_TO_CLASS_MAPPING[plot_item.plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        return item_class(
            *graphicsobjectargs,
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size
        )

    @staticmethod
    def clone(
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
        plot_config = object_to_create_from._parent_plot_item.plot_config
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LiveTimestampMarker.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = _PLOTTING_STYLE_TO_CLASS_MAPPING[plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        return item_class(
            *graphicsobjectargs,
            plot_item=object_to_create_from._parent_plot_item,
            data_source=object_to_create_from._data_model,
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


class ScrollingTimestampMarker(LiveTimestampMarker):

    """
    Infinite Lines that display live data that marks specific timestamps with a
    vertical colored line and a label.
    """

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        curve_x, colors, labels = self._data_model.subset_for_xrange(
            start=self._parent_plot_item.time_span.start, end=self._parent_plot_item.time_span.end
        )
        if curve_x.size == colors.size == labels.size and curve_x.size > 0:
            self._clear_infinite_lines()
            for x_value, color, label in zip(curve_x, colors, labels):
                self._add_line_at_position(x_position=x_value, color=color, label=label)
