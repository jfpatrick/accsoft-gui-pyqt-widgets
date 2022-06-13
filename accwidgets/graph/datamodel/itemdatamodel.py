"""
Data models are managing information presented by views. Each view (e.g. a live plotted curve)
is associated with a specific data model type, which is created when initializing the view.
The model is responsible for:

* Storing data
* Notifying the view about updates via PyQt signals
"""

import abc
import warnings
import numpy as np
from typing import Optional, Tuple, Union, cast
from qtpy.QtCore import QObject, Signal, Slot

from accwidgets.qt import AbstractQObjectMeta
from accwidgets.graph import (UpdateSource, DEFAULT_BUFFER_SIZE, SortedBarGraphDataBuffer, SortedCurveDataBuffer,
                              BaseSortedDataBuffer, SortedTimestampMarkerDataBuffer, SortedInjectionBarsDataBuffer,
                              BarCollectionData, BarData, CurveData, TimestampMarkerCollectionData, TimestampMarkerData,
                              InjectionBarCollectionData, InjectionBarData, PointData, PlottingItemData)
from .history import History


class AbstractBaseDataModel(QObject, metaclass=AbstractQObjectMeta):

    sig_data_model_changed = Signal()
    """
    General purpose signal informing that any changed happened to the data
    stored by the data model. This signal is triggered when the data is
    changed in direction from the :class:`UpdateSource` to the view,
    but not in the opposite one.

    :type: pyqtSignal
    """

    # TODO: Does it need to be in the superclass. Sounds like it is for editing only.
    sig_data_model_edited = Signal([CurveData])
    """
    Signal informing that the data model was edited from the view.

    :type: pyqtSignal
    """

    def __init__(self, data_source: UpdateSource, **_):
        """
        Base class for all data models.

        It exposes signals and slots to be connected to the :class:`UpdateSource`
        subclasses and views.

        Connections between the data model and the view must be initialized by the
        view itself. In contrast, connections to the :class:`UpdateSource` are
        made automatically when initializing the data model or replacing the update
        source in the existing data model.

        Args:
            data_source: Source for data updates that this model should be attached to.
        """
        super().__init__()
        self._data_source = data_source
        self._connect_to_data_source()

    # TODO: Does it need to be in the superclass. Sounds like it is for editing only.
    @abc.abstractmethod
    @Slot(CurveData)
    def handle_editing(self, data: CurveData):
        """Slot for receiving data updates performed in the view."""
        pass

    def replace_data_source(self, data_source: UpdateSource):
        """
        Replace associated data source, removing connections from the old one and
        creating new connections with the passed object.

        Override this method if replacing a data source must trigger the purge of
        all buffered data.

        Args:
            data_source: New source that model should be associated with.
        """
        self._disconnect_from_data_source()
        self._data_source = data_source
        self._connect_to_data_source()

    @property
    def data_source(self) -> UpdateSource:
        """Source for data updates that this data model is attached to."""
        return self._data_source

    @property
    @abc.abstractmethod
    def full_data_buffer(self) -> Tuple[np.ndarray, ...]:
        """
        Return the all data stored in the internal buffer.

        The return type depends on the concrete subclass implementation.
        """
        pass

    def _connect_to_data_source(self):
        """
        Build the connection between the data model and the update source by wiring
        all update signals to the fitting handler slots in both ways.
        """
        self._data_source.sig_new_data.connect(self._handle_data_update_signal)
        self.sig_data_model_edited.connect(self._data_source.handle_data_model_edit)

    def _disconnect_from_data_source(self):
        """
        Disconnect all wiring between the update source and the data model. After
        calling, none of both will receive any updates from the other anymore.
        """
        self._data_source.sig_new_data.disconnect(self._handle_data_update_signal)
        self.sig_data_model_edited.disconnect(self._data_source.handle_data_model_edit)

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
    def _handle_data_update_signal(self, data: PlottingItemData):
        """Handle arriving data"""
        pass


