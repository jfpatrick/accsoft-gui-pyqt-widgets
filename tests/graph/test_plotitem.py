import numpy as np
import pyqtgraph as pg
import pytest
from pytestqt.qtbot import QtBot
from typing import List
from enum import Enum
from qtpy import QtCore, QtWidgets, QtGui
from PyQt5 import QtTest  # qtpy.QTest incomplete: https://github.com/spyder-ide/qtpy/issues/197
from unittest import mock
from accwidgets.graph import (ExPlotItem, ExPlotWidgetConfig, TimeSpan, ScrollingPlotWidget, BarCollectionData,
                              StaticPlotWidget, EditablePlotWidget, CyclicPlotWidget, EditablePlotCurve, UpdateSource,
                              PointData, ExPlotWidget, CurveData, InjectionBarCollectionData, LivePlotCurve,
                              PlotWidgetStyle)
from .mock_utils.widget_test_window import PlotWidgetTestWindow
from .mock_utils.utils import sim_selection_moved


# ~~~~~~~~~~~~~~~~ Test Helper Function and Classes ~~~~~~~~~~~~~~~~~~~~~~~~~~


class ResumeRangeOperation(Enum):

    """
    A scrolling plot with a fixed x range allows zooming into the plot.
    There exist two ways of reverting back to the original range with a
    automatically set y range: Clicking the "View All" entry of the plot
    items context menu and clicking the small [A] button on the lower left
    corner of the plot.
    """

    view_all = 1
    auto_button = 2


class TransformRangeOperation(Enum):

    """
    A scrolling plot with a fixed x range allows zooming into the plot.
    This enum offers options for x, y and x+y transformation.
    """

    transform_xy = 1
    transform_x = 2
    transform_y = 3


def _resume_to_orig_range(plot_item: ExPlotItem, reset_operation: ResumeRangeOperation):
    """Reset the view range of a plot item"""
    if reset_operation == ResumeRangeOperation.auto_button:
        plot_item.autoBtn.mouseClickEvent(ev=None)
    elif reset_operation == ResumeRangeOperation.view_all:
        plot_item.vb.menu.viewAll.activate(QtWidgets.QAction.Trigger)
    else:
        raise ValueError(f"{reset_operation} is not a known operation for resetting the view range in the plot.")


@pytest.fixture
def scrolling_plot_test_window(qtbot: QtBot):
    """
    Prepare a window for testing

    Args:
        qtbot: qtbot pytest fixture
        time_span: time span size, how much data should be shown
    """

    def _wrapper(time_span: TimeSpan, should_create_timing_source: bool = True):
        plot_config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.SCROLLING_PLOT,
                                         time_span=time_span,
                                         time_progress_line=True)
        window = PlotWidgetTestWindow(plot_config,
                                      item_to_add=LivePlotCurve,
                                      should_create_timing_source=should_create_timing_source)
        qtbot.add_widget(window)
        with qtbot.wait_exposed(window):
            window.show()
        return window

    return _wrapper


def check_range(actual_range: List[List[float]], expected_range: List[List[float]]):
    """Compare a viewboxes range with an expected range"""
    result = True
    for actual, expected in list(zip(actual_range, expected_range)):
        if not np.isnan(expected[0]):
            result = result and np.isclose(actual[0], expected[0])
        if not np.isnan(expected[1]):
            result = result and np.isclose(actual[1], expected[1])
    return result


# ~~~~~~~~~~~~~~~~~~~~~~ Tests ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def test_scrolling_plot_fixed_scrolling_xrange(scrolling_plot_test_window):
    window = scrolling_plot_test_window(time_span=TimeSpan(left=5.0, right=0.0),
                                        should_create_timing_source=True)
    plot_item: pg.PlotItem = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(30.0)
    plot_item.vb.setRange(yRange=[-1.0, 1.0], padding=0.0)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[25.0, 30.0], [-1.0, 1.0]])
    data.create_new_value(0.0, 0.0)
    time.create_new_value(29.0)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[25.0, 30.0], [-1.0, 1.0]])
    time.create_new_value(35.0)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[30.0, 35.0], [-1.0, 1.0]])
    # time updates always set the range no matter what it was before
    plot_item.vb.setRange(xRange=[0.0, 1.0], padding=0.0)
    time.create_new_value(40.0)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[35.0, 40.0], [-1.0, 1.0]])
    # data updates do not change the x range
    data.create_new_value(41.0, 0.0)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[35.0, 40.0], [-1.0, 1.0]])


