"""
Tests for emitting valid and non valid data structures to an item in a plot.
Validity of data structures is test in the tests for datastructures
"""
import numpy as np
import pytest

from accwidgets import graph as accgraph
from .mock_utils.utils import warn_always

# For matching warning messages we capture
_INVALID_DATA_STRUCTURE_WARNING_MSG = r"is not valid and can't be drawn for " \
                                      r"the following reasons:"


@pytest.mark.parametrize("missing_value", [np.nan, None])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_curves(qtbot, minimal_test_window, recwarn, missing_value):
    data_source = accgraph.UpdateSource()
    minimal_test_window.plot.addCurve(data_source=data_source, pen="r")
    model: accgraph.LiveCurveDataModel = minimal_test_window.plot.plotItem.live_curves[0].model()
    buffer: accgraph.SortedCurveDataBuffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [])
    np.testing.assert_equal(buffer[1], [])
    # valid
    data_source.send_data(accgraph.PointData(x=0.0, y=2.0))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0])
    np.testing.assert_equal(buffer[1], [2.0])
    # valid
    data_source.send_data(accgraph.PointData(x=1.0, y=missing_value))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 1.0])
    np.testing.assert_equal(buffer[1], [2.0, np.nan])
    # valid
    data_source.send_data(accgraph.PointData(x=missing_value, y=missing_value))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 1.0, np.nan])
    np.testing.assert_equal(buffer[1], [2.0, np.nan, np.nan])
    # valid
    data_source.send_data(accgraph.PointData(x=0.0, y=missing_value))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 0.0, 1.0, np.nan])
    np.testing.assert_equal(buffer[1], [2.0, np.nan, np.nan, np.nan])


@pytest.mark.parametrize("missing_value", [np.nan, None])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_curves(qtbot, minimal_test_window, missing_value):
    ds = accgraph.UpdateSource()
    minimal_test_window.plot.addCurve(data_source=ds, pen="r")
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.PointData(x=missing_value, y=2.0))
    buffer: accgraph.SortedCurveDataBuffer = minimal_test_window.plot.plotItem.live_curves[0].model().full_data_buffer
    np.testing.assert_equal(buffer[0], [])
    np.testing.assert_equal(buffer[1], [])
    # valid
    ds.send_data(accgraph.PointData(x=0.0, y=3.0))
    buffer: accgraph.SortedCurveDataBuffer = minimal_test_window.plot.plotItem.live_curves[0].model().full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0])
    np.testing.assert_equal(buffer[1], [3.0])
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.PointData(x=missing_value, y=4.0))
    buffer: accgraph.SortedCurveDataBuffer = minimal_test_window.plot.plotItem.live_curves[0].model().full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0])
    np.testing.assert_equal(buffer[1], [3.0])


# ~~~~~~~~~~~~~~~~~~~~~~~~~ Bar Graphs ~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("missing_value", [np.nan, None])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_bars(qtbot, minimal_test_window, recwarn, missing_value):
    ds = accgraph.UpdateSource()
    minimal_test_window.plot.addBarGraph(data_source=ds)
    model: accgraph.LiveBarGraphDataModel = minimal_test_window.plot.plotItem.live_bar_graphs[0].model()
    # valid
    ds.send_data(accgraph.BarData(x=1.0, y=missing_value, height=2.0))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [1.0])
    np.testing.assert_equal(buffer[1], [0.0])
    np.testing.assert_equal(buffer[2], [2.0])
    # valid
    ds.send_data(accgraph.BarData(x=0.0, y=1.0, height=2.0))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 1.0])
    np.testing.assert_equal(buffer[1], [1.0, 0.0])
    np.testing.assert_equal(buffer[2], [2.0, 2.0])


@pytest.mark.parametrize("missing_value", [np.nan, None])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_bars(qtbot, minimal_test_window, missing_value):
    ds = accgraph.UpdateSource()
    minimal_test_window.plot.addBarGraph(data_source=ds)
    model: accgraph.LiveBarGraphDataModel = minimal_test_window.plot.plotItem.live_bar_graphs[0].model()
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.BarData(x=1.0, y=1.0, height=missing_value))
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [])
    np.testing.assert_equal(buffer[1], [])
    np.testing.assert_equal(buffer[2], [])
    # valid
    ds.send_data(accgraph.BarData(x=1.0, y=missing_value, height=2.0))
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [1.0])
    np.testing.assert_equal(buffer[1], [0.0])
    np.testing.assert_equal(buffer[2], [2.0])
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.BarData(x=missing_value, y=1.0, height=1.0))
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [1.0])
    np.testing.assert_equal(buffer[1], [0.0])
    np.testing.assert_equal(buffer[2], [2.0])


