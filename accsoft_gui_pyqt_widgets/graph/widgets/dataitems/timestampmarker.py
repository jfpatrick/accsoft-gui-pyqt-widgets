"""Scrolling Bar Chart for live data plotting"""

import abc
from typing import List

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
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotcycle import ScrollingPlotCycle


class LiveTimestampMarker(DataModelBasedItem, pyqtgraph.GraphicsObject, metaclass=AbstractDataModelBasedItemMeta):

    """Baseclass for an InfiniteLine based marking of specific timestamps

    Since this class does only create InfiniteLines but does not paint itself,
    the right QtGraphicsItem Flags have to be set, so the class does not have
    to provide its own Bounding Rectangle.
    """

    def __init__(
        self,
        *graphicsobjectargs,
        data_source: UpdateSource,
        plot_item: pyqtgraph.PlotItem,
        plot_config: ExPlotWidgetConfig,
        timing_source_attached: bool,
        buffer_size: int = DEFAULT_BUFFER_SIZE
    ):
        """
        Constructor for baseclass, use constructors of subclasses
        """
        data_model = TimestampMarkerDataModel(
            data_source=data_source,
            buffer_size=buffer_size
        )
        pyqtgraph.GraphicsObject.__init__(self, *graphicsobjectargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            timing_source_attached=timing_source_attached,
            parent_plot_item=plot_item,
        )
        self._plot_config: ExPlotWidgetConfig = plot_config
        self._line_elements: List[pyqtgraph.InfiniteLine] = []

    @staticmethod
    def create(
        *graphicsobjectargs,
        data_source: UpdateSource,
        plot_item: pyqtgraph.PlotDataItem,
        buffer_size: int = DEFAULT_BUFFER_SIZE
    ) -> "LiveTimestampMarker":
        """Factory method for creating line object fitting the passed plot"""
        plot_config = plot_item.plot_config
        if plot_config.plotting_style != PlotWidgetStyle.SCROLLING_PLOT:
            raise TypeError(f"Unsupported plotting style: {plot_config.plotting_style}")
        return ScrollingTimestampMarker(
            *graphicsobjectargs,
            plot_item=plot_item,
            plot_config=plot_config,
            data_source=data_source,
            timing_source_attached=plot_item.timing_source_attached,
            buffer_size=buffer_size
        )

    @abc.abstractmethod
    def update_timestamp(self, new_timestamp: float) -> None:
        """ Update the timestamp and react to the update

        Args:
            new_timestamp: The new timestamp that is supposed to be reacted to

        Returns:
            None
        """
        pass

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

    # Override
    def flags(self):
        """ ItemHasNoContents -> we do not have to provide a bounding rectangle for the ViewBox """
        return QGraphicsItem.ItemHasNoContents

    # Override
    def paint(self, *args):
        """
        paint function has to be implemented but this component only
        creates InfiniteLines and does not paint anything, so we can pass
        """
        pass

    # Override
    def boundingRect(self):
        """
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

    def __init__(self, *graphicsobjectargs, **kwargs):
        super().__init__(*graphicsobjectargs, **kwargs)
        self._cycle = ScrollingPlotCycle(
            plot_config=self._plot_config,
            size=self._plot_config.cycle_size
        )

    def update_timestamp(self, new_timestamp: float) -> None:
        """Handle a new timestamp

        Handle a new arriving timestamp that determines what part of the
        data is supposed to be shown.

        Args:
            new_timestamp (float): The new published timestamp
        """
        if new_timestamp >= self._last_timestamp:
            self._last_timestamp = new_timestamp
            self._cycle.number = (
                int(new_timestamp - self._cycle.start) // self._cycle.size
            )
            self._update_lines()

    def _update_lines(self):
        """Redraw the data as bars

        Select data according to the cycle size and the latest timestamp
        and redraw the bars of the graph from this data.
        """
        self._cycle.update_cycle(self._last_timestamp)
        curve_x, colors, labels = self._data_model.get_subset(
            start=self._cycle.start, end=self._cycle.end
        )
        if curve_x.size == colors.size == labels.size and curve_x.size > 0:
            self._clear_infinite_lines()
            for x_value, color, label in zip(curve_x, colors, labels):
                self._add_line_at_position(x_position=x_value, color=color, label=label)
