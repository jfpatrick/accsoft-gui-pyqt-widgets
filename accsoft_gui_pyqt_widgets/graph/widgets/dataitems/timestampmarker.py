"""Scrolling Bar Chart for live data plotting"""

import sys
from typing import List, Union

import pyqtgraph
from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtCore import QRectF

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import TimestampMarkerDataModel
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)


# which plotting style is achieved by which class
plotting_style_to_class_mapping = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingTimestampMarker",
}


class LiveTimestampMarker(DataModelBasedItem, pyqtgraph.GraphicsObject, metaclass=AbstractDataModelBasedItemMeta):

    """Baseclass for an InfiniteLine based marking of specific timestamps

    Since this class does only create InfiniteLines but does not paint itself,
    the right QtGraphicsItem Flags have to be set, so the class does not have
    to provide its own Bounding Rectangle.
    """

    supported_plotting_styles: List[PlotWidgetStyle] = list(plotting_style_to_class_mapping.keys())

    def __init__(
        self,
        *graphicsobjectargs,
        data_source: Union[UpdateSource, TimestampMarkerDataModel],
        plot_item: pyqtgraph.PlotItem,
        buffer_size: int = DEFAULT_BUFFER_SIZE
    ):
        """
        Constructor for baseclass, use constructors of subclasses
        """
        if isinstance(data_source, TimestampMarkerDataModel):
            data_model = data_source
        elif isinstance(data_source, UpdateSource):
            data_model = TimestampMarkerDataModel(
                data_source=data_source,
                buffer_size=buffer_size
            )
        else:
            raise ValueError(
                f"Data Source of type {type(data_source)} can not be used as a source or model for data."
            )
        pyqtgraph.GraphicsObject.__init__(self, *graphicsobjectargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        self._line_elements: List[pyqtgraph.InfiniteLine] = []

    @staticmethod
    def create_from(
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
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        return item_class(
            *graphicsobjectargs,
            plot_item=object_to_create_from._parent_plot_item,
            data_source=object_to_create_from._data_model,
        )

    @staticmethod
    def create(
        *graphicsobjectargs,
        data_source: UpdateSource,
        plot_item: pyqtgraph.PlotDataItem,
        buffer_size: int = DEFAULT_BUFFER_SIZE
    ) -> "LiveTimestampMarker":
        """Factory method for creating line object fitting the passed plot"""
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_item.plot_config,
            supported_styles=LiveTimestampMarker.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_item.plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        return item_class(
            *graphicsobjectargs,
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size
        )

    def _clear_infinite_lines(self):
        for line in self._line_elements:
            self.getViewBox().removeItem(line)
        self._line_elements.clear()

    def _add_line_at_position(self, x_position: float, color: str, label: str):
        infinite_line = pyqtgraph.InfiniteLine(
            pos=x_position,
            pen=color,
            label=label,
            labelOpts={
                "position": 0.95,
                "fill": (255, 255, 255, 200),
                "color": (0, 0, 0),
            },
        )
        infinite_line.label.anchors = [(0.5, 0.5), (0.5, 0.5)]
        infinite_line.setParentItem(parent=self._parent_plot_item)
        self.getViewBox().addItem(infinite_line)
        self._line_elements.append(infinite_line)

    def flags(self):
        """
        Overrides base's flags().
        ItemHasNoContents -> we do not have to provide a bounding rectangle
        for the ViewBox
        """
        return QGraphicsItem.ItemHasNoContents

    def paint(self, *args):
        """
        Overrides base's paint().
        paint function has to be implemented but this component only
        creates InfiniteLines and does not paint anything, so we can pass
        """
        pass

    def boundingRect(self):
        """
        Overrides base's boundingRect().
        Since this component is not painting anything, it does not
        matter what we pass back as long as it is in the boundaries
        of the internal InfiniteLines Bounding Rectangle
        """
        try:
            return self._line_elements[0].boundingRect()
        except IndexError:
            return QRectF(0.0, 0.0, 0.0, 0.0)


class ScrollingTimestampMarker(LiveTimestampMarker):

    """
    Infinite Lines that display live data that marks specific timestamps with a
    vertical colored line and a label.
    """

    def update_item(self) -> None:
        """Update item based on the plot items cycle information"""
        curve_x, colors, labels = self._data_model.get_subset(
            start=self._parent_plot_item.cycle.start, end=self._parent_plot_item.cycle.end
        )
        if curve_x.size == colors.size == labels.size and curve_x.size > 0:
            self._clear_infinite_lines()
            for x_value, color, label in zip(curve_x, colors, labels):
                self._add_line_at_position(x_position=x_value, color=color, label=label)