# ~~~~~~~~~~~~~~~~~~~~~~~~~ Injection-Bar Graphs ~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("missing_value", [np.nan, None])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_valid_injection_bars(qtbot, minimal_test_window, recwarn, missing_value):
    ds = accgraph.UpdateSource()
    minimal_test_window.plot.addInjectionBar(data_source=ds)
    model: accgraph.LiveInjectionBarDataModel = minimal_test_window.plot.plotItem.live_injection_bars[0].model()
    # valid
    ds.send_data(accgraph.InjectionBarData(x=0.0,
                                           y=1.0,
                                           height=missing_value,
                                           width=1.0,
                                           label="1"))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0])
    np.testing.assert_equal(buffer[1], [1.0])
    np.testing.assert_equal(buffer[2], [np.nan])
    np.testing.assert_equal(buffer[3], [1.0])
    np.testing.assert_equal(buffer[4], ["1"])
    # valid
    ds.send_data(accgraph.InjectionBarData(x=1.0,
                                           y=1.0,
                                           height=1.0,
                                           width=missing_value,
                                           label="2"))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 1.0])
    np.testing.assert_equal(buffer[1], [1.0, 1.0])
    np.testing.assert_equal(buffer[2], [np.nan, 1.0])
    np.testing.assert_equal(buffer[3], [1.0, np.nan])
    np.testing.assert_equal(buffer[4], ["1", "2"])
    # valid
    ds.send_data(accgraph.InjectionBarData(x=2.0,
                                           y=1.0,
                                           height=missing_value,
                                           width=missing_value,
                                           label="3"))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 1.0, 2.0])
    np.testing.assert_equal(buffer[1], [1.0, 1.0, 1.0])
    np.testing.assert_equal(buffer[2], [np.nan, 1.0, np.nan])
    np.testing.assert_equal(buffer[3], [1.0, np.nan, np.nan])
    np.testing.assert_equal(buffer[4], ["1", "2", "3"])


@pytest.mark.parametrize("missing_value", [np.nan, None])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_injection_bars(qtbot, minimal_test_window, missing_value):
    ds = accgraph.UpdateSource()
    minimal_test_window.plot.addInjectionBar(data_source=ds)
    model: accgraph.LiveInjectionBarDataModel = minimal_test_window.plot.plotItem.live_injection_bars[0].model()
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.InjectionBarData(x=missing_value,
                                               y=1.0,
                                               height=1.0,
                                               width=1.0,
                                               label="6"))
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [])
    np.testing.assert_equal(buffer[1], [])
    np.testing.assert_equal(buffer[2], [])
    np.testing.assert_equal(buffer[3], [])
    # assert_equals seems to fail with an empty string array (ZeroDivisionError)
    assert buffer[4].size == 0
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.InjectionBarData(x=5.0,
                                               y=missing_value,
                                               height=1.0,
                                               width=1.0,
                                               label="7"))
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [])
    np.testing.assert_equal(buffer[1], [])
    np.testing.assert_equal(buffer[2], [])
    np.testing.assert_equal(buffer[3], [])
    # assert_equals seems to fail with an empty string array
    assert buffer[4].size == 0
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.InjectionBarData(x=missing_value,
                                               y=missing_value,
                                               height=1.0,
                                               width=1.0,
                                               label="8"))
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [])
    np.testing.assert_equal(buffer[1], [])
    np.testing.assert_equal(buffer[2], [])
    np.testing.assert_equal(buffer[3], [])
    # assert_equals seems to fail with an empty string array
    assert buffer[4].size == 0


# ~~~~~~~~~~~~~~~~~~~~~~~~~ Timestamp Marker ~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("missing_value", ["", None])
@warn_always(accgraph.InvalidValueWarning)
def test_valid_timestamp_markers(qtbot, minimal_test_window, recwarn, missing_value):
    ds = accgraph.UpdateSource()
    minimal_test_window.plot.addTimestampMarker(data_source=ds)
    model: accgraph.TimestampMarkerData = minimal_test_window.plot.plotItem.live_timestamp_markers[0].model()
    # valid
    ds.send_data(accgraph.TimestampMarkerData(x=0.0,
                                              color=missing_value,
                                              label="1"))
    assert recwarn.pop(accgraph.InvalidValueWarning)
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0])
    np.testing.assert_equal(buffer[1], ["w"])
    np.testing.assert_equal(buffer[2], ["1"])
    # valid
    ds.send_data(accgraph.TimestampMarkerData(x=1.0,
                                              color="r",
                                              label=missing_value))
    assert len(recwarn) == 0
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 1.0])
    np.testing.assert_equal(buffer[1], ["w", "r"])
    np.testing.assert_equal(buffer[2], ["1", ""])
    # valid
    ds.send_data(accgraph.TimestampMarkerData(x=2.0,
                                              color=missing_value,
                                              label=missing_value))
    assert recwarn.pop(accgraph.InvalidValueWarning)
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [0.0, 1.0, 2.0])
    np.testing.assert_equal(buffer[1], ["w", "r", "w"])
    np.testing.assert_equal(buffer[2], ["1", "", ""])


@pytest.mark.parametrize("missing_value", [np.nan, None])
@warn_always(accgraph.InvalidDataStructureWarning)
def test_invalid_timestamp_markers(qtbot, minimal_test_window, missing_value):
    ds = accgraph.UpdateSource()
    minimal_test_window.plot.addTimestampMarker(data_source=ds)
    model: accgraph.TimestampMarkerData = minimal_test_window.plot.plotItem.live_timestamp_markers[0].model()
    # invalid
    with pytest.warns(accgraph.InvalidDataStructureWarning,
                      match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
        ds.send_data(accgraph.TimestampMarkerData(x=missing_value,
                                                  color="r",
                                                  label="1"))
    buffer = model.full_data_buffer
    np.testing.assert_equal(buffer[0], [])
    # assert_equals seems to fail with an empty string array
    assert buffer[1].size == 0
    assert buffer[2].size == 0
