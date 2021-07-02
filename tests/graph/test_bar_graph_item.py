import numpy as np
import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from accwidgets.graph import (ExPlotWidgetConfig, PlotWidgetStyle, UpdateSource, BarData, BarCollectionData,
                              PointData, CurveData)
from .mock_utils.widget_test_window import PlotWidgetTestWindow


@pytest.mark.parametrize("auto_scaling_enabled,widget_type,data,is_collection,expected_range", [
    # Cyclic plot does not support bar graphs
    (True, PlotWidgetStyle.SCROLLING_PLOT, [0.0, 0.5, 2.5, 3.5], False, [0.0, 3.5]),
    (True, PlotWidgetStyle.SCROLLING_PLOT, [1e-5, 2.5e-5, 1.5e-5, 1e-6], False, [1e-6, 2.5e-5]),
    (True, PlotWidgetStyle.STATIC_PLOT, [0.0, 0.5, 2.5, 3.5], True, [0.0, 3.5]),
    (True, PlotWidgetStyle.STATIC_PLOT, [1e-5, 2.5e-5, 1.5e-5, 1e-6], True, [1e-6, 2.5e-5]),
    (False, PlotWidgetStyle.SCROLLING_PLOT, [0.0, 0.5, 2.5, 3.5], False, [0.0, 1.0]),
    (False, PlotWidgetStyle.SCROLLING_PLOT, [1e-5, 2.5e-5, 1.5e-5, 1e-6], False, [0.0, 1.0]),
    (False, PlotWidgetStyle.STATIC_PLOT, [0.0, 0.5, 2.5, 3.5], True, [0.0, 1.0]),
    (False, PlotWidgetStyle.STATIC_PLOT, [1e-5, 2.5e-5, 1.5e-5, 1e-6], True, [0.0, 1.0]),
])
def test_bargraph_auto_scales_alone(qtbot: QtBot, widget_type, auto_scaling_enabled, data, is_collection, expected_range):
    plot_config = ExPlotWidgetConfig(plotting_style=widget_type)
    window = PlotWidgetTestWindow(plot_config, should_create_timing_source=False)
    qtbot.add_widget(window)

    if not auto_scaling_enabled:
        window.plot.disableAutoRange()

    source = UpdateSource()
    window.plot.addBarGraph(data_source=source, width=0.5)
    if is_collection:
        source.send_data(BarCollectionData(x=list(range(len(data))), y=np.zeros(len(data)), heights=data))
    else:
        for i, data_point in enumerate(data):
            source.send_data(BarData(x=i, height=data_point))

    # Instead of placing delays to wait for automatic update, trigger it here
    if window.plot.getViewBox()._autoRangeNeedsUpdate:
        window.plot.getViewBox().updateAutoRange()

    tolerance = np.max(np.abs(expected_range)) * 0.1  # Allow margin of 10% in variation (for padding of the graph)
    assert np.all(np.abs(np.array(expected_range) - np.array(window.plot.getViewBox().targetRange()[1])) <= tolerance)


