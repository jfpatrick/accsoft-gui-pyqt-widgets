"""Scrolling Bar Chart for live-data plotting"""

import abc
from typing import List, Optional

import pyqtgraph
import numpy as np

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import InjectionBarDataModel
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotcycle import ScrollingPlotCycle


class LiveInjectionBarGraphItem(DataModelBasedItem, pyqtgraph.ErrorBarItem, metaclass=AbstractDataModelBasedItemMeta):

    """Baseclass for different live bar graph plots"""

    def __init__(
        self,
        data_source: UpdateSource,
        plot_item: pyqtgraph.PlotItem,
        plot_config: ExPlotWidgetConfig,
        timing_source_attached: bool,
        **errorbaritem_kwargs,
    ):
        """
        Constructor for baseclass, use constructors of subclasses
        """
        data_model = InjectionBarDataModel(data_source=data_source)
        pyqtgraph.ErrorBarItem.__init__(self, **errorbaritem_kwargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            timing_source_attached=timing_source_attached,
            parent_plot_item=plot_item,
        )
        self._plot_config: ExPlotWidgetConfig = plot_config
        # TextItems for the labels of the injection-bars
        self._text_labels: List[pyqtgraph.TextItem] = []
        self._label_texts: List[str] = []
        self._label_y_positions: List[float] = []

    @staticmethod
    def create(
        data_source: UpdateSource,
        plot_item: pyqtgraph.PlotDataItem,
        **errorbaritem_kwargs,
    ) -> "LiveInjectionBarGraphItem":
        """Factory method for creating injectionbar object fitting the requested style"""
        plot_config = plot_item.plot_config
        if plot_config.plotting_style != PlotWidgetStyle.SCROLLING_PLOT:
            raise TypeError(f"Unsupported plotting style: {plot_config.plotting_style}")
        return ScrollingInjectionBarGraphItem(
            plot_item=plot_item,
            data_source=data_source,
            plot_config=plot_config,
            timing_source_attached=plot_item.timing_source_attached,
            x=np.array([0.0]),
            y=np.array([0.0]),
            height=np.array([0.0]),
            width=0.3,
            **errorbaritem_kwargs,
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

    # Override
    def paint(self, p, *args):
        """Add additional functionality to the ErrorBarItems paint function"""
        super().paint(p, *args)
        self.draw_injector_bar_labels()

    def draw_injector_bar_labels(self):
        """Draw a specified label at a specific position"""
        label_position = self.opts["x"]
        self._clear_labels()
        for index, x_position in enumerate(label_position):
            self._draw_label_at_position(x_position=x_position, index=index)

    def _clear_labels(self):
        """Remove all labels from the viewbox"""
        for label in self._text_labels:
            self.getViewBox().removeItem(label)
        self._text_labels.clear()

    def _draw_label_at_position(self, x_position, index):
        """Draw a label next to the actual ErrorBarItem at a given position"""
        if 0 <= index < len(self._label_texts):
            self._text_labels.append(pyqtgraph.TextItem(text=self._label_texts[index]))
            self._text_labels[index].setColor(self.opts.get("pen", "w") or "w")
            self._text_labels[index].setParentItem(self)
            self._text_labels[index].setPos(x_position, self._label_y_positions[index])


class ScrollingInjectionBarGraphItem(LiveInjectionBarGraphItem):

    """Scrolling Bar Graph"""

    def __init__(self, **kwargs):
        """Create a new scrolling injection-bar item, for parameters see baseclass"""
        super().__init__(**kwargs)
        self._cycle = ScrollingPlotCycle(
            plot_config=self._plot_config, size=self._plot_config.cycle_size
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
            self._redraw_bars()

    def _redraw_bars(self):
        """Redraw the data as bars

        Select data according to the cycle size and the latest timestamp
        and redraw the bars of the graph from this data.
        """
        self._cycle.update_cycle(self._last_timestamp)
        curve_x, curve_y, height, width, top, bottom, labels = self._data_model.get_subset(
            start=self._cycle.start, end=self._cycle.end
        )
        self._label_texts = labels
        self._label_y_positions = [(y + h / 2) for y, h in zip(curve_y, height)]
        if curve_x.size == curve_y.size and curve_x.size > 0:
            beam = width[0] if width[0] is not None else 0.05
            self.setData(
                x=curve_x,
                y=curve_y,
                height=height,
                width=0.0,
                beam=beam,
                top=top,
                bottom=bottom,
            )
