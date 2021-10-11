"""Scrolling Bar Chart for live-data plotting"""

import pyqtgraph as pg
import numpy as np
from typing import List, Type, Union, cast, TYPE_CHECKING
from copy import copy
from accwidgets.graph import (UpdateSource, LiveInjectionBarDataModel, StaticInjectionBarDataModel,
                              AbstractBaseDataModel, DEFAULT_BUFFER_SIZE, DEFAULT_COLOR, DataModelBasedItem,
                              PlotWidgetStyle)
from accwidgets.qt import AbstractQGraphicsItemMeta
if TYPE_CHECKING:
    from accwidgets.graph import ExPlotItem


_PLOTTING_STYLE_TO_CLASS_MAPPING = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingInjectionBarGraphItem",
}
"""which plotting style is achieved by which class"""


class AbstractBaseInjectionBarGraphItem(DataModelBasedItem,
                                        pg.ErrorBarItem,
                                        metaclass=AbstractQGraphicsItemMeta):

    def __init__(self,
                 data_model: AbstractBaseDataModel,
                 plot_item: "ExPlotItem",
                 **errorbaritem_kwargs):
        """
        Base class for injection bar plots.

        Args:
            data_model: Data model serving the item.
            plot_item: Parent plot item.
            **errorbaritem_kwargs: Keyword arguments for the :class:`~pyqtgraph.ErrorBarItem` constructor.
        """
        errorbaritem_kwargs = LiveInjectionBarGraphItem._prepare_error_bar_item_params(**errorbaritem_kwargs)
        pg.ErrorBarItem.__init__(self, **errorbaritem_kwargs)
        DataModelBasedItem.__init__(self,
                                    data_model=data_model,
                                    parent_plot_item=plot_item)
        # TextItems for the labels of the injection-bars
        self._text_labels: List[pg.TextItem] = []

    @classmethod
    def from_plot_item(cls,
                       plot_item: "ExPlotItem",
                       data_source: UpdateSource,
                       buffer_size: int = DEFAULT_BUFFER_SIZE,
                       **errorbaritem_kwargs) -> "AbstractBaseInjectionBarGraphItem":
        """
        Factory method for creating injection bar objects matching the given plot item.

        This function allows easier creation of proper items by using the right type.
        It only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: Plot item the item should fit to.
            data_source: Source the item receives data from.
            buffer_size: Amount of values that data model's buffer is able to accommodate.
            **errorbaritem_kwargs: Keyword arguments for the :class:`~pyqtgraph.ErrorBarItem` constructor.

        Returns:
            A new injection bar which receives data from the given data source.
        """
        subclass = cls.get_subclass_fitting_plotting_style(plot_item=plot_item)
        data_model = subclass.data_model_type(data_source=data_source,
                                              buffer_size=buffer_size)
        return subclass(plot_item=plot_item,
                        data_model=data_model,
                        **errorbaritem_kwargs)

    def _set_data(self,
                  curve_x: np.ndarray,
                  curve_y: np.ndarray,
                  height: np.ndarray,
                  width: np.ndarray,
                  labels: np.ndarray):
        """
        Set data to the injection bar graph.

        Args:
            curve_x: X values
            curve_y: Y values
            height: Height values
            width: Width values
            labels: Labels
        """
        y_wo_nan = np.nan_to_num(curve_y)
        h_wo_nan = np.nan_to_num(height)
        label_texts = labels
        label_y_positions = y_wo_nan + h_wo_nan / 2
        if curve_x.size == curve_y.size and curve_x.size > 0:
            # beam = self.opts.get("beam") or height.max() * 0.1
            beam = self.opts.get("beam", 0.0) or 0.0
            self.setData(x=curve_x,
                         y=curve_y,
                         height=height,
                         width=width,
                         beam=beam)
            self._draw_injector_bar_labels(label_texts, label_y_positions)

    def _draw_injector_bar_labels(self, texts: np.ndarray, y_values: np.ndarray):
        """
        Draw a specified label at a specific position.

        Args:
            texts: Array of text for the labels
            y_values: y values
        """
        x_values = self.opts["x"]
        self._clear_labels()
        for x, y, text in zip(x_values, y_values, texts):
            try:
                color = pg.mkPen(self.opts.get("pen", "w") or "w").color()
            except ValueError:
                color = "w"
            label = pg.TextItem(text=text,
                                color=color)
            label.setPos(x, y)
            self._text_labels.append(label)
            label.setParentItem(self)

    def _clear_labels(self):
        """Remove all labels from the ViewBox."""
        for label in self._text_labels:
            self.getViewBox().removeItem(label)
        self._text_labels.clear()


class LiveInjectionBarGraphItem(AbstractBaseInjectionBarGraphItem):

    data_model_type = LiveInjectionBarDataModel

    def __init__(self,
                 plot_item: "ExPlotItem",
                 data_model: Union[LiveInjectionBarDataModel, UpdateSource],
                 buffer_size: int = DEFAULT_BUFFER_SIZE,
                 **errorbaritem_kwargs):
        """
        Base class for live injection bar plots.

        Args:
            plot_item: Parent plot item.
            data_model: Either an update source or an already intialized data model.
            buffer_size: Amount of values that data model's buffer is able to accommodate.
            **errorbaritem_kwargs: Keyword arguments for the :class:`~pyqtgraph.ErrorBarItem` constructor.
        """
        if isinstance(data_model, UpdateSource):
            data_model = LiveInjectionBarDataModel(data_source=data_model,
                                                   buffer_size=buffer_size)
        if data_model is not None:
            super().__init__(plot_item=plot_item,
                             data_model=data_model,
                             **errorbaritem_kwargs)
        else:
            raise TypeError("Need either data source or data model to create "
                            f"a {type(self).__name__} instance")

    @classmethod
    def clone(cls: Type["LiveInjectionBarGraphItem"],
              object_to_create_from: "LiveInjectionBarGraphItem",
              **errorbaritem_kwargs) -> "LiveInjectionBarGraphItem":
        """
        Clone graph item from an existing one. The data model is shared, but the new graph item
        is relying on the style of the old graph's parent plot item. If this style has changed
        since the creation of the old graph item, the new graph item will also have the new style.

        Args:
            object_to_create_from: Source object.
            **errorbaritem_kwargs: Keyword arguments for the :class:`~pyqtgraph.ErrorBarItem` constructor.

        Returns:
            New live injection bar with the data model from the old one.
        """
        item_class = LiveInjectionBarGraphItem.get_subclass_fitting_plotting_style(
            plot_item=object_to_create_from._parent_plot_item)
        # Take opts from old item except ones passed explicitly
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(errorbaritem_kwargs)
        return cast(Type[LiveInjectionBarGraphItem], item_class)(plot_item=object_to_create_from._parent_plot_item,
                                                                 data_model=object_to_create_from._data_model,
                                                                 **kwargs)

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


class ScrollingInjectionBarGraphItem(LiveInjectionBarGraphItem):
    """Injection bar to display live data in a :class:`ScrollingPlotWidget`."""

    supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    def update_item(self):
        self._set_data(*self._data_model.subset_for_xrange(start=self._parent_plot_item.time_span.start,
                                                           end=self._parent_plot_item.time_span.end))


class StaticInjectionBarGraphItem(AbstractBaseInjectionBarGraphItem):
    """Injection bar to display static data in a :class:`StaticPlotWidget`."""

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticInjectionBarDataModel

    def update_item(self):
        self._set_data(*self._data_model.full_data_buffer)
