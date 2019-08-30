""" Data Model for one single curve. """

import abc
import logging
from typing import Optional, Tuple, Union

import numpy as np
from qtpy.QtCore import QObject, Signal, Slot

from accsoft_gui_pyqt_widgets.graph.datamodel.connection import UpdateSource
from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelbuffer import (
    DEFAULT_BUFFER_SIZE,
    SortedBarGraphDataBuffer,
    SortedCurveDataBuffer,
    BaseSortedDataBuffer,
    SortedTimestampMarkerDataBuffer,
    SortedInjectionBarsDataBuffer,
)
from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import (
    AbstractQObjectMeta,
    BarCollectionData,
    BarData,
    CurveData,
    TimestampMarkerCollectionData,
    TimestampMarkerData,
    InjectionBarCollectionData,
    InjectionBarData,
    PointData,
)

_LOGGER = logging.getLogger(__name__)


class BaseDataModel(QObject, metaclass=AbstractQObjectMeta):
    """
    Baseclass for different data models
    """

    # Signal  that is sent as soon as any data has changed
    # The new data then can be retrieved by the view
    sig_model_has_changed = Signal()

    def __init__(self, data_source: UpdateSource, buffer_size: Optional[int] = DEFAULT_BUFFER_SIZE):
        super().__init__()
        self._buffer_size = buffer_size or DEFAULT_BUFFER_SIZE
        self._full_data_buffer: BaseSortedDataBuffer
        self._data_source = data_source
        self._connect_to_data_source()
        self._non_fitting_data_info_printed: bool = False

    def replace_data_source(self, data_source: UpdateSource, clear_buffer: bool = True):
        """Replace the current data source and clear the inner saved data if wanted"""
        self._disconnect_from_data_source()
        self._data_source = data_source
        self._connect_to_data_source()
        if clear_buffer:
            self._full_data_buffer.reset()

    def _connect_to_data_source(self):
        """Connect to all available signals of the data source"""
        self._data_source.sig_data_update.connect(self._handle_data_update_signal)

    def _disconnect_from_data_source(self):
        """Disconnect from all available signals of the data source"""
        self._data_source.sig_data_update.disconnect(self._handle_data_update_signal)

    def get_data_source(self):
        """Getter for the attached data source"""
        return self._data_source

    def get_full_data_buffer(self) -> Tuple[np.ndarray, ...]:
        """ Get the data buffers values

        Return the full inner data as a tuple containing numpy arrays.
        How many numpy arrays are included is depending on the type of
        the data buffer, see implementation (primary_values and all secondary
        values)
        """
        return self._full_data_buffer.as_np_array()

    def get_smallest_distance_between_x_values(self):
        """Get the smallest distance between two x values in the buffer"""
        return self._full_data_buffer.smallest_distance_between_primary_values

    def is_empty(self):
        """Check if the buffer has any values in it"""
        return self._full_data_buffer.is_empty()

    def get_data_buffer_size(self):
        """Get the number of entries the data buffer can hold at max"""
        return self._full_data_buffer.full_size

    def get_highest_primary_value(self) -> Optional[float]:
        """Return the highest x value available in the buffer that is not nan"""
        primary_values = self.get_full_data_buffer()[0]
        if primary_values.size == 0:
            return None
        i = primary_values.size - 1
        while i >= 0 and np.isnan(primary_values[i]):
            i -= 1
        if np.isnan(primary_values[i]):
            return None
        return primary_values[i]

    def get_subset(self, start: float, end: float):
        """ Get Subset of a specific start and end

        Return a subset of the curve whose x values fulfill the condition start <= x <= end.
        The subset will only contain points from the original data and won't be clipped
        at start and end. This means that there might be gaps between boundaries and the
        first and last points.
        """
        return self._full_data_buffer.get_subset(start=start, end=end)

    # ~~~~~ Mandatory to implement ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @abc.abstractmethod
    @Slot(PointData)
    @Slot(CurveData)
    @Slot(BarData)
    @Slot(BarCollectionData)
    @Slot(InjectionBarData)
    @Slot(InjectionBarData)
    @Slot(InjectionBarCollectionData)
    @Slot(TimestampMarkerData)
    @Slot(TimestampMarkerCollectionData)
    def _handle_data_update_signal(self, data):
        """Handle arriving data"""
        pass


