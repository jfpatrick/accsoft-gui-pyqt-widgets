from unittest import mock

# qtpy.QTest incomplete: https://github.com/spyder-ide/qtpy/issues/197
from PyQt5 import QtTest
from qtpy import QtCore
import pytest
import numpy as np
import pyqtgraph as pg

import accwidgets.graph as accgraph
from .mock_utils.utils import (sim_selection_moved,
                               assert_qpen_equals,
                               assert_qbrush_equals)


def test_editable_curve_supported_plotting_style():
    style = accgraph.EditablePlotCurve.supported_plotting_style
    assert style == accgraph.PlotWidgetStyle.EDITABLE


@pytest.mark.parametrize("selection, expected_indices", [
    (QtCore.QRectF(0, 1, 4, 2), [True, True, True, True, True]),
    (QtCore.QRectF(0, 1.2, 4, 0.9), [False, True, False, True, False]),
    (QtCore.QRectF(0, 1, 0.5, 0.5), [False, False, False, False, False]),
    (None, [False, False, False, False, False]),
])
def test_point_selection(qtbot,
                         editable_testing_window,
                         selection,
                         expected_indices):
    qtbot.addWidget(editable_testing_window)
    plot: accgraph.EditablePlotWidget = editable_testing_window.plot

    source: accgraph.UpdateSource = accgraph.UpdateSource()
    curve: accgraph.EditablePlotCurve = plot.addCurve(data_source=source)
    source.new_data(accgraph.CurveData(x=[0, 1, 2, 3, 4], y=[3, 2, 1, 2, 3]))

    spy = QtTest.QSignalSpy(curve.sig_selection_changed)
    assert len(spy) == 0

    if selection:
        curve.select(selection=selection)
    else:
        curve.unselect()

    assert len(spy) == 1
    assert np.array_equal(curve._selected_indices, expected_indices)


@pytest.mark.parametrize(
    "pen, "
    "brush, "
    "symbol, "
    "selection_pen, "
    "selection_brush", [
        # Curve without a symbol
        (pg.mkPen((255, 255, 255), width=1),
         None,
         None,
         pg.mkPen((255, 0, 0), width=3),
         pg.mkBrush((255, 255, 255))),
        # White curve
        (pg.mkPen((255, 255, 255), width=1),
         pg.mkBrush((255, 255, 255)),
         "o",
         pg.mkPen((255, 0, 0), width=3),
         pg.mkBrush(None)),
        # Black curve
        (pg.mkPen((0, 0, 0), width=1),
         pg.mkBrush((0, 0, 0)),
         "o",
         pg.mkPen((255, 0, 0), width=3),
         pg.mkBrush(None)),
        # Greyish curve
        (pg.mkPen((123, 128, 125), width=1),
         pg.mkBrush((123, 128, 125)),
         "o",
         pg.mkPen((255, 0, 0), width=3),
         pg.mkBrush(None)),
        # Different symbol
        (pg.mkPen((250, 5, 120), width=1),
         pg.mkBrush((255, 0, 255)),
         "+",
         pg.mkPen((5, 250, 135), width=3),
         pg.mkBrush(None)),
        # Colored curve
        (pg.mkPen((250, 5, 120), width=1),
         pg.mkBrush((255, 0, 255)),
         "o",
         pg.mkPen((5, 250, 135), width=3),
         pg.mkBrush(None))],
)
def test_selection_style(qtbot,
                         editable_testing_window,
                         pen,
                         brush,
                         symbol,
                         selection_pen,
                         selection_brush):
    qtbot.addWidget(editable_testing_window)
    plot: accgraph.EditablePlotWidget = editable_testing_window.plot

    source: accgraph.UpdateSource = accgraph.UpdateSource()
    # The line color does not matter, when setting the selection color,
    # only the dots' pen color does matter
    curve: accgraph.EditablePlotCurve = plot.addCurve(data_source=source,
                                                      symbolSize=1,
                                                      symbolPen=pen,
                                                      symbolBrush=brush,
                                                      symbol=symbol)
    source.new_data(accgraph.CurveData(x=[0, 1, 2, 3, 4], y=[3, 2, 1, 2, 3]))

    curve.select(selection=QtCore.QRectF(0, 1.2, 4, 0.9))
    assert_qpen_equals(curve._selection.opts["pen"], selection_pen)
    assert_qbrush_equals(curve._selection.opts["brush"], selection_brush)
    assert curve._selection.opts["symbol"] == curve.scatter.opts["symbol"]
    # Minimum size for symbols is 5 pixels
    assert curve._selection.opts["size"] == 5


