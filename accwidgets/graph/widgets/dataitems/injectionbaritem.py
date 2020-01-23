"""Scrolling Bar Chart for live-data plotting"""

from typing import List, Type, Union, cast
from copy import copy

import pyqtgraph as pg
import numpy as np

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.itemdatamodel import (
    LiveInjectionBarDataModel,
    StaticInjectionBarDataModel,
    AbstractBaseDataModel,
)
from accwidgets.graph.datamodel.datamodelbuffer import DEFAULT_BUFFER_SIZE
from accwidgets.graph.datamodel.datastructures import DEFAULT_COLOR
from accwidgets.graph.widgets.dataitems.datamodelbaseditem import (
    DataModelBasedItem,
    AbstractDataModelBasedItemMeta,
)
from accwidgets.graph.widgets.plotconfiguration import (
    PlotWidgetStyle,
)
from accwidgets.graph.util import deprecated_param_alias
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem

_PLOTTING_STYLE_TO_CLASS_MAPPING = {
    PlotWidgetStyle.SCROLLING_PLOT: "ScrollingInjectionBarGraphItem",
}
"""which plotting style is achieved by which class"""


class AbstractBaseInjectionBarGraphItem(DataModelBasedItem,
                                        pg.ErrorBarItem,
                                        metaclass=AbstractDataModelBasedItemMeta):

    def __init__(
        self,
        data_model: AbstractBaseDataModel,
        plot_item: "ExPlotItem",
        **errorbaritem_kwargs,
    ):
        """Base class for different live bar graph plots.

        Args:
            data_model: Data model for the curve which holds the
            plot_item: plot_item the item should fit in style
            **errorbaritem_kwargs: keyword arguments for the base class
        """
        errorbaritem_kwargs = LiveInjectionBarGraphItem._prepare_error_bar_item_params(**errorbaritem_kwargs)
        pg.ErrorBarItem.__init__(self, **errorbaritem_kwargs)
        DataModelBasedItem.__init__(
            self,
            data_model=data_model,
            parent_plot_item=plot_item,
        )
        # TextItems for the labels of the injection-bars
        self._text_labels: List[pg.TextItem] = []

    @classmethod
    def from_plot_item(
            cls,
            plot_item: "ExPlotItem",
            data_source: UpdateSource,
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **errorbaritem_kwargs,
    ) -> "AbstractBaseInjectionBarGraphItem":
        """Factory method for creating curve object fitting to the given plot item.

        This function allows easier creation of the right object instead of creating
        the right object that fits to the plotting style of the plot item by hand. This
        function only initializes the item but does not yet add it to the plot item.

        Args:
            plot_item: plot item the item should fit to
            data_source: source the item receives data from
            buffer_size: count of values the item's data model's buffer should hold at max
            **errorbaritem_kwargs: keyword arguments for the items base class

        Returns:
            the created item
        """
        subclass = cls.get_subclass_fitting_plotting_style(plot_item=plot_item)
        data_model = subclass.data_model_type(
            data_source=data_source,
            buffer_size=buffer_size,
        )
        return subclass(
            plot_item=plot_item,
            data_model=data_model,
            **errorbaritem_kwargs,
        )

    def _set_data(
            self,
            curve_x: np.ndarray,
            curve_y: np.ndarray,
            height: np.ndarray,
            width: np.ndarray,
            labels: np.ndarray,
    ) -> None:
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
            self.setData(
                x=curve_x,
                y=curve_y,
                height=height,
                width=width,
                beam=beam,
            )
            self._draw_injector_bar_labels(label_texts, label_y_positions)

    def _draw_injector_bar_labels(self, texts: np.ndarray, y_values: np.ndarray) -> None:
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
            label = pg.TextItem(
                text=text,
                color=color,
            )
            label.setPos(x, y)
            self._text_labels.append(label)
            label.setParentItem(self)

    def _clear_labels(self) -> None:
        """Remove all labels from the ViewBox."""
        for label in self._text_labels:
            self.getViewBox().removeItem(label)
        self._text_labels.clear()


class LiveInjectionBarGraphItem(AbstractBaseInjectionBarGraphItem):

    data_model_type = LiveInjectionBarDataModel

    @deprecated_param_alias(data_source="data_model")
    def __init__(
            self,
            plot_item: "ExPlotItem",
            data_model: Union[LiveInjectionBarDataModel, UpdateSource],
            buffer_size: int = DEFAULT_BUFFER_SIZE,
            **errorbaritem_kwargs,
    ):
        """
        Live Injection Bar Graph Item, abstract base class for all live
        data injection bar graphs like the scrolling injection bar graph.
        Either Data Source of data model have to be set.

        Args:
            plot_item: Plot Item the curve is created for
            data_model: Either an Update Source or a already initialized data
                        model
            buffer_size: Buffer size, which will be passed to the data model,
                         will only be used if the data_model is only an Update
                         Source.
            **errorbaritem_kwargs: Further Keyword Arguments for the ErrorBarItem
        """
        if isinstance(data_model, UpdateSource):
            data_model = LiveInjectionBarDataModel(
                data_source=data_model,
                buffer_size=buffer_size,
            )
        if data_model is not None:
            super().__init__(
                plot_item=plot_item,
                data_model=data_model,
                **errorbaritem_kwargs,
            )
        else:
            raise TypeError("Need either data source or data model to create "
                            f"a {type(self).__name__} instance")

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

    @classmethod
    def clone(
            cls: Type["LiveInjectionBarGraphItem"],
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
        item_class = LiveInjectionBarGraphItem.get_subclass_fitting_plotting_style(
            plot_item=object_to_create_from._parent_plot_item)
        # Take opts from old item except ones passed explicitly
        kwargs = copy(object_to_create_from.opts)
        kwargs.update(errorbaritem_kwargs)
        return cast(Type[LiveInjectionBarGraphItem], item_class)(
            plot_item=object_to_create_from._parent_plot_item,
            data_model=object_to_create_from._data_model,
            **kwargs,
        )


class ScrollingInjectionBarGraphItem(LiveInjectionBarGraphItem):

    """Scrolling Injection Bar Graph"""

    supported_plotting_style = PlotWidgetStyle.SCROLLING_PLOT

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        self._set_data(*self._data_model.subset_for_xrange(
            start=self._parent_plot_item.time_span.start,
            end=self._parent_plot_item.time_span.end,
        ))


class StaticInjectionBarGraphItem(AbstractBaseInjectionBarGraphItem):

    """
    Static Injection Bar Graph. Injection Bars are based on ErrorBars
    with the addition of labels. New arriving data will replace the old
    one entirely.
    """

    supported_plotting_style = PlotWidgetStyle.STATIC_PLOT
    data_model_type = StaticInjectionBarDataModel

    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        self._set_data(*self._data_model.full_data_buffer)
