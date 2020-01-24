""" Data Model for one single curve. """

import abc
import warnings
from typing import Optional, Tuple, Union, cast

import numpy as np
from qtpy.QtCore import QObject, Signal, Slot

from accwidgets.graph.datamodel.connection import UpdateSource
from accwidgets.graph.datamodel.datamodelbuffer import (
    DEFAULT_BUFFER_SIZE,
    SortedBarGraphDataBuffer,
    SortedCurveDataBuffer,
    BaseSortedDataBuffer,
    SortedTimestampMarkerDataBuffer,
    SortedInjectionBarsDataBuffer,
)
from accwidgets.graph.datamodel.datastructures import (
    AbstractQObjectMeta,
    BarCollectionData,
    BarData,
    CurveData,
    TimestampMarkerCollectionData,
    TimestampMarkerData,
    InjectionBarCollectionData,
    InjectionBarData,
    PointData,
    PlottingItemData,
)


class WrongDataType(Warning):
    """
    Warning for an invalid Data Structure. PlottingItemData should emit
    this if they are invalid, which means that they can not be drawn
    in their fitting graph-type.
    """
    pass


class AbstractBaseDataModel(QObject, metaclass=AbstractQObjectMeta):

    sig_data_model_changed = Signal()
    """
    General purpose signal informing that any changed
    happened to the data stored by the data model
    """

    def __init__(self, data_source: UpdateSource, **_):
        """
        Abstract base class that defines signals and slots that all derived data
        models can use to publish and implement to react to data related changes.

        The handler slots offered by this class are connected to signals from the
        passed update source that can react to changes published from it. These
        handler slots can also be used by an item that allows altering the data model.
        This class also offers signals that others can connect to, to receive any
        information about changes in the data model. By default these are connected
        to the handler slots of the update source to publish changes in the datamodel
        back to the attached source. These signals can of course also be used by an
        item that wants to display changes happened in this data model.

        Connections from the datamodel to a view item have to be initialized by the
        view item itself. Connections to the update source are automatically
        initialized when creating the data model or replacing the update source
        through the fitting API.

        Args:
            data_source: source for data updates this data-model connects to.
            **_: Swallows unused keyword arguments
        """
        super().__init__()
        self._data_source = data_source
        self._connect_to_data_source()

    def replace_data_source(self, data_source: UpdateSource) -> None:
        """
        Disconnect the data model from the old data source and connect to a new
        one. If replacing the data source should lead to the deletion of all up
        to this point stored data, this has to be implemented by the derived class
        by overriding this function in the desired way.

        Args:
            data_source: New source the model should connect to.
        """
        self._disconnect_from_data_source()
        self._data_source = data_source
        self._connect_to_data_source()

    @property
    def data_source(self) -> UpdateSource:
        """Source for data updates the data-model is attached to."""
        return self._data_source

    @property
    @abc.abstractmethod
    def full_data_buffer(self) -> Tuple[np.ndarray, ...]:
        """
        Return the data saved in the data model as a tuple of numpy arrays.
        The count of numpy arrays are dependent on the type of data model.
        """
        pass

    def _connect_to_data_source(self) -> None:
        """
        Build the connection between the data model and the update source by wiring
        all update signals to the fitting handler slots in both ways.
        """
        self._data_source.sig_new_data.connect(self._handle_data_update_signal)

    def _disconnect_from_data_source(self) -> None:
        """
        Disconnect all wiring between the update source and the data model. After
        calling, none of both will receive any updates from the other anymore.
        """
        self._data_source.sig_new_data.disconnect(self._handle_data_update_signal)

    # ~~~~~ Mandatory to implement in non abstract derived classes ~~~~~~~~~~~~

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
    def _handle_data_update_signal(self, data: PlottingItemData) -> None:
        """Handle arriving data"""
        pass