@pytest.mark.parametrize("direction, movement, expected_x, expected_y", [
    (accgraph.DragDirection.Y,
     ((0.0, 3.0), (1.0, 4.0)),
     [0, 1, 2, 3, 4],
     [4, 2, 1, 2, 4]),
    (accgraph.DragDirection.X,
     ((0.0, 3.0), (1.0, 4.0)),
     [1, 1, 2, 3, 5],
     [3, 2, 1, 2, 3]),
    (accgraph.DragDirection.X | accgraph.DragDirection.Y,
     ((0.0, 3.0), (1.0, 4.0)),
     [1, 1, 2, 3, 5],
     [4, 2, 1, 2, 4]),
])
def test_selection_moved(qtbot,
                         editable_testing_window,
                         direction,
                         movement,
                         expected_x,
                         expected_y):
    qtbot.addWidget(editable_testing_window)
    plot: accgraph.EditablePlotWidget = editable_testing_window.plot

    source: accgraph.UpdateSource = accgraph.UpdateSource()
    curve: accgraph.EditablePlotCurve = plot.addCurve(data_source=source)
    source.new_data(accgraph.CurveData(x=[0, 1, 2, 3, 4], y=[3, 2, 1, 2, 3]))

    spy = QtTest.QSignalSpy(curve.sig_selection_changed)
    assert len(spy) == 0
    curve.select(selection=QtCore.QRectF(0, 2.5, 4, 1))
    curve.selection.drag_direction = direction
    assert len(spy) == 1
    sim_selection_moved(curve._selection, *movement)
    assert len(spy) == 2
    x, y = curve.getData()
    assert np.array_equal(x, expected_x)
    assert np.array_equal(y, expected_y)


@pytest.mark.parametrize("selection, labels, activate_labels", [
    (QtCore.QRectF(0, 2.5, 4, 1), [(0, 3), (4, 3)], True),
    (QtCore.QRectF(0, 2.5, 4, 1), [], False),
    (QtCore.QRectF(0, 5, 1, 1), [], True),
])
def test_selection_labels(qtbot,
                          editable_testing_window,
                          selection,
                          labels,
                          activate_labels):
    qtbot.addWidget(editable_testing_window)
    plot: accgraph.EditablePlotWidget = editable_testing_window.plot

    source: accgraph.UpdateSource = accgraph.UpdateSource()
    curve: accgraph.EditablePlotCurve = plot.addCurve(data_source=source)
    source.new_data(accgraph.CurveData(x=[0, 1, 2, 3, 4], y=[3, 2, 1, 2, 3]))

    curve.selection.points_labeled = activate_labels
    curve.select(selection=selection)
    assert len(curve._selection._point_labels) == len(labels)
    for i, l in enumerate(curve._selection._point_labels):
        assert l.pos().x() == labels[i][0]
        assert l.pos().y() == labels[i][1]


def test_send_curves_state(qtbot,
                           editable_testing_window):
    qtbot.addWidget(editable_testing_window)
    plot: accgraph.EditablePlotWidget = editable_testing_window.plot

    source: accgraph.UpdateSource = accgraph.UpdateSource()
    edit_handler_slot = "accwidgets.graph.UpdateSource.handle_data_model_edit"
    with mock.patch(edit_handler_slot) as mock_handler:
        curve: accgraph.EditablePlotCurve = plot.addCurve(data_source=source)
        source.new_data(accgraph.CurveData(x=[0, 1, 2, 3, 4], y=[3, 2, 1, 2, 3]))

        curve.select(selection=QtCore.QRectF(0, 2.5, 4, 1))
        curve.send_current_state()
        mock_handler.assert_not_called()

        sim_selection_moved(curve._selection, (0.0, 3.0), (0.0, 4.0))
        curve.send_current_state()
        expected = accgraph.CurveData([0, 1, 2, 3, 4], [4, 2, 1, 2, 4])
        mock_handler.assert_called_once_with(expected)

        mock_handler.reset_mock()
        curve.send_current_state()
        mock_handler.assert_not_called()