class AbstractLiveDataModel(AbstractBaseDataModel, metaclass=abc.ABCMeta):

    def __init__(self, data_source: UpdateSource, buffer_size: int = DEFAULT_BUFFER_SIZE):
        """
        Base class for all live plotting data models.

        Such models are built on top of a sorted buffer (see :class:`BaseSortedDataBuffer`),
        which is optimized for fast storage of the newly arriving data.

        Args:
            data_source: Source for data updates that this model should be attached to.
            buffer_size: Amount of entries that the buffer can hold (not necessarily equal
                         the amount of visible entries).
        """
        super().__init__(data_source=data_source)
        self._buffer_size = buffer_size
        self._full_data_buffer: BaseSortedDataBuffer
        self.non_fitting_data_info_printed: bool = False

    def replace_data_source(self, data_source: UpdateSource, clear_buffer: bool = True):
        """
        Replace associated data source, removing connections from the old one and
        creating new connections with the passed object.

        Args:
            data_source: New source that model should be associated with.
            clear_buffer: Purge of all buffered data.
        """
        super().replace_data_source(data_source=data_source)
        if clear_buffer:
            self._full_data_buffer.reset()

    def subset_for_xrange(self, start: float, end: float) -> Tuple[np.ndarray, ...]:
        """
        Get slice of data, where x-values lie in range between start and end (including).
        This subset is not interpolated on the edges, meaning there might be gaps between
        range boundaries and the first and last data samples.

        Args:
            start: Lower boundary on the x-axis.
            end: Upper boundary on the x-axis.

        Returns:
            Tuple of slices in the form *(x-values, corresponding specific data arrays...)*,
            where amount of slices depends on the dimensions of the secondary array.
        """
        return self._full_data_buffer.subset_for_primary_val_range(start=start, end=end)

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, ...]:
        """
        Return the data saved in the data model as a tuple of :class:`numpy.array`.
        The amount of returned arrays depends on the data model implementation.
        """
        return self._full_data_buffer.as_np_array()

    @property
    def min_dx(self) -> float:
        """Smallest distance between two x-values in the data model's buffer."""
        return self._full_data_buffer.min_dx

    @property
    def is_empty(self) -> bool:
        """Check if the model's buffer is empty."""
        return self._full_data_buffer.is_empty

    @property
    def buffer_size(self) -> int:
        """Maximum entry count that model's buffer can hold."""
        return self._full_data_buffer.capacity

    @property
    def max_primary_val(self) -> Optional[float]:
        """Largest x-value available in the buffer that is not :obj:`~numpy.nan`."""
        primary_values = self.full_data_buffer[0]
        if primary_values.size == 0:
            return None
        i = primary_values.size - 1
        while i >= 0 and np.isnan(primary_values[i]):
            i -= 1
        if np.isnan(primary_values[i]):
            return None
        return primary_values[i]

    @Slot(CurveData)
    def handle_editing(self, data: CurveData):
        """This is an empty implementation, as editing is irrelevant in the live plotting model"""
        # TODO: See the comment in the base class. When it's removed, this implementation is not needed.
        pass