class CurveDataModel(BaseDataModel):

    """DataModel for a live line graph"""

    def __init__(self, data_source: UpdateSource, buffer_size: Optional[int] = DEFAULT_BUFFER_SIZE):
        """Create a new curve data model connected to a data-source"""
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedCurveDataBuffer = SortedCurveDataBuffer(size=buffer_size)

    def get_clipped_subset(self, start: float, end: float) -> Tuple[np.ndarray, np.ndarray]:
        """ Get a subset of the models data """
        return self._full_data_buffer.get_subset(start, end, clip_at_boundaries=True)

    @Slot(PointData)
    @Slot(CurveData)
    def _handle_data_update_signal(self, data: Union[PointData, CurveData]) -> None:
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, PointData) and data.is_valid():
            self._full_data_buffer.add_entry(
                x_value=data.x_value,
                y_value=data.y_value
            )
            self.sig_model_has_changed.emit()
        elif isinstance(data, CurveData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x_values=data.x_values,
                y_values=data.y_values
            )
            self.sig_model_has_changed.emit()
        else:
            if not self._non_fitting_data_info_printed:
                _LOGGER.warning(f"Data {data} of type {type(data).__name__} does not fit this "
                                f"line graph datamodel or is invalid and will be ignored.")
                self._non_fitting_data_info_printed = True


class BarGraphDataModel(BaseDataModel):

    """
    DataModel for a live bar graph
    """

    def __init__(self, data_source: UpdateSource, buffer_size: Optional[int] = None):
        """Create a new bar graph data model connected to a data-source"""
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedBarGraphDataBuffer = SortedBarGraphDataBuffer(size=buffer_size)

    def _get_min_distance_between_bars(self) -> float:
        """ Get the minimum distance between two bars

        Get the minimum distance between two bars. This can be helpful
        for setting the width of the bars so they would not touch each other.
        """
        return self._full_data_buffer.smallest_distance_between_primary_values

    @Slot(BarData)
    @Slot(BarCollectionData)
    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]):
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, BarData) and data.is_valid():
            self._full_data_buffer.add_entry(
                x_value=data.x_value, y_value=data.y_value, height=data.height
            )
            self.sig_model_has_changed.emit()
        elif isinstance(data, BarCollectionData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x_values=data.x_values,
                y_values=data.y_values,
                height=data.heights,
            )
            self.sig_model_has_changed.emit()
        else:
            if not self._non_fitting_data_info_printed:
                _LOGGER.warning(f"Data {data} of type {type(data).__name__} does not "
                                f"fit this bar graph datamodel or is invalid and will be ignored.")
                self._non_fitting_data_info_printed = True


class InjectionBarDataModel(BaseDataModel):

    """
    DataModel for a live injection bar graph
    """

    def __init__(self, data_source: UpdateSource, buffer_size: Optional[int] = None):
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedInjectionBarsDataBuffer = SortedInjectionBarsDataBuffer(size=buffer_size)

    @Slot(InjectionBarData)
    @Slot(InjectionBarData)
    def _handle_data_update_signal(self, data: Union[InjectionBarData, InjectionBarCollectionData]):
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, InjectionBarData) and data.is_valid():
            self._full_data_buffer.add_entry(
                x_value=data.x_value,
                y_value=data.y_value,
                height=data.height,
                width=data.width,
                label=data.label,
            )
            self.sig_model_has_changed.emit()
        elif isinstance(data, InjectionBarCollectionData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x_values=data.x_values,
                y_values=data.y_values,
                heights=data.heights,
                widths=data.widths,
                labels=data.labels,
            )
            self.sig_model_has_changed.emit()
        else:
            if not self._non_fitting_data_info_printed:
                _LOGGER.warning(f"Data {data} of type {type(data).__name__} does not fit "
                                f"this injection-bar datamodel or is invalid and will be ignored.")
                self._non_fitting_data_info_printed = True


class TimestampMarkerDataModel(BaseDataModel):

    """DataModel for a live Vertical Infinite Lines marking timestamps (f.e. for marking special timestamps)"""

    def __init__(self, data_source: UpdateSource, buffer_size: Optional[int] = None):
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedTimestampMarkerDataBuffer = SortedTimestampMarkerDataBuffer(size=buffer_size)

    @Slot(TimestampMarkerData)
    @Slot(TimestampMarkerCollectionData)
    def _handle_data_update_signal(self, data: Union[TimestampMarkerData, TimestampMarkerCollectionData]):
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, TimestampMarkerData) and data.is_valid():
            self._full_data_buffer.add_entry(
                x_value=data.x_value, color=data.color, label=data.label
            )
            self.sig_model_has_changed.emit()
        elif isinstance(data, TimestampMarkerCollectionData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x_values=data.x_values,
                colors=data.colors,
                labels=data.labels,
            )
            self.sig_model_has_changed.emit()
        else:
            if not self._non_fitting_data_info_printed:
                _LOGGER.warning(f"Data {data} of type {type(data).__name__} does not fit "
                                f"this timestamp mark datamodel or is invalid and will be ignored.")
                self._non_fitting_data_info_printed = True
