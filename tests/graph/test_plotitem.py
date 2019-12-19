from typing import List
from enum import Enum

import numpy as np
import pyqtgraph as pg
import pytest
from qtpy.QtWidgets import QAction

from accwidgets import graph as accgraph

from .mock_utils.widget_test_window import PlotWidgetTestWindow


def test_scrolling_plot_fixed_scrolling_xrange(qtbot):
    """ Test the fixed x range option on the scrolling plot

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(
        qtbot=qtbot,
        time_span=accgraph.TimeSpan(
            left=5.0,
            right=0.0,
        ),
        should_create_timing_source=True
    )
    plot_item: pg.PlotItem = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(30.0)
    plot_item.vb.setRange(yRange=[-1.0, 1.0], padding=0.0)
    assert check_range(plot_item.vb.targetRange(), [[25.0, 30.0], [-1.0, 1.0]])
    data.create_new_value(0.0, 0.0)
    time.create_new_value(29.0)
    assert check_range(plot_item.vb.targetRange(), [[25.0, 30.0], [-1.0, 1.0]])
    time.create_new_value(35.0)
    assert check_range(plot_item.vb.targetRange(), [[30.0, 35.0], [-1.0, 1.0]])
    # time updates always set the range no matter what it was before
    plot_item.vb.setRange(xRange=[0.0, 1.0], padding=0.0)
    time.create_new_value(40.0)
    assert check_range(plot_item.vb.targetRange(), [[35.0, 40.0], [-1.0, 1.0]])
    # data updates do not change the x range
    data.create_new_value(41.0, 0.0)
    assert check_range(plot_item.vb.targetRange(), [[35.0, 40.0], [-1.0, 1.0]])


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


@pytest.mark.parametrize("resume_operation", [
    ResumeRangeOperation.view_all,
    ResumeRangeOperation.auto_button
])
@pytest.mark.parametrize("transform_operation", [
    TransformRangeOperation.transform_x,
    TransformRangeOperation.transform_y,
    TransformRangeOperation.transform_xy,
])
def test_scrolling_plot_fixed_scrolling_xrange_zoom(
        qtbot,
        resume_operation: ResumeRangeOperation,
        transform_operation: TransformRangeOperation
):
    """
    Test handling of transformation operations if the fixed x range option is
    activated.

    Args:
        qtbot: pytest-qt fixture to control pyqt applications
    """
    window = _prepare_cyclic_plot_test_window(
        qtbot=qtbot,
        time_span=accgraph.TimeSpan(
            left=20.0,
            right=0.0,
        ),
        should_create_timing_source=True
    )
    plot_item: pg.PlotItem = window.plot.plotItem
    time = window.time_source_mock
    data = window.data_source_mock
    time.create_new_value(30.0)
    data.create_new_value(timestamp=15.0, value=-15.0)
    data.create_new_value(timestamp=20.0, value=0.0)
    data.create_new_value(timestamp=25.0, value=15.0)
    qtbot.waitForWindowShown(window)
    # Auto range y axis and scrolling fixed range
    assert check_range(
        plot_item.vb.targetRange(),
        [[10.0, 30.0], [np.nan, np.nan]]
    )
    assert (-15.0 - 30 * 0.1) <= plot_item.vb.targetRange()[1][0] <= -15.0
    assert 15.0 <= plot_item.vb.targetRange()[1][1] <= (15.0 + 30 * 0.1)
    # Alter range by hand
    expected = _transform_operation(
        plot_item=plot_item,
        transform_operation=transform_operation
    )
    assert check_range(
        actual_range=plot_item.vb.targetRange(),
        expected_range=expected
    )
    # Send timing update -> hand set range has to be kept
    time.create_new_value(31.0)
    assert check_range(
        actual_range=plot_item.vb.targetRange(),
        expected_range=expected
    )
    # Zoom a second time
    expected = _transform_operation(
        plot_item=plot_item,
        transform_operation=transform_operation,
        offset=1.0
    )
    assert check_range(
        actual_range=plot_item.vb.targetRange(),
        expected_range=expected
    )
    # Resume to original view range
    _resume_to_orig_range(
        plot_item=plot_item,
        reset_operation=resume_operation
    )
    assert check_range(
        plot_item.vb.targetRange(),
        [[11.0, 31.0], [np.nan, np.nan]]
    )
    assert (-15.0 - 30 * 0.1) <= plot_item.vb.targetRange()[1][0] <= -15.0
    assert 15.0 <= plot_item.vb.targetRange()[1][1] <= (15.0 + 30 * 0.1)
    time.create_new_value(32.0)
    assert check_range(
        plot_item.vb.targetRange(),
        [[12.0, 32.0], [np.nan, np.nan]]
    )
    assert (-15.0 - 30 * 0.1) <= plot_item.vb.targetRange()[1][0] <= -15.0
    assert 15.0 <= plot_item.vb.targetRange()[1][1] <= (15.0 + 30 * 0.1)


def _transform_operation(
        plot_item: accgraph.ExPlotItem,
        transform_operation: TransformRangeOperation,
        offset: float = 0.0
) -> List[List[float]]:
    """Transform the view range of the given plot item in the given way."""
    # We want to make sure no auto range updates are pending anymore.
    # If auto-range updates are pending, they might get executed after
    # setting the range which would destroy the range set by hand.
    if plot_item.vb._autoRangeNeedsUpdate:
        plot_item.vb.updateAutoRange()
    if transform_operation == TransformRangeOperation.transform_xy:
        expected = [[-1.0 - offset, 1.0 + offset], [10.0 - offset, 25.0 + offset]]
    elif transform_operation == TransformRangeOperation.transform_x:
        expected = [[-1.0 - offset, 1.0 + offset], [np.nan, np.nan]]
    elif transform_operation == TransformRangeOperation.transform_y:
        expected = [[np.nan, np.nan], [10.0 - offset, 25.0 + offset]]
    else:
        raise ValueError(
            f"{transform_operation} is not a known operation for transforming the view range in the plot."
        )
    if not np.isnan(expected[0]).any() or not np.isnan(expected[1]).any():
        plot_item.vb.sigRangeChangedManually.emit(plot_item.vb.mouseEnabled())
    if not np.isnan(expected[0]).any():
        plot_item.setXRange(min=expected[0][0], max=expected[0][1], padding=0.0)
    if not np.isnan(expected[1]).any():
        plot_item.setYRange(min=expected[1][0], max=expected[1][1], padding=0.0)
    return expected


def _resume_to_orig_range(plot_item: accgraph.ExPlotItem, reset_operation: ResumeRangeOperation) -> None:
    """Reset the view range of a plot item"""
    if reset_operation == ResumeRangeOperation.auto_button:
        plot_item.autoBtn.mouseClickEvent(ev=None)
    elif reset_operation == ResumeRangeOperation.view_all:
        plot_item.vb.menu.viewAll.activate(QAction.Trigger)
    else:
        raise ValueError(
            f"{reset_operation} is not a known operation for resetting the view range in the plot."
        )


def _prepare_cyclic_plot_test_window(qtbot, time_span: accgraph.TimeSpan, should_create_timing_source: bool = True):
    """
    Prepare a window for testing

    Args:
        qtbot: qtbot pytest fixture
        time_span: time span size, how much data should be shown
    """
    plot_config = accgraph.ExPlotWidgetConfig(
        plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
        time_span=time_span,
        time_progress_line=True,
    )
    window = PlotWidgetTestWindow(
        plot_config,
        item_to_add=accgraph.LivePlotCurve,
        should_create_timing_source=should_create_timing_source
    )
    window.show()
    qtbot.addWidget(window)
    return window


def check_range(actual_range: List[List[float]], expected_range: List[List[float]]):
    """Compare a viewboxes range with an expected range"""
    result = True
    for actual, expected in list(zip(actual_range, expected_range)):
        if not np.isnan(expected[0]):
            result = result and np.isclose(actual[0], expected[0])
        if not np.isnan(expected[1]):
            result = result and np.isclose(actual[1], expected[1])
    return result