@pytest.mark.skip("It's unclear what is actually being tested here. Needs refactoring.")
@pytest.mark.parametrize("resume_operation", [
    ResumeRangeOperation.view_all,
    ResumeRangeOperation.auto_button,
])
@pytest.mark.parametrize("transform_x, transform_y", [
    (True, False),
    (False, True),
    (True, True),
])
def test_scrolling_plot_fixed_scrolling_xrange_zoom(scrolling_plot_test_window, resume_operation: ResumeRangeOperation,
                                                    transform_x, transform_y):
    window = scrolling_plot_test_window(should_create_timing_source=True,
                                        time_span=TimeSpan(left=20.0, right=0.0))
    plot_item: pg.PlotItem = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(timestamp=30.0)
    data.create_new_value(timestamp=15.0, value=-15.0)
    data.create_new_value(timestamp=20.0, value=0.0)
    data.create_new_value(timestamp=25.0, value=15.0)
    # Auto range y axis and scrolling fixed range
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[10.0, 30.0], [np.nan, np.nan]])
    assert (-15.0 - 30 * 0.1) <= plot_item.vb.targetRange()[1][0] <= -15.0
    assert 15.0 <= plot_item.vb.targetRange()[1][1] <= (15.0 + 30 * 0.1)

    def get_transform_range(plot_item: ExPlotItem, tx: bool, ty: bool, offset: float = 0.0) -> List[List[float]]:
        # We want to make sure no auto range updates are pending anymore.
        # If auto-range updates are pending, they might get executed after
        # setting the range which would destroy the range set by hand.
        if plot_item.vb._autoRangeNeedsUpdate:
            plot_item.vb.updateAutoRange()
        expected_x = [-1.0 - offset, 1.0 + offset] if tx else [np.nan, np.nan]
        expected_y = [10.0 - offset, 25.0 + offset] if ty else [np.nan, np.nan]
        return [expected_x, expected_y]

    def do_transform(plot_item: ExPlotItem, range: List[List[float]]):
        """Transform the view range of the given plot item in the given way."""
        ev = mock.MagicMock()
        ev.delta.return_value = 0.3
        ev.pos.return_value = QtCore.QPointF(0.5, 0.5)
        if not np.isnan(range[0]).any() or not np.isnan(range[1]).any():
            plot_item.vb.wheelEvent(ev)
            # plot_item.vb.sigRangeChangedManually.emit(plot_item.vb.mouseEnabled())
        if not np.isnan(range[0]).any():
            plot_item.getAxis("bottom").wheelEvent(ev)
            # plot_item.setXRange(min=range[0][0], max=range[0][1], padding=0.0)
        if not np.isnan(range[1]).any():
            plot_item.getAxis("left").wheelEvent(ev)
            # plot_item.setYRange(min=range[1][0], max=range[1][1], padding=0.0)

    # Alter range by hand
    expected_range = get_transform_range(plot_item=plot_item, tx=transform_x, ty=transform_y)
    do_transform(plot_item=plot_item, range=expected_range)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=expected_range)
    # Send timing update -> hand set range has to be kept
    time.create_new_value(31.0)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=expected_range)
    # Zoom a second time
    expected_range = get_transform_range(plot_item=plot_item, tx=transform_x, ty=transform_y, offset=1.0)
    do_transform(plot_item=plot_item, range=expected_range)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=expected_range)
    # Resume to original view range
    _resume_to_orig_range(plot_item=plot_item,
                          reset_operation=resume_operation)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[11.0, 31.0], [np.nan, np.nan]])
    assert (-15.0 - 30 * 0.1) <= plot_item.vb.targetRange()[1][0] <= -15.0
    assert 15.0 <= plot_item.vb.targetRange()[1][1] <= (15.0 + 30 * 0.1)
    time.create_new_value(32.0)
    assert check_range(actual_range=plot_item.vb.targetRange(),
                       expected_range=[[12.0, 32.0], [np.nan, np.nan]])
    assert (-15.0 - 30 * 0.1) <= plot_item.vb.targetRange()[1][0] <= -15.0
    assert 15.0 <= plot_item.vb.targetRange()[1][1] <= (15.0 + 30 * 0.1)


