"""Module for signal based updates for the graph and implementation"""

from qtpy.QtCore import QObject, Signal

from accsoft_gui_pyqt_widgets.graph.datamodel.datastructures import (
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
    """Baseclass for update-sources

    Baseclass with predefined signals for timing and data updates.
    This can be subclassed to define own timing and data update sources.
    """

    # TODO: Range Change Signal not used yet. Change dict to fitting type when integrated.
    sig_range_update = Signal(dict)
    sig_timing_update = Signal(float)
    sig_data_update = Signal(
        [PointData],
        [CurveData],
        [BarData],
        [BarCollectionData],
        [InjectionBarData],
        [InjectionBarCollectionData],
        [TimestampMarkerData],
        [TimestampMarkerCollectionData]
    )
