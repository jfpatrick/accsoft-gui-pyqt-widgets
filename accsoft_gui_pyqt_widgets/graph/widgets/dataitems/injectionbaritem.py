"""Scrolling Bar Chart for live-data plotting"""

import sys
from typing import List, Union, Type
from copy import copy

import pyqtgraph as pg
import numpy as np

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import InjectionBarDataModel
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import DEFAULT_COLOR
from accsoft_gui_pyqt_widgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta
)
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accsoft_gui_pyqt_widgets.graph.widgets.plotitem import ExPlotItem

# which plotting style is achieved by which class
plotting_style_to_class_mapping = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingInjectionBarGraphItem",
}


class LiveInjectionBarGraphItem(DataModelBasedItem, pg.ErrorBarItem, metaclass=AbstractDataModelBasedItemMeta):

    """Base class for different live bar graph plots"""

    supported_plotting_styles: List[PlotWidgetStyle] = [*plotting_style_to_class_mapping]

    def __init__(
        self,
        data_source: Union[UpdateSource, InjectionBarDataModel],
        plot_item: "ExPlotItem",
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        **errorbaritem_kwargs,
    ):
        """ Constructor for base class, use constructors of subclasses

        Args:
            data_source: source the item receives data from
            plot_item: plot_item the item should fit in style
            plot_config: configuration of the plot item
            timing_source_attached: is a source for timing updates attached to the plotitem
            buffer_size: count of values the items datamodel's buffer should hold at max
            **errorbaritem_kwargs: keyword arguments for the base class
        """
        if isinstance(data_source, UpdateSource):
            data_model = InjectionBarDataModel(
                data_source=data_source,
                buffer_size=buffer_size
            )
        elif isinstance(data_source, InjectionBarDataModel):
            data_model = data_source
        errorbaritem_kwargs = LiveInjectionBarGraphItem._prepare_error_bar_item_params(**errorbaritem_kwargs)
        pg.ErrorBarItem.__init__(self, **errorbaritem_kwargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        # TextItems for the labels of the injection-bars
        self._text_labels: List[pg.TextItem] = []
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
        object_to_create_from: "LiveInjectionBarGraphItem",
        **errorbaritem_kwargs,
    ) -> "LiveInjectionBarGraphItem":
        """
        Recreate graph item from existing one. The datamodel is shared, but the new graph item
        is fitted to the old graph item's parent plot item's style. If this one has changed
        since the creation of the old graph item, the new graph item will have the new style.

        Args:
            object_to_create_from: object which f.e. datamodel should be taken from
            **errorbaritem_kwargs: Keyword arguments for the ErrorBarItem base class

        Returns:
            New live data injection bar with the datamodel from the old passed one
        """
        plot_config = object_to_create_from._parent_plot_item.plot_config
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_config,
            supported_styles=LiveInjectionBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        # Take opts from old item except ones passed explicitly
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(errorbaritem_kwargs)
        return item_class(
            plot_item=object_to_create_from._parent_plot_item,
            data_source=object_to_create_from._data_model,
            **kwargs,
        )

    @staticmethod
    def create(
        data_source: UpdateSource,
        plot_item: "ExPlotItem",
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
            **errorbaritem_kwargs: keyword arguments for the items base class

        Returns:
            the created item
        """
        DataModelBasedItem.check_plotting_style_support(
            plot_config=plot_item.plot_config,
            supported_styles=LiveInjectionBarGraphItem.supported_plotting_styles
        )
        # get class fitting to plotting style and return instance
        class_name: str = plotting_style_to_class_mapping[plot_item.plot_config.plotting_style]
        item_class: Type = getattr(sys.modules[__name__], class_name)
        return item_class(
            plot_item=plot_item,
            data_source=data_source,
            buffer_size=buffer_size,
            **errorbaritem_kwargs,
        )

    def paint(self, p, *args):
        """Overrides base's paint(). Add additional functionality to the ErrorBarItems paint function"""
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
            self._text_labels.append(pg.TextItem(text=self._label_texts[index]))
            try:
                color = pg.mkPen(self.opts.get("pen", "w") or "w").color()
            except ValueError:
                color = "w"
            self._text_labels[index].setColor(color)
            self._text_labels[index].setParentItem(self)
            self._text_labels[index].setPos(x_position, self._label_y_positions[index])


class ScrollingInjectionBarGraphItem(LiveInjectionBarGraphItem):

    """Scrolling Bar Graph"""

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        curve_x, curve_y, height, width, labels = self._data_model.get_subset(
            start=self._parent_plot_item.time_span.start, end=self._parent_plot_item.time_span.end
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
