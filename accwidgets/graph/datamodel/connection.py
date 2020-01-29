"""Module for signal based updates for the graph and implementation"""

from typing import (
    Optional,
    Callable,
    cast,
    Type,
    Sequence,
    Union,
    Any,
    Tuple,
    List,
    Dict,
)
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
        data_type_specified = data_type is not None
        transform_specified = transformation is not None

        if data_type_specified == transform_specified:
            raise ValueError("You must specify either data_type or transformation")
        self.transform: Callable = (transformation
                                    or PlottingItemDataFactory.get_transformation(data_type))
        sig.connect(self._emit_point)

    def _emit_point(self,
                    *args: Union[float, str, Sequence[float], Sequence[str]]):
        transformed_data = self.transform(*args)
        self.sig_new_data[type(transformed_data)].emit(transformed_data)


class PlottingItemDataFactory:

    """
    Class which offers factory methods for transforming f.e. simple float
    values into PlottingItemData data structures. To get the right
    transformation function by using the static method get_transformation().
    """

    TIMESTAMP_HEADER_FIELD = "acqStamp"

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
    def _to_point(*args: float) -> PointData:  # last argument can be header dict
        arguments, timestamp = PlottingItemDataFactory._separate(*args)
        return PointData(
            x=PlottingItemDataFactory._or_now(index=1,
                                              args=arguments,
                                              acq_timestamp=timestamp),
            y=arguments[0],  # mandatory
        )

    @staticmethod
    def _to_bar(*args: float) -> BarData:  # last argument can be header dict
        arguments, timestamp = PlottingItemDataFactory._separate(*args)
        return BarData(
            x=PlottingItemDataFactory._or_now(index=2,
                                              args=arguments,
                                              acq_timestamp=timestamp),
            y=PlottingItemDataFactory._or(index=1,
                                          args=arguments,
                                          default=0),
            height=arguments[0],  # mandatory
        )

    @staticmethod
    def _to_injection_bar(
            *args: Union[float, str],
    ) -> InjectionBarData:  # last argument can be header dict
        """
        **Attention**: String parameters will automatically set as label,
        no matter where they are positioned.
        """
        arguments, timestamp = PlottingItemDataFactory._separate(*args)
        label = ""
        str_param = [i for i in arguments if isinstance(i, str)]
        if str_param:
            label = str_param[0]
            arguments.remove(label)
        return InjectionBarData(
            x=PlottingItemDataFactory._or_now(index=3,
                                              args=arguments,
                                              acq_timestamp=timestamp),
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
    def _to_ts_marker(
            *args: Union[float, str],
    ) -> TimestampMarkerData:  # last argument can be header dict
        arguments, timestamp = PlottingItemDataFactory._separate(*args)
        return TimestampMarkerData(
            x=PlottingItemDataFactory._or_now(index=0,
                                              args=arguments,
                                              acq_timestamp=timestamp),
            color=PlottingItemDataFactory._or(index=2,
                                              args=arguments,
                                              default=DEFAULT_COLOR),
            label=PlottingItemDataFactory._or(index=1,
                                              args=arguments,
                                              default=""),
        )

    @staticmethod
    def _to_curve(
        *args: Sequence[float],
    ) -> CurveData:  # last argument can be header dict
        arguments, _ = PlottingItemDataFactory._extract_header(list(args))
        return CurveData(
            x=PlottingItemDataFactory._or_num_range(index=1,
                                                    args=arguments),
            y=arguments[0],
        )

    @staticmethod
    def _to_bar_collection(
        *args: Sequence[float],
    ) -> BarCollectionData:  # last argument can be header dict
        arguments, _ = PlottingItemDataFactory._extract_header(list(args))
        return BarCollectionData(
            x=PlottingItemDataFactory._or_num_range(index=2,
                                                    args=arguments),
            y=PlottingItemDataFactory._or_array(index=1,
                                                args=arguments,
                                                default=0),
            heights=arguments[0],
        )

    @staticmethod
    def _to_injection_bar_collection(
            *args: Sequence[Union[float, str]],
    ) -> InjectionBarCollectionData:  # last argument can be header dict
        arguments, _ = PlottingItemDataFactory._extract_header(list(args))
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
    ) -> TimestampMarkerCollectionData:  # last argument can be header dict
        arguments, _ = PlottingItemDataFactory._extract_header(list(args))
        return TimestampMarkerCollectionData(
            x=cast(Sequence[float], arguments[0]),  # mandatory
            colors=PlottingItemDataFactory._or_array(index=2,
                                                     args=arguments,
                                                     default=DEFAULT_COLOR),
            labels=PlottingItemDataFactory._or_array(index=1,
                                                     args=arguments,
                                                     default=""),
        )

    # Index or Default Argument Functions

    @staticmethod
    def _or_now(index: int,
                args: List[Union[str, float]],
                acq_timestamp: Union[None, float]) -> float:
        """Either the value at the given index, the acquisition timestamp from
        the header or the current time's time stamp locally calculated.
        """
        default = acq_timestamp if acq_timestamp is not None else datetime.now().timestamp()
        return PlottingItemDataFactory._or(index, args, default)

    @staticmethod
    def _or_num_range(index: int,
                      args: List[Sequence[float]]) -> Sequence[float]:
        """Either the value at the given index or a range from 0 to the length
        as one of the entries in args."""
        return PlottingItemDataFactory._or(index,
                                           args,
                                           np.arange(0, len(args[0])))

    @staticmethod
    def _or_array(index: int, args: List[Any], default: Any) -> Any:
        """Return either the value in args at the given index or and array made
        from the passed default value (same length as other args entries)."""
        try:
            return args[index]
        except IndexError:
            return np.array([default for _ in range(len(args[0]))])

    @staticmethod
    def _or(index: int, args: List[Any], default: Any) -> Any:
        """Return either the value in args at the given index or the passed
        default value."""
        try:
            return args[index]
        except IndexError:
            return default

    @staticmethod
    def _separate(*args) -> Tuple[List[Union[float, str]], Optional[float]]:
        """Separate the header's timestamp from the arguments."""
        ts = None
        arguments, header = PlottingItemDataFactory._extract_header(
            list(args))
        if header:
            ts = PlottingItemDataFactory._extract_ts(header)
        return arguments, ts

    @staticmethod
    def _extract_header(args: List) -> Tuple[List, Optional[Dict]]:
        """Remove headers from the last position of the arguments if
        they are there."""
        header: Optional[Dict] = None
        if args and isinstance(args[-1], dict):
            header = args.pop(-1)
        return args, header

    @staticmethod
    def _extract_ts(header: Dict[str, Union[datetime, float]]) -> Optional[float]:
        """
        Extract the timestamp field from the header.
        """
        ts: Union[datetime, float, None] = None
        ts = header.get(PlottingItemDataFactory.TIMESTAMP_HEADER_FIELD)  # type: ignore
        try:
            ts = ts.timestamp()  # type: ignore
        except AttributeError:
            pass  # 'header' == None or 'ts' is float
        return cast(Optional[float], ts)
