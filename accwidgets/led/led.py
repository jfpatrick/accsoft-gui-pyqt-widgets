from typing import Optional, Union, cast
from enum import IntEnum
from qtpy.QtWidgets import QWidget, QStyleOption, QStyle
from qtpy.QtCore import Qt, QPoint, Property, Q_ENUMS, Slot, QSize
from qtpy.QtGui import QPainter, QBrush, QPen, QPaintEvent, QColor, QLinearGradient, QResizeEvent


class _QtDesignerStatus:
    Unknown = 0
    On = 1
    Off = 2
    Warning = 3
    Error = 4


class Led(QWidget, _QtDesignerStatus):

    Q_ENUMS(_QtDesignerStatus)

    class Status(IntEnum):
        """
        Predefined status that maps to standard colors.
        """
        ON = _QtDesignerStatus.On
        """The equipment is ON/enabled."""
        OFF = _QtDesignerStatus.Off
        """The equipment is OFF/disabled."""
        WARNING = _QtDesignerStatus.Warning
        """There is a non-blocking situation worth knowing about."""
        ERROR = _QtDesignerStatus.Error
        """There is a problem with the controlled equipment or the control chain."""
        NONE = _QtDesignerStatus.Unknown
        """There is no standard meaning associated with the value. This is the default value."""

        @staticmethod
        def color_for_status(status: "Led.Status") -> QColor:
            """
            Predefined color corresponding to a given status.

            Args:
                status: Status to define color based on.
            Returns:
                Corresponding color.
            Raises:
                ValueError: if status is not supported
            """
            if status == Led.Status.ON:
                rgb = 72, 191, 13  # green
            elif status == Led.Status.OFF:
                rgb = 112, 112, 112  # gray
            elif status == Led.Status.WARNING:
                rgb = 193, 178, 15  # yellow
            elif status == Led.Status.ERROR:
                rgb = 209, 4, 4  # red
            else:
                raise ValueError(f"Status {status} does not have corresponding color.")
            return QColor(*rgb)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Basic LED that displays a circle with certain fill color.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._painter = QPainter()
        self._color = QColor(127, 127, 127)
        self._brush = QBrush(self._grad_for_color(self._color))
        self._pen = QPen(Qt.SolidLine)
        self._accent_brush = QBrush(self._accent_grad)
        self._status: Led.Status = Led.Status.NONE

    @Slot("QColor")
    def setColor(self, new_val: QColor):
        """
        Slot for setting color.

        Args:
            new_val: New color.
        """
        self.color = new_val

    @Slot(int)
    def setStatus(self, new_val: Union[int, Status]):
        """
        Slot for setting status.

        Args:
            new_val: New status.
        """
        self.status = cast(Led.Status, new_val)

    def _get_color(self) -> QColor:
        return self._color

    def _set_color_prop_wrapper(self, new_val: QColor):
        self._status = Led.Status.NONE
        self._set_color(new_val)

    color: QColor = Property("QColor", _get_color, _set_color_prop_wrapper)
    """Fill color of the LED."""

    def _get_status(self) -> "Led.Status":
        return self._status

    def _set_status(self, new_val: Union[int, Status]):
        try:
            self._status = Led.Status(new_val)
        except ValueError:
            self._status = Led.Status.NONE
            return
        try:
            color = Led.Status.color_for_status(self._status)
        except ValueError:
            return
        self._set_color(color)

    status: "Led.Status" = Property(_QtDesignerStatus, _get_status, _set_status)
    """Status to switch LED to a predefined color."""

    def paintEvent(self, event: QPaintEvent):
        """
        A paint event is a request to repaint all or part of a widget. It can happen for one of the following reasons:

        * repaint() or update() was invoked,
        * the widget was obscured and has now been uncovered, or
        * many other reasons.

        Args:
            event: Paint event
        """
        self._painter.begin(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, self._painter, self)
        self._painter.setRenderHint(QPainter.Antialiasing)
        self._painter.setBrush(self._brush)
        self._painter.setPen(self._pen)
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        edge = min(width, height)
        r = edge / 2.0 - 2.0 * max(self._pen.widthF(), 1.0)
        self._painter.drawEllipse(QPoint(width / 2.0, height / 2.0), r, r)
        self._painter.setBrush(self._accent_brush)
        self._painter.setPen(QColor(0, 0, 0, 0))
        self._painter.drawEllipse(QPoint(width / 2.0, height / 2.0 - edge * 0.165), edge * 0.4, edge * 0.3)
        self._painter.end()

    def resizeEvent(self, event: QResizeEvent):
        """
        This event handler can be reimplemented in a subclass to receive widget resize events

        Args:
            event: Resize event.
        """
        # Recalculate gradients
        self._brush = QBrush(self._grad_for_color(self._color))
        self._accent_brush = QBrush(self._accent_grad)
        self.update()

    def minimumSizeHint(self) -> QSize:
        """This property holds the recommended minimum size for the widget."""
        return QSize(20, 20)

    def _set_color(self, new_val: QColor):
        self._color = new_val
        self._brush = QBrush(self._grad_for_color(new_val))
        self.update()

    def _grad_for_color(self, color: QColor) -> QLinearGradient:
        edge = min(self.width(), self.height())
        gradient = QLinearGradient(self.width() / 2.0, (self.height() - edge) / 2.0, self.width() / 2.0, (self.height() + edge) / 2.0)
        gradient.setColorAt(0, color)

        # Make a bit brighter using HSV model: https://doc.qt.io/qt-5/qcolor.html#the-hsv-color-model
        h = color.hueF()
        s = color.saturationF()
        v = color.valueF()
        gradient.setColorAt(1, QColor.fromHsvF(h, s * 0.25, min(v * 1.4, 1.0)))
        return gradient

    @property
    def _accent_grad(self) -> QLinearGradient:
        edge = min(self.width(), self.height())
        top_edge = (self.height() - edge) / 2.0
        gradient = QLinearGradient(self.width() / 2.0, top_edge + edge * 0.05, self.width() / 2.0, top_edge + edge * 0.65)
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(1, QColor(255, 255, 255, 5))
        return gradient
