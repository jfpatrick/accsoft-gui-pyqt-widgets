"""General Purpose Utility functions."""

import functools
from typing import Optional, Type, Callable, Tuple
import warnings
from unittest.mock import MagicMock

from qtpy import QtGui, QtCore
import accwidgets.graph as accgraph


def warn_always(warning_type: Optional[Type[Warning]] = None) -> Callable:
    """
    Decorator for raising warnings each time they appear. When no warning type
    is passed, all warning types will be risen always.

    Args:
        warning_type: Warning type which should be risen each time
    """
    def deco(f: Callable):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if warning_type is not None and issubclass(warning_type, Warning):
                warnings.simplefilter("always", category=warning_type)
            else:
                warnings.simplefilter("always")
            return_val = f(*args, **kwargs)
            warnings.resetwarnings()
            return return_val
        return wrapper
    return deco


def sim_selection_moved(marker: accgraph.DataSelectionMarker,
                        start: Tuple[float, float],
                        end: Tuple[float, float]) -> None:
    """
    This is a workaround for qttest api for movemouse being buggy:
    https://bugreports.qt.io/browse/QTBUG-5232
    So instead of actually dragging the mouse we will simulate it here
    TODO: switch to proper mouse events as soon as this is fixed

    Args:
        marker: Data Selection Marker of an editable curve
        start: mouse press position of drag event
        end: mouse press release position of drag event
    """
    # Button down press
    press = MagicMock()
    press.button.return_value = QtCore.Qt.LeftButton
    press.isStart.return_value = True
    press.isFinish.return_valaue = False
    press.buttonDownPos.return_value = QtCore.QPointF(*start)
    press.pos.return_value = QtCore.QPointF(*start)
    marker.mouseDragEvent(ev=press)
    # Move
    move = MagicMock()
    move.button.return_value = QtCore.Qt.LeftButton
    move.isStart.return_value = False
    move.isFinish.return_value = False
    move.buttonDownPos.return_value = QtCore.QPointF(*end)
    move.pos.return_value = QtCore.QPointF(*end)
    marker.mouseDragEvent(ev=move)
    # Button release
    release = MagicMock()
    release.button.return_value = QtCore.Qt.LeftButton
    release.isStart.return_value = False
    release.isFinish.return_valaue = True
    release.buttonDownPos.return_value = QtCore.QPointF(*end)
    release.pos.return_value = QtCore.QPointF(*end)
    marker.mouseDragEvent(ev=release)


def assert_qpen_equals(pen_1: QtGui.QPen, pen_2: QtGui.QPen) -> None:
    """Compare the styling of two qpens"""
    assert pen_1.color() == pen_2.color()
    assert pen_1.width() == pen_2.width()
    assert pen_1.style() == pen_2.style()


def assert_qbrush_equals(brush_1: QtGui.QBrush, brush_2: QtGui.QBrush) -> None:
    """Compare the styling of two qbrushs"""
    assert brush_1.color() == brush_2.color()
    assert brush_1.style() == brush_2.style()
