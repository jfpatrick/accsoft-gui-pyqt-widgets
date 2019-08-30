"""Scrolling Bar Chart for live-data plotting"""

import sys
import abc
from typing import List, Union

import pyqtgraph
import numpy as np
from qtpy.QtGui import QPen

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import InjectionBarDataModel
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import DEFAULT_COLOR
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    ExPlotWidgetConfig,
    PlotWidgetStyle,
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotcycle import ScrollingPlotCycle

# which plotting style is achieved by which class
plotting_style_to_class_mapping = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingInjectionBarGraphItem",
}


class LiveInjectionBarGraphItem(DataModelBasedItem, pyqtgraph.ErrorBarItem, metaclass=AbstractDataModelBasedItemMeta):

    """Baseclass for different live bar graph plots"""

    supported_plotting_styles: List[PlotWidgetStyle] = list(plotting_style_to_class_mapping.keys())

    def __init__(
        self,
        data_source: Union[UpdateSource, InjectionBarDataModel],
        plot_item: pyqtgraph.PlotItem,
        plot_config: ExPlotWidgetConfig,
        timing_source_attached: bool,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **errorbaritem_kwargs,
    ):
        """ Constructor for baseclass, use constructors of subclasses

        Args:
            data_source: source the item receives data from
            plot_item: plot_item the item should fit in style
            plot_config: configuration of the plot item
            timing_source_attached: is a source for timing updates attached to the plotitem
            buffer_size: count of values the items datamodel's buffer should hold at max
            **errorbaritem_kwargs: keyword arguments for the baseclass
        """
        if isinstance(data_source, UpdateSource):
            data_model = InjectionBarDataModel(
                data_source=data_source,
                buffer_size=buffer_size
            )
        elif isinstance(data_source, InjectionBarDataModel):
            data_model = data_source
        errorbaritem_kwargs = LiveInjectionBarGraphItem._prepare_error_bar_item_params(**errorbaritem_kwargs)
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
    def _prepare_error_bar_item_params(**errorbaritem_kwargs):
        """For drawing the BarGraphItem needs some data to display, empty data will
        lead to Errors when trying to set the visible range (which is done when drawing).
        This functions prepares adds some data to avoid this"""
        if errorbaritem_kwargs.get("pen", None) is None:
            errorbaritem_kwargs["pen"] = DEFAULT_COLOR
        if errorbaritem_kwargs.get("x", None) is None:
            errorbaritem_kwargs["x"] = np.array([0.0])
        if errorbaritem_kwargs.get("y", None) is None:
            errorbaritem_kwargs["y"] = np.array([0.0])
        if errorbaritem_kwargs.get("height", None) is None:
            errorbaritem_kwargs["height"] = np.array([0.0])
        if errorbaritem_kwargs.get("width", None) is None:
            errorbaritem_kwargs["width"] = 0.0
        return errorbaritem_kwargs

    @staticmethod
    def create_from(
        plot_config: ExPlotWidgetConfig,
        object_to_create_from: "LiveInjectionBarGraphItem",
        **errorbaritem_kwargs,
    ) -> "LiveInjectionBarGraphItem":
        """Factory method for creating curve object fitting the requested style


        """
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LiveInjectionBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        if not errorbaritem_kwargs:
            errorbaritem_kwargs = object_to_create_from.opts
        return item_class(
            plot_item=object_to_create_from._parent_plot_item,
            plot_config=plot_config,
            data_source=object_to_create_from._data_model,
            timing_source_attached=object_to_create_from._timing_source_attached,
            **errorbaritem_kwargs,
        )

    @staticmethod
    def create(
        data_source: UpdateSource,
        plot_item: pyqtgraph.PlotDataItem,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **errorbaritem_kwargs,
    ) -> "LiveInjectionBarGraphItem":
        """Factory method for creating injectionbar object fitting the requested style

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plotitem by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's datamodel's buffer should hold at max
            **errorbaritem_kwargs: keyword arguments for the items baseclass

        Returns:
            the created item
        """
        plot_config = plot_item.plot_config
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LiveInjectionBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            data_source=data_source,
            plot_config=plot_config,
            timing_source_attached=plot_item.timing_source_attached,
            buffer_size=buffer_size,
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
            try:
                color = pyqtgraph.mkPen(self.opts.get("pen", "w") or "w").color()
            except ValueError:
                color = "w"
            self._text_labels[index].setColor(color)
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
        curve_x, curve_y, height, width, labels = self._data_model.get_subset(
            start=self._cycle.start, end=self._cycle.end
        )
        self._label_texts = labels
        self._label_y_positions = []
        for y, h in zip(curve_y, height):
            y = y if not np.isnan(y) else 0
            h = h if not np.isnan(h) else 0
            self._label_y_positions.append(y + h / 2)
        if curve_x.size == curve_y.size and curve_x.size > 0:
            # beam = self.opts.get("beam") or height.max() * 0.1
            beam = self.opts.get("beam", 0.0) or 0.0
            self.setData(
                x=curve_x,
                y=curve_y,
                height=height,
                width=width,
                beam=beam,
            )