@pytest.mark.parametrize("plot_type, slot, data, expected", [
    # Single values
    (ScrollingPlotWidget,
     "pushData",
     [0, 1, 2],
     [0, 1, 2]),
    # (y, x) as tuple
    (ScrollingPlotWidget,
     "pushData",
     [(1, 0), (2, 1), (3, 2)],
     [(0, 1), (1, 2), (2, 3)]),
    # (y, x) as list
    (ScrollingPlotWidget,
     "pushData",
     [[1, 0], [2, 1], [3, 2]],
     [(0, 1), (1, 2), (2, 3)]),
    # (y, x) as numpy array
    (ScrollingPlotWidget,
     "pushData",
     [np.array([1, 0]), np.array([2, 1]), np.array([3, 2])],
     [(0, 1), (1, 2), (2, 3)]),
    # PointData(x, y)
    (ScrollingPlotWidget,
     "pushData",
     [PointData(0, 0), PointData(1, 1), PointData(2, 2)],
     [(0, 0), (1, 1), (2, 2)]),

    # Single values
    (CyclicPlotWidget,
     "pushData",
     [0, 1, 2], [0, 1, 2]),
    # (y, x) as tuple
    (CyclicPlotWidget,
     "pushData",
     [(1, 0), (2, 1), (3, 2)],
     [(0, 1), (1, 2), (2, 3)]),
    # (y, x) as list
    (CyclicPlotWidget,
     "pushData",
     [[1, 0], [2, 1], [3, 2]],
     [(0, 1), (1, 2), (2, 3)]),
    # (y, x) as numpy array
    (CyclicPlotWidget,
     "pushData",
     [np.array([1, 0]), np.array([2, 1]), np.array([3, 2])],
     [(0, 1), (1, 2), (2, 3)]),
    # PointData(x, y)
    (CyclicPlotWidget,
     "pushData",
     [PointData(0, 0), PointData(1, 1), PointData(2, 2)],
     [(0, 0), (1, 1), (2, 2)]),

    # array of y values
    (StaticPlotWidget,
     "replaceDataAsCurve",
     [np.array([0, 1, 2])],
     [(0, 0), (1, 1), (2, 2)]),
    # curve as 2D numpy value
    (StaticPlotWidget,
     "replaceDataAsCurve",
     [np.array([[10, 20, 30], [0, 1, 2]])],
     [(10, 0), (20, 1), (30, 2)]),
    # CurveData([x], [y])
    (StaticPlotWidget,
     "replaceDataAsCurve",
     [CurveData([10, 20, 30], [0, 1, 2])],
     [(10, 0), (20, 1), (30, 2)]),
    # multiple updates
    (StaticPlotWidget,
     "replaceDataAsCurve",
     [np.array([0, 1, 2]), np.array([10, 20, 30])],
     [(0, 10), (1, 20), (2, 30)]),
])
def test_curve_plotting_slot(qtbot,
                             plot_type,
                             slot,
                             data,
                             expected):
    plot: ExPlotWidget = plot_type()
    qtbot.add_widget(plot)
    plot.show()
    slot = getattr(plot, slot)
    assert plot.plotItem.single_value_slot_dataitem is None
    for d in data:
        slot(d)
    assert plot.plotItem.single_value_slot_dataitem is not None
    actual_x, actual_y = plot.plotItem.single_value_slot_dataitem.curve.getData()
    for i, d in enumerate(expected):
        if isinstance(d, (float, int)):
            assert actual_y[i] == d
        if isinstance(d, list):
            assert actual_x[i] == d[0]
            assert actual_y[i] == d[1]


@pytest.mark.parametrize("plot_type, data, expected", [
    # BarCollectionData([x], [y], [height])
    (StaticPlotWidget,
     [BarCollectionData(x=[10, 20, 30], y=[0, 1, 2], heights=[3, 4, 5])],
     [[10, 20, 30], [0, 1, 2], [3, 4, 5]]),
    # Multiple Updates
    (StaticPlotWidget,
     [BarCollectionData(x=[1, 2, 3], y=[4, 3, 2], heights=[1, 0, -1]),
      BarCollectionData(x=[10, 20, 30], y=[0, 1, 2], heights=[3, 4, 5])],
     [[10, 20, 30], [0, 1, 2], [3, 4, 5]]),
])
def test_bar_plotting_slots(qtbot,
                            plot_type,
                            data,
                            expected):
    plot: StaticPlotWidget = plot_type()
    qtbot.add_widget(plot)
    plot.show()
    assert plot.plotItem.single_value_slot_dataitem is None
    for d in data:
        plot.replaceDataAsBarGraph(d)
    assert plot.plotItem.single_value_slot_dataitem is not None
    bar_opts = plot.plotItem.single_value_slot_dataitem.opts
    assert np.array_equal(bar_opts.get("x"), expected[0])
    assert np.array_equal(bar_opts.get("y0"), expected[1])
    assert np.array_equal(bar_opts.get("height"), expected[2])


