"""General Purpose Utility functions."""

import functools
import warnings
from typing import Optional, Type, Callable, Tuple
from unittest.mock import MagicMock
from qtpy.QtGui import QPen, QBrush, QColor
from qtpy.QtCore import Qt, QPointF
from accwidgets.graph import DataSelectionMarker


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


def sim_selection_moved(marker: DataSelectionMarker,
                        start: Tuple[float, float],
                        end: Tuple[float, float]):
    """
    This is a workaround for qttest api for movemouse being buggy:
    https://bugreports.qt.io/browse/QTBUG-5232
    So instead of actually dragging the mouse we will simulate it here
    TODO: switch to proper mouse events as soon as this is fixed (promised in Qt 6)

    Args:
        marker: Data Selection Marker of an editable curve
        start: mouse press position of drag event
        end: mouse press release position of drag event
    """
    # Button down press
    press = MagicMock()
    press.button.return_value = Qt.LeftButton
    press.isStart.return_value = True
    press.isFinish.return_valaue = False
    press.buttonDownPos.return_value = QPointF(*start)
    press.pos.return_value = QPointF(*start)
    marker.mouseDragEvent(ev=press)
    # Move
    move = MagicMock()
    move.button.return_value = Qt.LeftButton
    move.isStart.return_value = False
    move.isFinish.return_value = False
    move.buttonDownPos.return_value = QPointF(*end)
    move.pos.return_value = QPointF(*end)
    marker.mouseDragEvent(ev=move)
    # Button release
    release = MagicMock()
    release.button.return_value = Qt.LeftButton
    release.isStart.return_value = False
    release.isFinish.return_valaue = True
    release.buttonDownPos.return_value = QPointF(*end)
    release.pos.return_value = QPointF(*end)
    marker.mouseDragEvent(ev=release)


def assert_qcolor_equals(color_1: QColor, color_2: QColor):
    """Compare two QColors by their r,g,b,a values"""
    assert color_1.red() == color_2.red()
    assert color_1.green() == color_2.green()
    assert color_1.blue() == color_2.blue()
    assert color_1.alpha() == color_2.alpha()


def assert_qpen_equals(pen_1: QPen, pen_2: QPen):
    """Compare the styling of two qpens"""
    assert_qcolor_equals(pen_1.color(), pen_2.color())
    assert pen_1.width() == pen_2.width()
    assert pen_1.style() == pen_2.style()


def assert_qbrush_equals(brush_1: QBrush, brush_2: QBrush):
    """Compare the styling of two qbrushs"""
    assert_qcolor_equals(brush_1.color(), brush_2.color())
    assert brush_1.style() == brush_2.style()
