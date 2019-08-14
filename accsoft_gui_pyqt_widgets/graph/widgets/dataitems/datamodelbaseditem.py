"""Module with baseclasses for attaching pyqtgraph based items to a datamodel"""

import abc
import logging
from typing import List, Optional

import numpy as np
import pyqtgraph

from accsoft_gui_pyqt_widgets.graph.datamodel.itemdatamodel import BaseDataModel
from accsoft_gui_pyqt_widgets.graph.widgets.plotconfiguration import ExPlotWidgetConfig, PlotWidgetStyle

_LOGGER = logging.getLogger(__name__)

class DataModelBasedItem(metaclass=abc.ABCMeta):

    """ Baseclass for DataSource based graphitems

    Baseclass for attaching an pyqtgraph based item do a datasource.
    By subclassing this class and implementing the mandatory functions the
    item is attached to the datasource and can react to changes in its data
    """

    def __init__(
        self,
        timing_source_attached: bool,
        data_model: BaseDataModel,
        parent_plot_item: pyqtgraph.PlotItem,
    ):
        self._data_model: BaseDataModel = data_model
        self._data_model.sig_model_has_changed.connect(self._data_model_change_handler)
        self._last_timestamp: float = -1.0
        self._timing_source_attached: bool = timing_source_attached
        self._parent_plot_item: pyqtgraph.PlotItem = parent_plot_item
        self._layer_identifier: str = ""

    def _data_model_change_handler(self):
        """ Handle change in the data model

        If the PlotItem that contains this item is attached to a timing source,
        we can normally update the items shown data. If no timing source is attached,
        we simply use the timestamp of the last value to handle the timing updates.
        This we can do by passing the new timestamp to the parent plotitem.
        Additional functionality can be implemented in each subclass

        Returns:
            None
        """
        if not self._timing_source_attached:
            possible_ts = self._data_model.get_highest_primary_value()
            if possible_ts is not None and not np.isnan(possible_ts):
                self._last_timestamp = possible_ts
                self._parent_plot_item.handle_timing_update(self._last_timestamp)
        elif self._timing_source_attached and self._last_timestamp != -1:
            self.update_timestamp(self._last_timestamp)

    def get_layer_identifier(self):
        """Get the identifier of the layer the object has been created in"""
        if self._layer_identifier is None:
            return ""
        return self._layer_identifier

    # ~~~~~ Functions mandatory to implement ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @abc.abstractmethod
    def update_timestamp(self, new_timestamp: float) -> None:
        """ React to the new available timestamp

        Args:
            new_timestamp: The new timestamp that is supposed to used for plotting

        Returns:
            None
        """
        pass

    def set_layer_information(self, layer_identifier: str) -> None:
        """Get the identifier of the layer the item is drawn in"""
        self._layer_identifier = layer_identifier

    def get_layer_identifier(self) -> str:
        """Get the identifier of the layer the item is drawn in"""
        return self._layer_identifier

    @staticmethod
    def check_plotting_style_support(
            plot_config: ExPlotWidgetConfig,
            supported_styles: List[PlotWidgetStyle]
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
            raise TypeError(f"Unsupported plotting style: {plot_config.plotting_style}")


class AbstractDataModelBasedItemMeta(type(pyqtgraph.GraphicsObject), type(DataModelBasedItem)):

    """ Metaclass to avoid metaclass conflicts

    By creating a Metaclass that derives from GraphicsObject and our DataModelBasedItem
    (which uses ABCMeta as metaclass) we can avoid the following metaclass conflict:

    TypeError: metaclass conflict: the metaclass of a derived class must be
    a (non-strict) subclass of the metaclasses of all its bases
    """

    pass