class AbstractLiveDataModel(AbstractBaseDataModel, metaclass=abc.ABCMeta):

    def __init__(self, data_source: UpdateSource, buffer_size: int = DEFAULT_BUFFER_SIZE):
        """
        Abstract base class for any live plotting data models that are built on top
        of a sorted buffer that is optimized for fast storage of new arriving data.

        Args:
            data_source: source for data updates
            buffer_size: Amount of entries the buffer is holding (not equal the
                         amount of displayed entries)
        """
        super().__init__(data_source=data_source)
        self._buffer_size = buffer_size
        self._full_data_buffer: BaseSortedDataBuffer
        self.non_fitting_data_info_printed: bool = False

    def replace_data_source(self, data_source: UpdateSource, clear_buffer: bool = True):
        """
        Replace the current data source and clear the inner saved data if wanted

        Args:
            data_source: New source the model should connect to.
            clear_buffer: Should all up to this point accumulated points be deleted
        """
        super().replace_data_source(data_source=data_source)
        if clear_buffer:
            self._full_data_buffer.reset()

    def subset_for_xrange(self, start: float, end: float) -> Tuple[np.ndarray, ...]:
        """ Get Subset of a specific start and end

        Return a subset of the curve whose x values fulfill the condition start <= x <= end.
        The subset will only contain points from the original data and won't be clipped
        at start and end. This means that there might be gaps between boundaries and the
        first and last points.

        Args:
            start: No x value in the subset is smaller than start
            end: No x value in the subset is bigger than end

        Returns:
            View on a subset of the data in the given range
        """
        return self._full_data_buffer.subset_for_primary_val_range(start=start, end=end)

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, ...]:
        """
        Return the data saved in the data model as a tuple of numpy arrays.
        The count of numpy arrays are dependent on the type of data model.
        """
        return self._full_data_buffer.as_np_array()

    @property
    def min_dx(self) -> float:
        """The smallest distance between two x values in the buffer."""
        return self._full_data_buffer.min_dx

    @property
    def is_empty(self) -> bool:
        """Check if the buffer has any values in it"""
        return self._full_data_buffer.is_empty

    @property
    def buffer_size(self) -> int:
        """Number of entries the data buffer can hold at max."""
        return self._full_data_buffer.capacity

    @property
    def max_primary_val(self) -> Optional[float]:
        """Biggest x value available in the buffer that is not nan"""
        primary_values = self.full_data_buffer[0]
        if primary_values.size == 0:
            return None
        i = primary_values.size - 1
        while i >= 0 and np.isnan(primary_values[i]):
            i -= 1
        if np.isnan(primary_values[i]):
            return None
        return primary_values[i]


class LiveCurveDataModel(AbstractLiveDataModel):

    def __init__(self, data_source: UpdateSource, buffer_size: int = DEFAULT_BUFFER_SIZE):
        """DataModel for a live line graph

        Args:
            data_source: update source for data related updates
            buffer_size: Amount of entries the buffer is holding
                         (not equal the amount of displayed entries)
        """
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedCurveDataBuffer = SortedCurveDataBuffer(size=buffer_size)

    def subset_for_xrange(self, start: float, end: float, interpolated: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """ Get a subset of the data models data in a specific x range

        Since the data buffer keeps data sorted, the subset will be sorted as well.

        **Note:** This method returns a view on the original data, if the data is not interpolated.
        If the curve is interpolated, a copy of the data is returned, which contains the two interpolated
        points at the start and end.

        Args:
            start: No x value in the subset is smaller than start
            end: No x value in the subset is bigger than end
            interpolated: Should the subset be linearly interpolated at the start and end point?

        Returns:
            Subset of the data in the given range
        """
        return self._full_data_buffer.subset_for_primary_val_range(start, end, interpolated=interpolated)

    @Slot(PointData)
    @Slot(CurveData)
    def _handle_data_update_signal(self, data: Union[PointData, CurveData]) -> None:
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, PointData) and data.is_valid():
            self._full_data_buffer.add_entry(
                x=data.x,
                y=data.y,
            )
            self.sig_data_model_changed.emit()
        elif isinstance(data, CurveData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x=data.x,
                y=data.y,
            )
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                              f"{type(self).__name__} or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True


