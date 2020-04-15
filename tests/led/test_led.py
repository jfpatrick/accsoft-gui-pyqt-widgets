import pytest
from unittest import mock
from pytestqt.qtbot import QtBot
from typing import cast
from qtpy.QtGui import QColor, QLinearGradient
from qtpy.QtCore import QSize, QPointF
from accwidgets.led.led import Led, _QtDesignerStatus


@pytest.mark.parametrize("api_flags, designer_enum", [
    (Led.Status.ON, _QtDesignerStatus.On),
    (Led.Status.OFF, _QtDesignerStatus.Off),
    (Led.Status.WARNING, _QtDesignerStatus.Warning),
    (Led.Status.ERROR, _QtDesignerStatus.Error),
    (Led.Status.NONE, _QtDesignerStatus.Unknown),
])
def test_designer_enums(api_flags, designer_enum):
    assert api_flags == designer_enum


@pytest.mark.parametrize("incoming_type", [int, Led.Status])
@pytest.mark.parametrize("status, r, g, b", [
    (Led.Status.ON, 72, 191, 13),
    (Led.Status.OFF, 112, 112, 112),
    (Led.Status.WARNING, 193, 178, 15),
    (Led.Status.ERROR, 209, 4, 4),
])
def test_color_for_status_succeeds(incoming_type, status, r, g, b):
    res = Led.Status.color_for_status(incoming_type(status))
    assert isinstance(res, QColor)
    assert cast(QColor, res).red() == r
    assert cast(QColor, res).green() == g
    assert cast(QColor, res).blue() == b


@pytest.mark.parametrize("status, error_msg", [
    (Led.Status.NONE, r"Status 0 does not have corresponding color."),
    (int(Led.Status.NONE), r"Status 0 does not have corresponding color."),
    (Led.Unknown, r"Status 0 does not have corresponding color."),
    (int(Led.Unknown), r"Status 0 does not have corresponding color."),
])
def test_color_for_status_fails(status, error_msg):
    with pytest.raises(ValueError, match=error_msg):
        Led.Status.color_for_status(status)


@pytest.mark.parametrize("slot_name, property_name, slot_arg", [
    ("setColor", "color", QColor()),
    ("setStatus", "status", Led.Status.ERROR),
    ("setStatus", "status", 1),
])
def test_slots(qtbot: QtBot, slot_name, property_name, slot_arg):
    with mock.patch(f"accwidgets.led.led.Led.{property_name}", new_callable=mock.PropertyMock) as mocked_prop:
        widget = Led()
        qtbot.addWidget(widget)
        mocked_prop.assert_not_called()
        getattr(widget, slot_name)(slot_arg)
        mocked_prop.assert_called_with(slot_arg)


@pytest.mark.parametrize("color", [QColor(0, 0, 0), QColor(255, 255, 255), QColor(255, 0, 0)])
def test_color_getter(qtbot: QtBot, color):
    widget = Led()
    qtbot.addWidget(widget)
    widget._color = color
    assert widget.color == color


def test_color_setter_resets_status(qtbot: QtBot):
    widget = Led()
    qtbot.addWidget(widget)
    widget.status = Led.Status.ERROR
    orig_color = widget.color
    widget.color = QColor(0, 0, 0)
    assert widget.color != orig_color
    assert widget.color == QColor(0, 0, 0)
    assert widget.status == Led.Status.NONE


@pytest.mark.parametrize("status", [
    Led.Status.NONE,
    Led.Status.ON,
    Led.Status.OFF,
    Led.Status.WARNING,
    Led.Status.ERROR,
])
def test_status_getter(qtbot: QtBot, status):
    widget = Led()
    qtbot.addWidget(widget)
    widget._status = status
    assert widget.status == status


def test_status_setter(qtbot: QtBot):
    widget = Led()
    qtbot.addWidget(widget)
    orig_color = QColor(0, 0, 0)
    widget.color = orig_color
    widget.status = Led.Status.ERROR
    assert widget.status == Led.Status.ERROR
    assert widget.color != orig_color
    assert widget.color == Led.Status.color_for_status(Led.Status.ERROR)


@pytest.mark.parametrize("alignment", [
    Led.Alignment.CENTER,
    Led.Alignment.TOP,
    Led.Alignment.BOTTOM,
    Led.Alignment.LEFT,
    Led.Alignment.RIGHT,
])
def test_alignment_getter(qtbot: QtBot, alignment):
    widget = Led()
    qtbot.addWidget(widget)
    widget._alignment = alignment
    assert widget.alignment == alignment


