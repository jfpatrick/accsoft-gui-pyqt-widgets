from typing import Optional, Union, cast, Tuple
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


class _QtDesignerAlignment:
    Center = 0
    Top = 1
    Left = 2
    Bottom = 3
    Right = 4


class Led(QWidget, _QtDesignerStatus, _QtDesignerAlignment):

    Q_ENUMS(_QtDesignerStatus, _QtDesignerAlignment)

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

    class Alignment(IntEnum):
        """
        Alignment of the LED bubble inside the widget boundaries, when boundaries are stretched to the larger
        size along one of the axes.
        """
        CENTER = _QtDesignerAlignment.Center
        """Keep the LED in the center (default)."""
        TOP = _QtDesignerAlignment.Top
        """Snap the LED to the top edge, when widget height is greater than width."""
        LEFT = _QtDesignerAlignment.Left
        """Snap the LED to the left edge, when widget width is greater than height."""
        BOTTOM = _QtDesignerAlignment.Bottom
        """Snap the LED to the bottom edge, when widget height is greater than width."""
        RIGHT = _QtDesignerAlignment.Right
        """Snap the LED to the right edge, when widget width is greater than height."""

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Basic LED that displays a circle with certain fill color.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._painter = QPainter()
        self._color = QColor(127, 127, 127)
        self._alignment: Led.Alignment = Led.Alignment.CENTER
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

    color = Property("QColor", _get_color, _set_color_prop_wrapper)
    """
    Fill color of the LED.

    :type: QColor
    """

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

    status = Property(_QtDesignerStatus, _get_status, _set_status)
    """
    Status to switch LED to a predefined color.

    :type: Led.Status
    """

    def _get_alignment(self) -> "Led.Alignment":
        return self._alignment

    def _set_alignment(self, new_val: "Led.Alignment"):
        if self._alignment == new_val:
            return
        self._alignment = new_val
        self._brush = QBrush(self._grad_for_color(self._color))
        self._accent_brush = QBrush(self._accent_grad)
        self.update()

    alignment = Property(_QtDesignerAlignment, _get_alignment, _set_alignment)
    """
    Alignment of the rendered LED inside the widget frame.

    :type: Led.Alignment
    """

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
        x_center, y_center, edge = self._bubble_center
        r = edge / 2.0 - 2.0 * max(self._pen.widthF(), 1.0)
        self._painter.drawEllipse(QPoint(x_center, y_center), r, r)
        self._painter.setBrush(self._accent_brush)
        self._painter.setPen(QColor(0, 0, 0, 0))
        self._painter.drawEllipse(QPoint(x_center, y_center - edge * 0.165), edge * 0.4, edge * 0.3)
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
        x_center, y_center, edge = self._bubble_center
        gradient = QLinearGradient(x_center, y_center - edge / 2.0, x_center, y_center + edge / 2.0)
        gradient.setColorAt(0, color)

        # Make a bit brighter using HSV model: https://doc.qt.io/qt-5/qcolor.html#the-hsv-color-model
        h = color.hueF()
        s = color.saturationF()
        v = color.valueF()
        gradient.setColorAt(1, QColor.fromHsvF(h, s * 0.25, min(v * 1.4, 1.0)))
        return gradient

    @property
    def _accent_grad(self) -> QLinearGradient:
        x_center, y_center, edge = self._bubble_center
        top_edge = y_center - edge / 2.0
        gradient = QLinearGradient(x_center, top_edge + edge * 0.05, x_center, top_edge + edge * 0.65)
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(1, QColor(255, 255, 255, 5))
        return gradient

    @property
    def _bubble_center(self) -> Tuple[float, float, float]:
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        edge = min(width, height)
        x_center = width / 2.0
        y_center = height / 2.0
        if self.alignment == Led.Alignment.LEFT:
            x_center = edge / 2.0
        elif self.alignment == Led.Alignment.RIGHT:
            x_center = width - edge / 2.0
        elif self.alignment == Led.Alignment.TOP:
            y_center = edge / 2.0
        elif self.alignment == Led.Alignment.BOTTOM:
            y_center = height - edge / 2.0
        return x_center, y_center, edge