class LiveBarGraphDataModel(AbstractLiveDataModel):

    def __init__(self, data_source: UpdateSource, buffer_size: int = DEFAULT_BUFFER_SIZE):
        """ DataModel for a live bar graph.
        Args:
            data_source: update source for data related updates
            buffer_size: Amount of entries the buffer is holding
                         (not equal the amount of displayed entries)
        """
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedBarGraphDataBuffer = SortedBarGraphDataBuffer(size=buffer_size)

    def _get_min_distance_between_bars(self) -> float:
        """ Get the minimum distance between two bars

        Get the minimum distance between two bars. This can be helpful
        for setting the width of the bars so they would not touch each other.
        """
        return self._full_data_buffer.min_dx

    @Slot(BarData)
    @Slot(BarCollectionData)
    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]) -> None:
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, BarData) and data.is_valid():
            self._full_data_buffer.add_entry(x=data.x, y=data.y, height=data.height)
            self.sig_data_model_changed.emit()
        elif isinstance(data, BarCollectionData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x=data.x,
                y=data.y,
                heights=data.heights,
            )
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not "
                              f"fit this bar graph datamodel or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True


class LiveInjectionBarDataModel(AbstractLiveDataModel):

    def __init__(self, data_source: UpdateSource, buffer_size: int = DEFAULT_BUFFER_SIZE):
        """DataModel for a live injection bar graph

        Args:
            data_source: source for data updates
            buffer_size: Amount of entries the buffer is holding
                         (not equal the amount of displayed entries)
        """
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedInjectionBarsDataBuffer = SortedInjectionBarsDataBuffer(size=buffer_size)

    @Slot(InjectionBarData)
    @Slot(InjectionBarData)
    def _handle_data_update_signal(self, data: Union[InjectionBarData, InjectionBarCollectionData]) -> None:
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, InjectionBarData) and data.is_valid():
            self._full_data_buffer.add_entry(
                x=data.x,
                y=data.y,
                height=data.height,
                width=data.width,
                label=data.label,
            )
            self.sig_data_model_changed.emit()
        elif isinstance(data, InjectionBarCollectionData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x=data.x,
                y=data.y,
                heights=data.heights,
                widths=data.widths,
                labels=data.labels,
            )
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit "
                              f"this injection-bar datamodel or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True


class LiveTimestampMarkerDataModel(AbstractLiveDataModel):

    def __init__(self, data_source: UpdateSource, buffer_size: int = DEFAULT_BUFFER_SIZE):
        """
        DataModel for a live timestamp markers.

        Args:
            data_source: source for data updates
            buffer_size: Amount of entries the buffer is holding
                         (not equal the amount of displayed entries)
        """
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedTimestampMarkerDataBuffer = SortedTimestampMarkerDataBuffer(size=buffer_size)

    @Slot(TimestampMarkerData)
    @Slot(TimestampMarkerCollectionData)
    def _handle_data_update_signal(self, data: Union[TimestampMarkerData, TimestampMarkerCollectionData]) -> None:
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, TimestampMarkerData) and data.is_valid():
            self._full_data_buffer.add_entry(x=data.x, color=data.color, label=data.label)
            self.sig_data_model_changed.emit()
        elif isinstance(data, TimestampMarkerCollectionData) and np.alltrue(data.is_valid()):
            self._full_data_buffer.add_list_of_entries(
                x=data.x,
                colors=data.colors,
                labels=data.labels,
            )
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit "
                              f"this timestamp mark datamodel or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True