class LiveCurveDataModel(AbstractLiveDataModel):

    def __init__(self, data_source: UpdateSource, buffer_size: int = DEFAULT_BUFFER_SIZE):
        """
        Data model tailored for live line graphs.

        Args:
            data_source: Source for data updates that this model should be attached to.
            buffer_size: Amount of entries that the buffer can hold (not necessarily equal
                         the amount of visible entries).
        """
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedCurveDataBuffer = SortedCurveDataBuffer(size=buffer_size)

    def subset_for_xrange(self, start: float, end: float, interpolated: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get slice of data, where x-values lie in range between start and end (including).
        The interpolated points are imaginary points on both edges of the subset that are lying on the requested
        range boundaries, (for cases, when boundaries do not directly coincide with real data points in the buffer).

        Args:
            start: Lower boundary on the x-axis.
            end: Upper boundary on the x-axis.
            interpolated: Interpolate the curve at the edges, creating an imaginary point on each end
                          (for purposes, when range does not coincide with points directly).

        Returns:
            Tuple of x-values and y-values subsets.
        """
        return self._full_data_buffer.subset_for_primary_val_range(start, end, interpolated=interpolated)

    @Slot(PointData)
    @Slot(CurveData)
    def _handle_data_update_signal(self, data: Union[PointData, CurveData]):
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, PointData) and data.is_valid():
            self._full_data_buffer.add_entry(
                x=data.x,
                y=data.y,
            )
            self.sig_data_model_changed.emit()
        elif isinstance(data, CurveData) and np.all(data.is_valid()):
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
        """
        Data model tailored for live bar graphs.

        Args:
            data_source: Source for data updates that this model should be attached to.
            buffer_size: Amount of entries that the buffer can hold (not necessarily equal
                         the amount of visible entries).
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
    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]):
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, BarData) and data.is_valid():
            self._full_data_buffer.add_entry(x=data.x, y=data.y, height=data.height)
            self.sig_data_model_changed.emit()
        elif isinstance(data, BarCollectionData) and np.all(data.is_valid()):
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
        """
        Data model tailored for live injection bar graphs.

        Args:
            data_source: Source for data updates that this model should be attached to.
            buffer_size: Amount of entries that the buffer can hold (not necessarily equal
                         the amount of visible entries).
        """
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
                x=data.x,
                y=data.y,
                height=data.height,
                width=data.width,
                label=data.label,
            )
            self.sig_data_model_changed.emit()
        elif isinstance(data, InjectionBarCollectionData) and np.all(data.is_valid()):
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
        Data model tailored for live timestamp markers.

        Args:
            data_source: Source for data updates that this model should be attached to.
            buffer_size: Amount of entries that the buffer can hold (not necessarily equal
                         the amount of visible entries).
        """
        super().__init__(data_source=data_source, buffer_size=buffer_size)
        self._full_data_buffer: SortedTimestampMarkerDataBuffer = SortedTimestampMarkerDataBuffer(size=buffer_size)

    @Slot(TimestampMarkerData)
    @Slot(TimestampMarkerCollectionData)
    def _handle_data_update_signal(self, data: Union[TimestampMarkerData, TimestampMarkerCollectionData]):
        """Handle data emitted by the data source.

        Data that does not have the right type will just be ignored.
        This allows attaching the same source to multiple datamodels"""
        if isinstance(data, TimestampMarkerData) and data.is_valid():
            self._full_data_buffer.add_entry(x=data.x, color=data.color, label=data.label)
            self.sig_data_model_changed.emit()
        elif isinstance(data, TimestampMarkerCollectionData) and np.all(data.is_valid()):
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
        Data model tailored for static line graphs. Contrary to "live" curves,
        new data fully overwrites the existing one, instead of appending to it.

        Args:
            data_source: Source for data updates that this model should be attached to.
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._y_values: np.ndarray = np.array([])

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return the all data stored in the internal buffer as a tuple of x-values and y-values.
        """
        return self._x_values, self._y_values

    @Slot(CurveData)
    def handle_editing(self, data: CurveData):
        """This is an empty implementation, as editing is irrelevant in the live plotting model"""
        # TODO: See the comment in the base class. When it's removed, this implementation is not needed.
        pass

    def _set_data(self, data: Union[PointData, CurveData]) -> bool:
        if isinstance(data, PointData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._y_values = np.array([data.y])
            return True
        elif isinstance(data, CurveData) and np.all(data.is_valid()):
            self._x_values = data.x
            self._y_values = data.y
            return True
        if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
            warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                          f"line graph data model or is invalid and will be ignored.")
            cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True
        return False

    def _handle_data_update_signal(self, data: CurveData):
        if self._set_data(data=data):
            self.sig_data_model_changed.emit()