@pytest.mark.parametrize("alignment, width, height, edge, x_center, y_center", [
    (Led.Alignment.CENTER, 20, 50, 20, 10, 25),
    (Led.Alignment.CENTER, 50, 20, 20, 25, 10),
    (Led.Alignment.TOP, 20, 50, 20, 10, 10),
    (Led.Alignment.TOP, 50, 20, 20, 25, 10),
    (Led.Alignment.BOTTOM, 20, 50, 20, 10, 40),
    (Led.Alignment.BOTTOM, 50, 20, 20, 25, 10),
    (Led.Alignment.LEFT, 20, 50, 20, 10, 25),
    (Led.Alignment.LEFT, 50, 20, 20, 10, 10),
    (Led.Alignment.RIGHT, 20, 50, 20, 10, 25),
    (Led.Alignment.RIGHT, 50, 20, 20, 40, 10),
])
def test_alignment_setter(qtbot: QtBot, alignment, width, height, edge, x_center, y_center):
    widget = Led()
    qtbot.addWidget(widget)
    widget.resize(width, height)
    old_x_center, old_y_center, old_edge = widget._bubble_center
    assert old_edge == edge
    assert old_x_center == width / 2.0
    assert old_y_center == height / 2.0
    widget.alignment = alignment
    new_x_center, new_y_center, new_edge = widget._bubble_center
    assert new_x_center == x_center
    assert new_y_center == y_center
    assert new_edge == edge


def test_resize_recalculates_both_gradients(qtbot: QtBot):
    widget = Led()
    with mock.patch("accwidgets.led.led.Led._accent_grad", new_callable=mock.PropertyMock, return_value=QColor(0, 0, 0)) as prop_mock:
        qtbot.addWidget(widget)
        prop_mock.assert_not_called()
        with mock.patch.object(widget, "_grad_for_color", return_value=QColor(0, 0, 0)) as method_mock:
            widget.resizeEvent(mock.MagicMock())
            method_mock.assert_called_once()
            prop_mock.assert_called_once()


def test_alignment_setter_recalculates_both_gradients(qtbot: QtBot):
    widget = Led()
    with mock.patch("accwidgets.led.led.Led._accent_grad", new_callable=mock.PropertyMock, return_value=QColor(0, 0, 0)) as prop_mock:
        qtbot.addWidget(widget)
        prop_mock.assert_not_called()
        with mock.patch.object(widget, "_grad_for_color", return_value=QColor(0, 0, 0)) as method_mock:
            widget.alignment = Led.Alignment.BOTTOM
            method_mock.assert_called_once()
            prop_mock.assert_called_once()


def test_size_hint(qtbot: QtBot):
    widget = Led()
    qtbot.addWidget(widget)
    assert widget.minimumSizeHint() == QSize(20, 20)


def test_color_setter_recalculates_main_gradient(qtbot: QtBot):
    widget = Led()
    with mock.patch("accwidgets.led.led.Led._accent_grad", new_callable=mock.PropertyMock, return_value=QColor(0, 0, 0)) as prop_mock:
        qtbot.addWidget(widget)
        prop_mock.assert_not_called()
        with mock.patch.object(widget, "_grad_for_color", return_value=QColor(0, 0, 0)) as method_mock:
            widget.color = QColor(0, 0, 0)
            method_mock.assert_called_once()
            prop_mock.assert_not_called()


@pytest.mark.parametrize("width, height, start, stop", [
    (120, 320, QPointF(60, 100), QPointF(60, 220)),
    (320, 120, QPointF(160, 0), QPointF(160, 120)),
])
def test_grad_for_color(qtbot: QtBot, width, height, start, stop):
    widget = Led()
    qtbot.addWidget(widget)
    widget.resize(width, height)
    grad = widget._grad_for_color(QColor(127, 127, 127))
    assert isinstance(grad, QLinearGradient)
    assert grad.start() == start
    assert grad.finalStop() == stop


@pytest.mark.parametrize("width, height, start, stop", [
    (120, 320, QPointF(60, 106), QPointF(60, 178)),
    (320, 120, QPointF(160, 6), QPointF(160, 78)),
])
def test_accent_grad(qtbot: QtBot, width, height, start, stop):
    widget = Led()
    qtbot.addWidget(widget)
    widget.resize(width, height)
    grad = widget._accent_grad
    assert isinstance(grad, QLinearGradient)
    assert grad.start() == start
    assert grad.finalStop() == stop