@pytest.mark.parametrize("auto_scaling_enabled,widget_type,datas,items,expected_range", [
    # Cyclic plot does not support bar graphs
    (
        True, PlotWidgetStyle.SCROLLING_PLOT,
        [
            iter([
                BarData(x=0, y=0.3, height=0.3),
                BarData(x=1, y=0.3, height=0.5),
                BarData(x=2, y=0.3, height=2.5),
                BarData(x=3, y=0.3, height=3.5),
            ]),
            iter([
                PointData(x=0, y=1e-5),
                PointData(x=1, y=2.5e-5),
                PointData(x=2, y=1.5e-5),
                PointData(x=3, y=1e-6),
            ]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [1e-5, 3.8],
    ), (
        True, PlotWidgetStyle.SCROLLING_PLOT,
        [
            iter([
                BarData(x=0, y=0.1, height=1e-5),
                BarData(x=1, y=0.1, height=2.5e-5),
                BarData(x=2, y=0.1, height=1.5e-5),
                BarData(x=3, y=0.1, height=1e-6),
            ]),
            iter([
                PointData(x=0, y=0.3),
                PointData(x=1, y=0.5),
                PointData(x=2, y=2.5),
                PointData(x=3, y=3.5),
            ]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [0.1, 3.5],
    ), (
        True, PlotWidgetStyle.STATIC_PLOT,
        [
            iter([BarCollectionData(x=list(range(4)), y=[0.3] * 4, heights=[0.3, 0.5, 2.5, 3.5])]),
            iter([CurveData(x=list(range(4)), y=[1e-5, 2.5e-5, 1.5e-5, 1e-6])]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [1e-5, 3.8],
    ), (
        True, PlotWidgetStyle.STATIC_PLOT,
        [
            iter([BarCollectionData(x=list(range(4)), y=[0.1] * 4, heights=[1e-5, 2.5e-5, 1.5e-5, 1e-6])]),
            iter([CurveData(x=list(range(4)), y=[0.3, 0.5, 2.5, 3.5])]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [0.1, 3.5],
    ), (
        False, PlotWidgetStyle.SCROLLING_PLOT,
        [
            iter([
                BarData(x=0, y=0.3, height=0.3),
                BarData(x=1, y=0.3, height=0.5),
                BarData(x=2, y=0.3, height=2.5),
                BarData(x=3, y=0.3, height=3.5),
            ]),
            iter([
                PointData(x=0, y=1e-5),
                PointData(x=1, y=2.5e-5),
                PointData(x=2, y=1.5e-5),
                PointData(x=3, y=1e-6),
            ]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [0.0, 1.0],
    ), (
        False, PlotWidgetStyle.SCROLLING_PLOT,
        [
            iter([
                BarData(x=0, y=0.1, height=1e-5),
                BarData(x=1, y=0.1, height=2.5e-5),
                BarData(x=2, y=0.1, height=1.5e-5),
                BarData(x=3, y=0.1, height=1e-6),
            ]),
            iter([
                PointData(x=0, y=0.3),
                PointData(x=1, y=0.5),
                PointData(x=2, y=2.5),
                PointData(x=3, y=3.5),
            ]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [0.0, 1.0],
    ), (
        False, PlotWidgetStyle.STATIC_PLOT,
        [
            iter([BarCollectionData(x=list(range(4)), y=[0.3] * 4, heights=[0.3, 0.5, 2.5, 3.5])]),
            iter([CurveData(x=list(range(4)), y=[1e-5, 2.5e-5, 1.5e-5, 1e-6])]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [0.0, 1.0],
    ), (
        False, PlotWidgetStyle.STATIC_PLOT,
        [
            iter([BarCollectionData(x=list(range(4)), y=[0.1] * 4, heights=[1e-5, 2.5e-5, 1.5e-5, 1e-6])]),
            iter([CurveData(x=list(range(4)), y=[0.3, 0.5, 2.5, 3.5])]),
        ],
        [
            ("addBarGraph", {"width": 0.5}),
            ("addCurve", {}),
        ],
        [0.0, 1.0],
    ),
])
def test_bargraph_auto_scales_with_other_items(qtbot: QtBot, widget_type, items, auto_scaling_enabled, datas, expected_range):
    plot_config = ExPlotWidgetConfig(plotting_style=widget_type)
    window = PlotWidgetTestWindow(plot_config, should_create_timing_source=False)
    qtbot.add_widget(window)

    if not auto_scaling_enabled:
        window.plot.disableAutoRange()

    sources = []
    for item, opts in items:
        source = UpdateSource()
        sources.append(source)
        getattr(window.plot, item)(data_source=source, **opts)

    iter_exhausted = False
    while not iter_exhausted:
        for source, data_iter in zip(sources, datas):
            try:
                next_data = next(data_iter)
            except StopIteration:
                iter_exhausted = True
                break
            source.send_data(next_data)

    # Instead of placing delays to wait for automatic update, trigger it here
    if window.plot.getViewBox()._autoRangeNeedsUpdate:
        window.plot.getViewBox().updateAutoRange()

    tolerance = np.max(np.abs(expected_range)) * 0.1  # Allow margin of 10% in variation (for padding of the graph)
    assert np.all(np.abs(np.array(expected_range) - np.array(window.plot.getViewBox().targetRange()[1])) <= tolerance)


@pytest.mark.parametrize("widget_type", [
    PlotWidgetStyle.SCROLLING_PLOT,
    PlotWidgetStyle.STATIC_PLOT,
])
@pytest.mark.parametrize("axis", [0, 1])
@mock.patch("numpy.isscalar")
def test_bargraph_caches_auto_scale_calculation(isscalar, qtbot: QtBot, widget_type, axis):
    # detect by usage of np.isscalar inside the dataBounds method.
    plot_config = ExPlotWidgetConfig(plotting_style=widget_type)
    window = PlotWidgetTestWindow(plot_config, should_create_timing_source=False)
    qtbot.add_widget(window)
    source = UpdateSource()
    bar_graph = window.plot.addBarGraph(data_source=source, width=0.5)
    bar_graph.invalidateBounds()
    assert bar_graph._boundsCache[axis] is None
    isscalar.reset_mock()
    bar_graph.dataBounds(axis)
    isscalar.assert_called()
    isscalar.reset_mock()
    assert isinstance(bar_graph._boundsCache[axis], tuple)
    bar_graph.dataBounds(axis)
    isscalar.assert_not_called()
    assert isinstance(bar_graph._boundsCache[axis], tuple)


@pytest.mark.parametrize("widget_type", [
    PlotWidgetStyle.SCROLLING_PLOT,
    PlotWidgetStyle.STATIC_PLOT,
])
@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("call_fn,args", [
    ("viewTransformChanged", {}),
    ("setOpts", {"width": 0.3}),
])
def test_bargraph_cache_reset(qtbot: QtBot, widget_type, axis, call_fn, args):
    # detect by usage of np.isscalar inside the dataBounds method.
    plot_config = ExPlotWidgetConfig(plotting_style=widget_type)
    window = PlotWidgetTestWindow(plot_config, should_create_timing_source=False)
    qtbot.add_widget(window)
    source = UpdateSource()
    bar_graph = window.plot.addBarGraph(data_source=source, width=0.5)
    bar_graph.invalidateBounds()
    assert bar_graph._boundsCache[axis] is None
    bar_graph.dataBounds(axis)
    assert isinstance(bar_graph._boundsCache[axis], tuple)
    getattr(bar_graph, call_fn)(**args)
    assert bar_graph._boundsCache[axis] is None


@pytest.mark.parametrize("bargraph_kwargs, expect_is_correct", (
    ({"x": [1], "width": [2], "height": [1]}, True),
    ({"x": [1], "width": [2], "y1": [1]}, True),
    ({"x0": [1], "width": [2], "y1": [1]}, True),
    ({"x1": [1], "width": [2], "y1": [1]}, True),
    ({"x0": [1], "x1": [2], "y1": [1]}, True),
    ({"x0": [1], "x1": [2], "y1": [1], "height": [2]}, True),
    ({"x0": [1], "x1": [2], "width": [3], "y1": [1]}, True),
    ({"x": [0], "x0": [1], "x1": [2], "width": [3], "y1": [1]}, True),
    ({"x0": [1], "x1": [2], "y0": [-1], "y1": [1]}, True),
    ({"x": [1], "width": [2]}, False),
    ({"x1": [1], "width": [2]}, False),
    ({"x": [1], "height": [2]}, False),
    ({"x": [1], "y1": [2]}, False),
    ({"x0": [1], "y1": [2]}, False),
    ({"x1": [1], "y1": [2]}, False),
))
def test_bargraph_no_source_requires_correct_kwargs(qtbot, bargraph_kwargs, expect_is_correct):
    plot_config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.STATIC_PLOT)
    window = PlotWidgetTestWindow(plot_config, should_create_timing_source=False)
    qtbot.add_widget(window)

    if expect_is_correct:
        _ = window.plot.addBarGraph(**bargraph_kwargs)
    else:
        with pytest.raises(ValueError):
            _ = window.plot.addBarGraph(**bargraph_kwargs)
