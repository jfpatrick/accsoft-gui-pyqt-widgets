"""Module with base classes for attaching pyqtgraph based items to a datamodel"""

import abc
import logging
from typing import List
from typing import TYPE_CHECKING, Type, cast, TypeVar

import numpy as np
import pyqtgraph as pg

from accwidgets.graph.datamodel.itemdatamodel import AbstractBaseDataModel
from accwidgets.graph.widgets.plotconfiguration import ExPlotWidgetConfig, PlotWidgetStyle
if TYPE_CHECKING:
    from accwidgets.graph.widgets.plotitem import ExPlotItem

_LOGGER = logging.getLogger(__name__)


_T = TypeVar("_T", bound="DataModelBasedItem")


class DataModelBasedItem(metaclass=abc.ABCMeta):

    supported_plotting_style: PlotWidgetStyle = None  # type: ignore
    """Which plotting style does this item support?"""

    data_model_type: Type[AbstractBaseDataModel] = None  # type: ignore
    """Which is the default data model type for this item."""

    def __init__(
        self,
        data_model: AbstractBaseDataModel,
        parent_plot_item: "ExPlotItem",
    ):
        """Base class for data source / data model based graph items

        Base class for attaching an pyqtgraph based item do a data source.
        By subclassing this class and implementing the mandatory functions the
        item is attached to the data source and can react to changes in its data.

        Args:
            data_model: data model for the item
            parent_plot_item: plot item this item is displayed in
        """
        self._data_model: AbstractBaseDataModel = data_model
        self._data_model.sig_data_model_changed.connect(self._handle_data_model_change)
        self._parent_plot_item: "ExPlotItem" = parent_plot_item
        self._layer_id: str = ""

    @classmethod
    def get_subclass_fitting_plotting_style(
            cls: Type[_T],
            plot_item: "ExPlotItem",
    ) -> Type[_T]:
        """

        Args:
            plot_item: Plot Item, which the item should be searched for

        Returns:
            View Item class, Data Model
        """
        fitting_classes: List[Type[_T]] = [
            c for c in DataModelBasedItem.all_subclasses(cls)
            if plot_item.plot_config.plotting_style == cast(DataModelBasedItem, c).supported_plotting_style
        ]
        if not fitting_classes:
            raise ValueError(f"No fitting subclass could be found for the plot item "
                             f"with style {plot_item.plot_config.plotting_style.value}.")
        elif len(fitting_classes) > 1:
            _LOGGER.warning(f"Multiple fitting subclasses could be found for the plot "
                            f"item with style {plot_item.plot_config.plotting_style.value}")
        return fitting_classes[0]

    @staticmethod
    def all_subclasses(cls):
        """Search for all subclasses of a class recursively."""
        return set(cls.__subclasses__()).union(
            [s for c in cls.__subclasses__() for s in DataModelBasedItem.all_subclasses(c)])

    @abc.abstractmethod
    def update_item(self) -> None:
        """Update item based on the plot items time span information"""
        pass

    @staticmethod
    def check_plotting_style_support(
            plot_config: ExPlotWidgetConfig,
            supported_styles: List[PlotWidgetStyle],
    ) -> None:
        """ Check an items plotting style compatibility

        Check if the requested plotting style is supported by this item.
        If no supported styles is passed, the function checks, if 'supported_plotting_styles'
        exists as a class or instance variable.
        If a list of supported styles is found, the requested style is checked and, if not
        fitting a TypeError is raised. If no such list is provided in any of these both ways
        or the style is supported, no Error is raised.

        Args:
            plot_config: plot configuration of the plot for which the item should be created
            supported_styles: optional list of supported styles
        """
        if not supported_styles:
            return
        if plot_config.plotting_style not in supported_styles:
            raise TypeError(f"Unsupported plotting style: {plot_config.plotting_style.name}")

    def model(self) -> AbstractBaseDataModel:
        """Data Model that the item is based on."""
        return self._data_model

    @property
    def layer_id(self) -> str:
        """Identifier of the layer the object is located in"""
        if self._layer_id is None:
            return ""
        return self._layer_id

    @layer_id.setter
    def layer_id(self, layer_id: str) -> None:
        """Set the identifier of the layer the item was added to"""
        self._layer_id = layer_id

    def _handle_data_model_change(self) -> None:
        """ Handle change in the data model

        If the PlotItem that contains this item is attached to a timing source,
        we can normally update the items shown data. If no timing source is attached,
        we simply use the timestamp of the last value to handle the timing updates.
        This we can do by passing the new timestamp to the parent plot item.
        Additional functionality can be implemented in each subclass
        """
        plot = self._parent_plot_item
        if not plot.timing_source_attached and plot.timing_source_compatible:
            possible_ts = self._data_model.max_primary_val
            if possible_ts is not None and not np.isnan(possible_ts):
                self._parent_plot_item.update_timestamp(possible_ts)
        elif not plot.timing_source_compatible or \
                (plot.timing_source_attached and plot.last_timestamp != -1.0):
            self.update_item()


class AbstractDataModelBasedItemMeta(type(pg.GraphicsObject), type(DataModelBasedItem)):  # type: ignore

    """ Metaclass to avoid metaclass conflicts

    By creating a Metaclass that derives from GraphicsObject and our DataModelBasedItem
    (which uses ABCMeta as metaclass) we can avoid the following metaclass conflict:

    TypeError: metaclass conflict: the metaclass of a derived class must be
    a (non-strict) subclass of the metaclasses of all its bases
    """

    pass
