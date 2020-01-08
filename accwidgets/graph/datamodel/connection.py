"""Module for signal based updates for the graph and implementation"""

from qtpy.QtCore import QObject, Signal

from accwidgets.graph.datamodel.datastructures import (
    BarCollectionData,
    BarData,
    CurveData,
    TimestampMarkerCollectionData,
    TimestampMarkerData,
    InjectionBarCollectionData,
    InjectionBarData,
    PointData,
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