class StaticCurveDataModel(AbstractBaseDataModel):

    def __init__(self, data_source: UpdateSource, **_):
        """
        Data model for a static curve. If new data arrives, the
        old one will be replaced entirely with the new one.

        Args:
            data_source: Source for the new arriving data
            **_: Swallow unused keyword arguments
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._y_values: np.ndarray = np.array([])

    def _handle_data_update_signal(self, data: Union[PointData, CurveData]) -> None:
        if isinstance(data, PointData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._y_values = np.array([data.y])
            self.sig_data_model_changed.emit()
        elif isinstance(data, CurveData) and np.alltrue(data.is_valid()):
            self._x_values = data.x
            self._y_values = data.y
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                              f"line graph data model or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return the data saved in the data model as a tuple of numpy arrays
        in the form (x_values, y_values).
        """
        return self._x_values, self._y_values


class StaticBarGraphDataModel(AbstractBaseDataModel):

    def __init__(self, data_source: UpdateSource, **_):
        """
        Data model for a static bar graph. If new data arrives, the
        old one will be replaced.

        Args:
            data_source: Source for the new arriving data
            **_: Swallow unused keyword arguments
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._y_values: np.ndarray = np.array([])
        self._heights: np.ndarray = np.array([])

    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]) -> None:
        if isinstance(data, BarData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._y_values = np.array([data.y])
            self._heights = np.array([data.height])
            self.sig_data_model_changed.emit()
        elif isinstance(data, BarCollectionData) and np.alltrue(data.is_valid()):
            self._x_values = data.x
            self._y_values = data.y
            self._heights = data.heights
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                              f"bar graph datamodel or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Return the data saved in the data model as a tuple of numpy arrays
        in the form (x_values, y_values, height_values).
        """
        return self._x_values, self._y_values, self._heights


class StaticInjectionBarDataModel(AbstractBaseDataModel):

    def __init__(self, data_source: UpdateSource, **_):
        """
        Data model for a static injection bar graph. If new data arrives, the
        old one will be replaced.

        Args:
            data_source: Source for the new arriving data
            **_: Swallow unused keyword arguments
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._y_values: np.ndarray = np.array([])
        self._heights: np.ndarray = np.array([])
        self._widths: np.ndarray = np.array([])
        self._labels: np.ndarray = np.array([])

    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]) -> None:
        if isinstance(data, InjectionBarData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._y_values = np.array([data.y])
            self._heights = np.array([data.height])
            self._widths = np.array([data.width])
            self._labels = np.array([data.label])
            self.sig_data_model_changed.emit()
        elif isinstance(data, InjectionBarCollectionData) and np.alltrue(data.is_valid()):
            self._x_values = data.x
            self._y_values = data.y
            self._heights = data.heights
            self._widths = data.widths
            self._labels = data.labels
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                              f"injection bar data model or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Return the data saved in the data model as a tuple of numpy arrays
        in the form (x_values, y_values, height_values, width_values, labels).
        """
        return self._x_values, self._y_values, self._heights, self._widths, self._labels


class StaticTimestampMarkerDataModel(AbstractBaseDataModel):

    def __init__(self, data_source: UpdateSource, **_):
        """
        Data model for a static time stamp markers. If new data arrives, the
        old one will be replaced.

        Args:
            data_source: Source for the new arriving data
            **_: Swallow unused keyword arguments
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._colors: np.ndarray = np.array([])
        self._labels: np.ndarray = np.array([])

    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]) -> None:
        if isinstance(data, TimestampMarkerData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._colors = np.array([data.color])
            self._labels = np.array([data.label])
            self.sig_data_model_changed.emit()
        elif isinstance(data, TimestampMarkerCollectionData) and np.alltrue(data.is_valid()):
            self._x_values = data.x
            self._colors = data.colors
            self._labels = data.labels
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                              f"timestamp marker data model or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Return the data saved in the data model as a tuple of numpy arrays
        in the form (x_values, color_string_values, labels).
        """
        return self._x_values, self._colors, self._labels
