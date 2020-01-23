"""Module for signal based updates for the graph and implementation"""

from typing import Optional, Callable, cast, Type, Sequence, Union, Any
from datetime import datetime
import numpy as np

from qtpy.QtCore import QObject, Signal
from accwidgets.graph.datamodel.datastructures import (
    DEFAULT_COLOR,
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


class UpdateSource(QObject):

    """
    Update Source is the connection between the actual source where the data
    comes from which we want to display without being dependent on where the
    data comes from. This is achieved by defining signals that can be used to
    publish any changes related to the displayed data. These signals can then
    be connected to slots, that handle to the change in the data. When using
    f.e. addCurve on the ExPlotWidget, this connection will automatically be
    set up when passing an instance of this class.

    Additionally the update source can be used to publish other updates to a
    plot, f.e. timestamps that are used by the plot as the current time.
    """

    # TODO: Range Change Signal not used yet.
    #       Change dict to fitting type when integrated.
    # sig_new_time_span = Signal(dict)
    sig_new_timestamp = Signal(float)
    sig_new_data = Signal(
        [PointData],
        [CurveData],
        [BarData],
        [BarCollectionData],
        [InjectionBarData],
        [InjectionBarCollectionData],
        [TimestampMarkerData],
        [TimestampMarkerCollectionData],
    )


class SignalBoundDataSource(UpdateSource):

    def __init__(
            self,
            sig: Signal,
            data_type: Optional[Type[PlottingItemData]] = None,
            transformation: Optional[
                Callable[[Sequence[Union[float, str]]], PlottingItemData]
            ] = None,
    ):
        """
        Convenience class for creating Update Sources for a signal
        for a specific data-type. The idea is, that this update source
        attaches to a passed signal, transforms the data either through
        a default transformation or a passed transformation function and
        emit the resulting data to a data visualization item (curve,
        bar graph etc...).

        More details about the default transformation functions can be seen
        in this classes _to_xyz() functions.

        Args:
            sig: Signal where the new value is coming from
            data_type: Data Type, which should be emitted by this data source
                       The data type can be None only if a transformation
                       function is given
            transformation: Optional Transformation function, which translates
        """
        super().__init__(parent=None)
        assert data_type is not None or transformation is not None
        self.data_type: Optional[Type[PlottingItemData]] = data_type
        self.transform: Callable = (transformation
                                    or PlottingItemDataFactory.get_transformation(self.data_type))
        sig.connect(self._emit_point)

    def _emit_point(self,
                    *args: Union[float, str, Sequence[float], Sequence[str]]):
        envelope = self.transform(*args)
        # In case a transformation function was given but no data type
        if self.data_type is None:
            self.data_type = cast(Type[PlottingItemData], type(envelope))
        self.sig_new_data[self.data_type].emit(envelope)


class PlottingItemDataFactory:

    """
    Class which offers factory methods for transforming f.e. simple float
    values into PlottingItemData data structures. To get the right
    transformation function by using the static method get_transformation().
    """

    @staticmethod
    def get_transformation(
            data_type: Optional[Type[PlottingItemData]],
    ) -> Callable[[], PlottingItemData]:
        """
        Try to transform the given *args to the desired data structure.
        This allows easier transformation between raw values coming from
        the signal and a data structure which can be interpreted by the
        graphs.

        Raises:
            IndexError: Not enough arguments were passed for the data type.
        """
        if data_type is not None:
            if issubclass(data_type, PointData):
                return PlottingItemDataFactory._to_point
            if issubclass(data_type, BarData):
                return PlottingItemDataFactory._to_bar
            if issubclass(data_type, InjectionBarData):
                return PlottingItemDataFactory._to_injection_bar
            if issubclass(data_type, TimestampMarkerData):
                return PlottingItemDataFactory._to_ts_marker
            if issubclass(data_type, CurveData):
                return PlottingItemDataFactory._to_curve
            if issubclass(data_type, BarCollectionData):
                return PlottingItemDataFactory._to_bar_collection
            if issubclass(data_type, InjectionBarCollectionData):
                return PlottingItemDataFactory._to_injection_bar_collection
            if issubclass(data_type, TimestampMarkerCollectionData):
                return PlottingItemDataFactory._to_ts_marker_collection
        raise TypeError("No default transformation function could be found"
                        f"for data type '{data_type}'")

    @staticmethod
    def _to_point(*args: float) -> PointData:
        args = PlottingItemDataFactory._unwrapped(*args)
        return PointData(
            x=PlottingItemDataFactory._or_now(index=1,
                                              args=args),
            y=args[0],  # mandatory
        )

    @staticmethod
    def _to_bar(*args: float) -> BarData:
        args = PlottingItemDataFactory._unwrapped(*args)
        return BarData(
            x=PlottingItemDataFactory._or_now(index=2,
                                              args=args),
            y=PlottingItemDataFactory._or(index=1,
                                          args=args,
                                          default=0),
            height=args[0],  # mandatory
        )

    @staticmethod
    def _to_injection_bar(*args: Union[float, str]) -> InjectionBarData:
        """
        **Attention**: String parameters will automatically set as label,
        no matter where they are positioned.
        """
        arguments = PlottingItemDataFactory._unwrapped(*args)
        label = ""
        str_param = [i for i in arguments if isinstance(i, str)]
        if str_param:
            label = str_param[0]
            arguments.remove(label)
        return InjectionBarData(
            x=PlottingItemDataFactory._or_now(index=3,
                                              args=arguments),
            y=PlottingItemDataFactory._or(index=1,
                                          args=arguments,
                                          default=np.nan),
            width=PlottingItemDataFactory._or(index=2,
                                              args=arguments,
                                              default=np.nan),
            height=arguments[0],  # mandatory
            label=label,
        )

    @staticmethod
    def _to_ts_marker(*args: Union[float, str]) -> TimestampMarkerData:
        args = PlottingItemDataFactory._unwrapped(*args)
        return TimestampMarkerData(
            x=PlottingItemDataFactory._or_now(index=0,
                                              args=args),
            color=PlottingItemDataFactory._or(index=2,
                                              args=args,
                                              default=DEFAULT_COLOR),
            label=PlottingItemDataFactory._or(index=1,
                                              args=args,
                                              default=""),
        )

    @staticmethod
    def _to_curve(*args: Sequence[float]) -> CurveData:
        args = PlottingItemDataFactory._collection_unwrapped(*args)
        return CurveData(
            x=PlottingItemDataFactory._or_num_range(index=1,
                                                    args=args),
            y=args[0],
        )

    @staticmethod
    def _to_bar_collection(*args: Sequence[float]) -> BarCollectionData:
        args = PlottingItemDataFactory._collection_unwrapped(*args)
        return BarCollectionData(
            x=PlottingItemDataFactory._or_num_range(index=2,
                                                    args=args),
            y=PlottingItemDataFactory._or_array(index=1,
                                                args=args,
                                                default=0),
            heights=args[0],
        )

    @staticmethod
    def _to_injection_bar_collection(
            *args: Sequence[Union[float, str]],
    ) -> InjectionBarCollectionData:
        arguments = PlottingItemDataFactory._collection_unwrapped(*args)
        label = np.zeros(len(arguments[0]), str)
        string_params = [i for i in arguments
                         if not any((not isinstance(j, str) for j in i))]
        if string_params:
            label = string_params[0]
            arguments.remove(label)
        return InjectionBarCollectionData(
            x=PlottingItemDataFactory._or_num_range(index=3,
                                                    args=arguments),
            y=PlottingItemDataFactory._or_array(index=1,
                                                args=arguments,
                                                default=np.nan),
            heights=arguments[0],  # mandatory
            widths=PlottingItemDataFactory._or_array(index=2,
                                                     args=arguments,
                                                     default=np.nan),
            labels=label,
        )

    @staticmethod
    def _to_ts_marker_collection(
            *args: Sequence[Union[float, str]],
    ) -> TimestampMarkerCollectionData:
        args = PlottingItemDataFactory._collection_unwrapped(*args)
        return TimestampMarkerCollectionData(
            x=cast(Sequence[float], args[0]),  # mandatory
            colors=PlottingItemDataFactory._or_array(index=2,
                                                     args=args,
                                                     default=DEFAULT_COLOR),
            labels=PlottingItemDataFactory._or_array(index=1,
                                                     args=args,
                                                     default=""),
        )

    # Index or Default Argument Functions

    @staticmethod
    def _or_now(index: int,
                args: Sequence[Union[str, float]]) -> float:
        """Either the value at the given index or the current time's
        time stamp."""
        return PlottingItemDataFactory._or(index,
                                           args,
                                           datetime.now().timestamp())

    @staticmethod
    def _or_num_range(index: int,
                      args: Sequence[Sequence[float]]) -> Sequence[float]:
        """Either the value at the given index or a range from 0 to the length
        as one of the entries in args."""
        return PlottingItemDataFactory._or(index,
                                           args,
                                           np.arange(0, len(args[0])))

    @staticmethod
    def _or_array(index: int, args: Sequence[Any], default: Any) -> Any:
        """Return either the value in args at the given index or and array made
        from the passed default value (same length as other args entries)."""
        try:
            return args[index]
        except IndexError:
            return np.array([default for _ in range(len(args[0]))])

    @staticmethod
    def _or(index: int, args: Sequence[Any], default: Any) -> Any:
        """Return either the value in args at the given index or the passed
        default value."""
        try:
            return args[index]
        except IndexError:
            if isinstance(default, float) and np.isnan(default):
                print(index)
                print(args)
                print(default)
            return default

    @staticmethod
    def _unwrapped(*args):
        if len(args) == 1 and isinstance(args[0], (Sequence, np.ndarray)):
            return list(args[0])
        return list(args)

    @staticmethod
    def _collection_unwrapped(*args):
        if (
                len(args) == 1
                and isinstance(args[0], (Sequence, np.ndarray))
                and isinstance(args[0][0], (Sequence, np.ndarray))
        ):
            return list(args[0])
        return list(args)