class StaticBarGraphDataModel(AbstractBaseDataModel):

    def __init__(self, data_source: UpdateSource, **_):
        """
        Data model tailored for static bar graphs. Contrary to "live" graphs,
        new data fully overwrites the existing one, instead of appending to it.

        Args:
            data_source: Source for data updates that this model should be attached to.
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._y_values: np.ndarray = np.array([])
        self._heights: np.ndarray = np.array([])

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Return the all data stored in the internal buffer as a tuple of x-values, y-values and heights.
        """
        return self._x_values, self._y_values, self._heights

    @Slot(CurveData)
    def handle_editing(self, data: CurveData):
        """This is an empty implementation, as editing is irrelevant in the live plotting model"""
        # TODO: See the comment in the base class. When it's removed, this implementation is not needed.
        pass

    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]):
        if isinstance(data, BarData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._y_values = np.array([data.y])
            self._heights = np.array([data.height])
            self.sig_data_model_changed.emit()
        elif isinstance(data, BarCollectionData) and np.all(data.is_valid()):
            self._x_values = data.x
            self._y_values = data.y
            self._heights = data.heights
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                              f"bar graph datamodel or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True


class StaticInjectionBarDataModel(AbstractBaseDataModel):

    def __init__(self, data_source: UpdateSource, **_):
        """
        Data model tailored for static injection bar graphs. Contrary to "live" graphs,
        new data fully overwrites the existing one, instead of appending to it.

        Args:
            data_source: Source for data updates that this model should be attached to.
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._y_values: np.ndarray = np.array([])
        self._heights: np.ndarray = np.array([])
        self._widths: np.ndarray = np.array([])
        self._labels: np.ndarray = np.array([])

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Return the all data stored in the internal buffer as a tuple of x-values, y-values, heights, widths and labels.
        """
        return self._x_values, self._y_values, self._heights, self._widths, self._labels

    @Slot(CurveData)
    def handle_editing(self, data: CurveData):
        """This is an empty implementation, as editing is irrelevant in the live plotting model"""
        # TODO: See the comment in the base class. When it's removed, this implementation is not needed.
        pass

    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]):
        if isinstance(data, InjectionBarData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._y_values = np.array([data.y])
            self._heights = np.array([data.height])
            self._widths = np.array([data.width])
            self._labels = np.array([data.label])
            self.sig_data_model_changed.emit()
        elif isinstance(data, InjectionBarCollectionData) and np.all(data.is_valid()):
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


class StaticTimestampMarkerDataModel(AbstractBaseDataModel):

    def __init__(self, data_source: UpdateSource, **_):
        """
        Data model tailored for static timestamp markers. Contrary to "live" markers,
        new data fully overwrites the existing one, instead of appending to it.

        Args:
            data_source: Source for data updates that this model should be attached to.
        """
        super().__init__(data_source=data_source)
        self._x_values: np.ndarray = np.array([])
        self._colors: np.ndarray = np.array([])
        self._labels: np.ndarray = np.array([])

    @property
    def full_data_buffer(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Return the all data stored in the internal buffer as a tuple of x-values and colors and labels.
        """
        return self._x_values, self._colors, self._labels

    @Slot(CurveData)
    def handle_editing(self, data: CurveData):
        """This is an empty implementation, as editing is irrelevant in the live plotting model"""
        # TODO: See the comment in the base class. When it's removed, this implementation is not needed.
        pass

    def _handle_data_update_signal(self, data: Union[BarData, BarCollectionData]):
        if isinstance(data, TimestampMarkerData) and data.is_valid():
            self._x_values = np.array([data.x])
            self._colors = np.array([data.color])
            self._labels = np.array([data.label])
            self.sig_data_model_changed.emit()
        elif isinstance(data, TimestampMarkerCollectionData) and np.all(data.is_valid()):
            self._x_values = data.x
            self._colors = data.colors
            self._labels = data.labels
            self.sig_data_model_changed.emit()
        else:
            if not cast(AbstractLiveDataModel, self).non_fitting_data_info_printed:
                warnings.warn(f"Data {data} of type {type(data).__name__} does not fit this "
                              f"timestamp marker data model or is invalid and will be ignored.")
                cast(AbstractLiveDataModel, self).non_fitting_data_info_printed = True


class EditableCurveDataModel(StaticCurveDataModel):

    def __init__(self, data_source: UpdateSource, **kwargs):
        """
        Model for editing static curves by interactively dragging points.

        Args:
            data_source: Access point for data updates that this model should be attached to.
            **kwargs: Any keyword arguments from :class:`StaticCurveDataModel`.
        """
        StaticCurveDataModel.__init__(self, data_source=data_source, **kwargs)
        self._history = History[CurveData]()

    @Slot(CurveData)
    def handle_editing(self, data: CurveData):
        """
        Slot that receives a change from view during interactive editing. Changes are
        registered in the data model but are not yet committed to propagate into the
        :attr:`~EditableCurveDataModel.data_source`.
        """
        if self._set_data(data=data):
            self._history.save_state(data)
        self.sig_data_model_changed.emit()

    def replace_selection(self, indices: np.ndarray, replacement: CurveData):
        """
        Replace the existing data residing at the given indices with the replacement values.
        The replacements will be sorted in by their x-values. Lengths of ``indices`` and
        ``replacement`` are allowed to be different.

        Args:
            indices: Positions that should be replaced with new values.
            replacement: Replacement values.
        """
        self._x_values = np.delete(self._x_values, indices)
        self._y_values = np.delete(self._y_values, indices)
        indices = np.searchsorted(self._x_values, replacement.x)
        if not np.can_cast(replacement.x.dtype, self._x_values.dtype):
            self._x_values = self._x_values.astype(replacement.x.dtype)
        if not np.can_cast(replacement.y.dtype, self._y_values.dtype):
            self._y_values = self._y_values.astype(replacement.y.dtype)
        self._x_values = np.insert(self._x_values, indices, replacement.x)
        self._y_values = np.insert(self._y_values, indices, replacement.y)
        self.sig_data_model_changed.emit()
        self._history.save_state(CurveData(self._x_values,
                                           self._y_values,
                                           check_validity=False))

    def send_current_state(self) -> bool:
        """
        Commit performed changes into the :attr:`~EditableCurveDataModel.data_source`.

        Returns:
            Whether change was successfully committed.
        """
        if self.sendable_state_exists:
            sendable_state = self._history.current_state
            if sendable_state is not None:
                self.sig_data_model_edited.emit(sendable_state)
                return True
        return False

    @property
    def sendable_state_exists(self) -> bool:
        """
        Check whether there are any changes that can be committed into the :attr:`~EditableCurveDataModel.data_source`.
        """
        return self._history.current_state is not None

    @property
    def undoable(self) -> bool:
        """Check whether there is an older state that can be rolled back to."""
        return self._history.undoable

    @property
    def redoable(self) -> bool:
        """Check whether there is a newer state that can be transitioned to."""
        return self._history.redoable

    def undo(self) -> bool:
        """
        Roll back to the next older state.

        Returns:
            Undo was successful.
        """
        if self.undoable:
            state = self._history.undo()
            if isinstance(state, (PointData, CurveData)):
                self._set_data(data=state)
                self.sig_data_model_changed.emit()
                return True
            else:
                warnings.warn(f"State {state} can't be applied.")
                return False
        return False

    def redo(self) -> bool:
        """
        Transition to the next newer state.

        Returns:
            Redo was successful.
        """
        if self.redoable:
            state = self._history.redo()
            if isinstance(state, (PointData, CurveData)):
                self._set_data(data=state)
                self.sig_data_model_changed.emit()
                return True
            else:
                warnings.warn(f"State {state} can't be applied.")
                return False
        return False

    def _handle_data_update_signal(self, data: CurveData):
        """
        Extend the static data models update handler with appending the state
        to the local history.

        Args:
            data: data coming from the update source
        """
        super()._handle_data_update_signal(data)
        self._history.save_state(data)