@pytest.mark.parametrize("plot_type, data, expected", [
    # InjectionBarCollectionData([x], [y], [height], [width], [label])
    (StaticPlotWidget,
     [InjectionBarCollectionData(x=[10, 20, 30],
                                 y=[0, 1, 2],
                                 heights=[3, 4, 5],
                                 widths=[1, 1, 1],
                                 labels=["a", "b", "c"])],
     [[10, 20, 30], [0, 1, 2], [3, 4, 5], [1, 1, 1], ["a", "b", "c"]]),
    # Multiple Updates
    (StaticPlotWidget,
     [InjectionBarCollectionData(x=[50, 60, 70],
                                 y=[2, 1, 1],
                                 heights=[5, 4, 3],
                                 widths=[2, 2, 2],
                                 labels=["l", "o", "l"]),
      InjectionBarCollectionData(x=[10, 20, 30],
                                 y=[0, 1, 2],
                                 heights=[3, 4, 5],
                                 widths=[1, 1, 1],
                                 labels=["a", "b", "c"])],
     [[10, 20, 30], [0, 1, 2], [3, 4, 5], [1, 1, 1], ["a", "b", "c"]]),
])
def test_inj_bar_plotting_slots(qtbot,
                                plot_type,
                                data,
                                expected):
    plot: StaticPlotWidget = plot_type()
    qtbot.add_widget(plot)
    plot.show()
    assert plot.plotItem.single_value_slot_dataitem is None
    for d in data:
        plot.replaceDataAsInjectionBars(d)
    assert plot.plotItem.single_value_slot_dataitem is not None
    bar_opts = plot.plotItem.single_value_slot_dataitem.opts
    assert np.array_equal(bar_opts.get("x"), expected[0])
    assert np.array_equal(bar_opts.get("y"), expected[1])
    assert np.array_equal(bar_opts.get("height"), expected[2])
    assert np.array_equal(bar_opts.get("width"), expected[3])
    text_labels: List[pg.TextItem] = plot.plotItem.single_value_slot_dataitem._text_labels
    assert len(text_labels) == len(expected[4])
    for label, text in zip(text_labels, expected[4]):
        assert label.textItem.toPlainText() == text


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Editabel Plot Item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def test_send_all_editables_state(qtbot,
                                  editable_testing_window):
    curve_count = 5
    qtbot.add_widget(editable_testing_window)
    plot: EditablePlotWidget = editable_testing_window.plot

    sources: List[UpdateSource] = []
    curves: List[EditablePlotCurve] = []
    spies: List[QtTest.QSignalSpy] = []
    for i in range(curve_count):
        source = UpdateSource()
        sources.append(source)
        curve = plot.addCurve(data_source=source)
        curves.append(curve)
        spies.append(QtTest.QSignalSpy(curve.model().sig_data_model_edited))
        initial_data = CurveData([0, 1, 2], [1 + i, 0 + i, 1 + i])
        source.send_data(initial_data)

    for i, c in list(enumerate(curves)):
        c.select(selection=QtCore.QRectF(0, 0.5 + i, 2, 1))
        assert len(spies[i]) == 0
        sim_selection_moved(c._selection, (0, 1 + i), (0, 2 + i))
        assert len(spies[i]) == 0

    assert all(plot.send_all_editables_state())
    assert all((len(s) == 1 for s in spies))


def test_plot_item_selection(qtbot,
                             editable_testing_window):
    qtbot.add_widget(editable_testing_window)
    plot: EditablePlotWidget = editable_testing_window.plot
    # Per default the plotselection is disabled (only activated when multiple
    # plots are connected to a editing-toolbar)
    plot.plotItem.make_selectable(True)
    # Since QTest API seems buggy with mouse events we have to call the
    # mouseDClick event handler by hand...
    event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonDblClick,
                              QtCore.QPointF(0, 0),
                              QtCore.Qt.LeftButton,
                              QtCore.Qt.LeftButton,
                              QtCore.Qt.NoModifier)
    plot.mouseDoubleClickEvent(event)
    assert plot.plotItem._plot_selected
    plot.mouseDoubleClickEvent(event)
    assert not plot.plotItem._plot_selected
