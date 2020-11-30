"""
Classes to control the rendering of the timing information on the screen.
"""

import math
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, cast, List, Union
from enum import IntFlag
from qtpy.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSpacerItem
from qtpy.QtGui import (QPaintEvent, QPalette, QColor, QPainter, QFontMetrics, QPixmap, QBrush, QLinearGradient,
                        QShowEvent)
from qtpy.QtCore import Property, Slot, Q_FLAGS, Qt, QRectF, QRect, Q_ENUMS, QSize
from accwidgets.designer_check import is_designer
from ._model import TimingBarModel, TimingBarDomain


class _QtDesignerLabels:
    DateTime = 1 << 0
    TimingDomain = 1 << 1
    User = 1 << 2
    CycleStart = 1 << 3
    LSACycleName = 1 << 4


class _QtDesignerDomain:

    @staticmethod
    def index_of_domain(domain: TimingBarDomain):
        return list(TimingBarDomain.__members__.keys()).index(domain.name)


for domain in TimingBarDomain:
    setattr(_QtDesignerDomain, domain.name, _QtDesignerDomain.index_of_domain(domain))


Color = Union[Qt.GlobalColor, QColor]


@dataclass
class TimingBarPalette:
    """Color scheme that can be used to configure the visual look of the :class:`TimingBar` widget."""

    text: Color
    """Default text color of the timing domain and timestamp labels."""

    error_text: Color
    """Font color of the error message (displayed when communication with XTIM or CTIM devices fails)."""

    highlighted_cycle: Color
    """
    Color of the cycle blocks and font for cycle start, user and LSA name labels for cycles that match the
    :attr:`TimingBar.highlightedUser` property, or when this property is set to :obj:`None`.
    """

    normal_cycle: Color
    """
    Color of the cycle blocks and font for cycle start, user and LSA name labels for cycles that do not match the
    :attr:`TimingBar.highlightedUser` property when it's set.
    """

    timing_mark: Color
    """Background color of the timing mark bar and its related label rendered in the supercycle view."""

    timing_mark_text: Color
    """Font color of the timing mark label rendered in the supercycle view."""

    frame: Color
    """Color of the frame around the widget."""

    bg_top: Color
    """Top color of the background gradient."""

    bg_bottom: Color
    """Bottom color of the background gradient."""

    bg_pattern: Color
    """Color of the dot pattern overlaid over background gradient."""

    bg_top_alt: Color
    """Alternate top color of the background gradient when indicating heartbeat."""

    bg_bottom_alt: Color
    """Alternate bottom color of the background gradient when indicating heartbeat."""

    bg_pattern_alt: Color
    """Alternate color of the dot pattern overlaid over background gradient when indicating heartbeat."""


class TimingBar(QWidget, _QtDesignerLabels, _QtDesignerDomain):

    Q_FLAGS(_QtDesignerLabels)
    Q_ENUMS(_QtDesignerDomain)

    class Labels(IntFlag):
        """Bit mask for various labels that have to be displayed in the widget."""

        DATETIME = _QtDesignerLabels.DateTime
        """Display date and the timestamp in the upper half of the widget."""

        TIMING_DOMAIN = _QtDesignerLabels.TimingDomain
        """Display accelerator name in the upper half of the widget."""

        USER = _QtDesignerLabels.User
        """Display beam user in the upper half of the widget."""

        CYCLE_START = _QtDesignerLabels.CycleStart
        """Display basic periods number when the cycle start in the upper half of the widget."""

        LSA_CYCLE_NAME = _QtDesignerLabels.LSACycleName
        """Display LSA cycle name in the upper half of the widget."""

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 disable_supercycle: bool = False,
                 model: Optional[TimingBarModel] = None):
        """
        Timing bar displays the composition of users and currently played user withing a given timing domain.

        Args:
            parent: Owning object.
            disable_supercycle: Have supercycle diagram initially disabled. This can be reset later via
                                :attr:`renderSuperCycle`.
            model: Model that handles communication with timing devices.
        """
        super().__init__(parent)
        self._labels: TimingBar.Labels = (TimingBar.Labels.DATETIME
                                          | TimingBar.Labels.TIMING_DOMAIN
                                          | TimingBar.Labels.USER
                                          | TimingBar.Labels.CYCLE_START
                                          | TimingBar.Labels.LSA_CYCLE_NAME)
        self._use_heartbeat: bool = True
        self._tick_bkg: bool = False
        self._show_us: bool = False
        self._show_tz: bool = False

        self._palette = TimingBarPalette(text=Qt.black,
                                         error_text=Qt.red,
                                         highlighted_cycle=QColor(31, 66, 221),
                                         normal_cycle=QColor(Qt.darkGray),
                                         timing_mark=QColor(7, 252, 15),
                                         timing_mark_text=QColor(Qt.black),
                                         frame=QColor(178, 178, 178),
                                         bg_top=Qt.white,
                                         bg_bottom=QColor(219, 219, 219),
                                         bg_pattern=QColor(240, 240, 240),
                                         bg_top_alt=QColor(252, 252, 226),
                                         bg_bottom_alt=QColor(243, 243, 194),
                                         bg_pattern_alt=QColor(239, 234, 170))

        self._canvas = TimingBarCanvas(self)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self._canvas)
        main_layout.setContentsMargins(5, self._TOP_PADDING, 5, self._BOTTOM_PADDING)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._lbl_datetime = QLabel()
        self._lbl_datetime.setToolTip("Date and time of the last update")
        font = self._lbl_datetime.font()
        font.setPointSize(8)
        self._lbl_datetime.setFont(font)
        self._lbl_domain = QLabel()
        self._lbl_domain.setToolTip("Timing domain")
        font = self._lbl_domain.font()
        font.setBold(True)
        font.setPointSize(12)
        self._lbl_domain.setFont(font)
        self._lbl_user = QLabel()
        self._lbl_user.setToolTip("Beam user")
        font = self._lbl_user.font()
        font.setBold(True)
        self._lbl_user.setFont(font)
        self._lbl_beam_offset = QLabel()
        self._lbl_beam_offset.setToolTip("Cycle start (in basic periods)")
        font = self._lbl_beam_offset.font()
        font.setBold(True)
        self._lbl_beam_offset.setFont(font)
        self._sep_lsa = QFrame()
        self._sep_lsa.setFrameStyle(QFrame.VLine)
        self._lbl_lsa_name = QLabel()
        self._lbl_lsa_name.setToolTip("LSA cycle name")
        font = self._lbl_lsa_name.font()
        font.setBold(True)
        self._lbl_lsa_name.setFont(font)

        self._update_alternate_indication()

        h_layout = QHBoxLayout()
        h_layout.addWidget(self._lbl_domain)
        h_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        h_layout.addWidget(self._lbl_datetime)
        h_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        h_layout.addWidget(self._lbl_beam_offset)
        h_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Maximum, QSizePolicy.Fixed))
        h_layout.addWidget(self._lbl_user)
        h_layout.addWidget(self._sep_lsa)
        h_layout.addWidget(self._lbl_lsa_name)
        h_layout.setSpacing(5)
        h_layout.setContentsMargins(10, TimingBarCanvas._LABEL_TOP_MARGIN, 10, 0)

        layout = QVBoxLayout()
        layout.addLayout(h_layout)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)

        self._highlighted_user: Optional[str] = None
        self._model_error: Optional[str] = None
        self._model = model or TimingBarModel()
        self._connect_model(self._model)

        self._canvas.setLayout(layout)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored))

        self._update_label_visibility()
        if not disable_supercycle:
            self.showSuperCycle()

    def _get_model(self) -> TimingBarModel:
        return self._model

    def _set_model(self, model: TimingBarModel):
        if model == self._model:
            return

        if self._model:
            self._disconnect_model(self._model)
        self._model = model
        self._connect_model(self._model)

    model = property(fget=_get_model, fset=_set_model)
    """
    Model that handles communication with timing devices.

    When assigning a new model, its ownership is transferred to the widget.
    """

    def _get_labels(self) -> "TimingBar.Labels":
        return self._labels

    def _set_labels(self, new_val: "TimingBar.Labels"):
        self._labels = new_val
        self._update_label_visibility()

    labels: "TimingBar.Labels" = Property(_QtDesignerLabels, _get_labels, _set_labels)
    """Bit mask for various labels that have to be displayed in the widget. By default, all the labels are enabled."""

    def _get_indicate_heartbeat(self) -> bool:
        return self._use_heartbeat

    def _set_indicate_heartbeat(self, new_val: bool):
        self._use_heartbeat = new_val
        self._update_alternate_indication()

    indicateHeartbeat: bool = Property(bool, fget=_get_indicate_heartbeat, fset=_set_indicate_heartbeat)
    """Flag to alternate background color on every new tick from the timing system. Defaults to :obj:`True`."""

    def _get_highlighted_user(self) -> Optional[str]:
        return self._highlighted_user

    def _set_highlighted_user(self, new_val: Optional[str]):
        self._highlighted_user = new_val
        self._redraw()

    highlightedUser: Optional[str] = Property(str, fget=_get_highlighted_user, fset=_set_highlighted_user)
    """
    Optional timing user that can be set to highlight cycles with the matching user property. When not set,
    all cycles will be rendered in highlighted color. Default value is :obj:`None`.

    In the default color scheme, highlighted users are blue, while others are gray.
    """

    def _get_render_supercycle(self) -> bool:
        return self._canvas.show_supercycle

    def _set_render_supercycle(self, new_val: bool):
        if new_val == self.renderSuperCycle:
            return
        if new_val:
            self.showSuperCycle()
        else:
            self.hideSuperCycle()

    renderSuperCycle: bool = Property(bool, fget=_get_render_supercycle, fset=_set_render_supercycle)
    """
    Flag to enable or disable rendering of the supercycle structure. When disabled, only the top row of the
    labels remains and the widget shrinks in height.
    """

    def _get_show_us(self) -> bool:
        return self._show_us

    def _set_show_us(self, new_val: bool):
        if new_val == self._show_us:
            return
        self._show_us = new_val
        self._on_new_timing_info(False)

    showMicroSeconds: bool = Property(bool, fget=_get_show_us, fset=_set_show_us)
    """
    Use microsecond precision in the timestamp label. Defaults to :obj:`False`.
    """

    def _get_show_tz(self) -> bool:
        return self._show_tz

    def _set_show_tz(self, new_val: bool):
        if new_val == self._show_tz:
            return
        self._show_tz = new_val
        self._on_new_timing_info(False)

    showTimeZone: bool = Property(bool, fget=_get_show_tz, fset=_set_show_tz)
    """
    Display timezone in the timestamp label. Defaults to :obj:`False`.
    """

    def _get_palette(self) -> TimingBarPalette:
        # Always give a copy of palette, so that if it's modified externally,
        # it has to be passed through a setter to have effect
        return copy(self._palette)

    def _set_palette(self, palette: TimingBarPalette):
        if palette == self._palette:
            return
        self._palette = palette
        self._canvas.update_gradients()
        self._redraw()

    color_palette = property(fget=_get_palette, fset=_set_palette)
    """
    Color scheme that can be used to configure the visual look of the widget.

    When accessed, a copy of the palette is returned, therefore direct modification has no effect and instead the
    user has to assign the property to the new palette. This approach is inspired by Qt's :attr:`QWidget.palette`.
    Using Qt palette on timing bar is discouraged, as it will not be able to cover all the styling of custom painting.
    """

    def _get_domain(self) -> TimingBarDomain:
        if is_designer():
            # Extract an index
            return _QtDesignerDomain.index_of_domain(self.model.domain)
        return self.model.domain

    def _set_domain(self, new_val: TimingBarDomain):
        if isinstance(new_val, int) or isinstance(new_val, _QtDesignerDomain):
            val = list(TimingBarDomain.__members__.values())[new_val]
            new_val = TimingBarDomain(val)
        self.model.domain = new_val

    domain: TimingBarDomain = Property(_QtDesignerDomain, fget=_get_domain, fset=_set_domain)
    """
    Currently displayed timing domain. Resetting this value will lead to termination of the active connections
    to XTIM and CTIM devices and creation of the new ones.

    This is a convenience property to access timing domain that actually belongs to the :attr:`model` (and can
    be modified there). It exists on the widget level for the sake of allowing this configuration in Qt Designer.
    """

    def _get_timing_mark_color(self) -> QColor:
        return self._palette.timing_mark

    def _set_timing_mark_color(self, new_color: QColor):
        palette = self.color_palette
        palette.timing_mark = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    timingMarkColor: Color = Property(QColor, fget=_get_timing_mark_color, fset=_set_timing_mark_color, designable=True)
    """
    Background color of the timing mark bar and its related label rendered in the supercycle view.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_timing_mark_text_color(self) -> QColor:
        return self._palette.timing_mark_text

    def _set_timing_mark_text_color(self, new_color: QColor):
        palette = self.color_palette
        palette.timing_mark_text = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    timingMarkTextColor: Color = Property(QColor, fget=_get_timing_mark_text_color, fset=_set_timing_mark_text_color, designable=True)
    """
    Font color of the timing mark label rendered in the supercycle view.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_normal_cycle_color(self) -> QColor:
        return self._palette.normal_cycle

    def _set_normal_cycle_color(self, new_color: QColor):
        palette = self.color_palette
        palette.normal_cycle = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    normalCycleColor: Color = Property(QColor, fget=_get_normal_cycle_color, fset=_set_normal_cycle_color, designable=True)
    """
    Color of the cycle blocks and font for cycle start, user and LSA name labels for cycles that do not match the
    :attr:`highlightedUser` property when it's set.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_highlighted_cycle_color(self) -> QColor:
        return self._palette.highlighted_cycle

    def _set_highlighted_cycle_color(self, new_color: QColor):
        palette = self.color_palette
        palette.highlighted_cycle = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    highlightedCycleColor: Color = Property(QColor, fget=_get_highlighted_cycle_color, fset=_set_highlighted_cycle_color, designable=True)
    """
    Color of the cycle blocks and font for cycle start, user and LSA name labels for cycles that match the
    :attr:`highlightedUser` property, or when this property is set to :obj:`None`.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_bg_pattern_color(self) -> QColor:
        return self._palette.bg_pattern

    def _set_bg_pattern_color(self, new_color: QColor):
        palette = self.color_palette
        palette.bg_pattern = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    backgroundPatternColor: Color = Property(QColor, fget=_get_bg_pattern_color, fset=_set_bg_pattern_color, designable=True)
    """
    Color of the dot pattern overlaid over background gradient.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_bg_pattern_alt_color(self) -> QColor:
        return self._palette.bg_pattern_alt

    def _set_bg_pattern_alt_color(self, new_color: QColor):
        palette = self.color_palette
        palette.bg_pattern_alt = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    backgroundPatternAltColor: Color = Property(QColor, fget=_get_bg_pattern_alt_color, fset=_set_bg_pattern_alt_color, designable=True)
    """
    Alternate color of the dot pattern overlaid over background gradient when indicating heartbeat.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_bg_top_color(self) -> QColor:
        return self._palette.bg_top

    def _set_bg_top_color(self, new_color: QColor):
        palette = self.color_palette
        palette.bg_top = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    backgroundTopColor: Color = Property(QColor, fget=_get_bg_top_color, fset=_set_bg_top_color, designable=True)
    """
    Top color of the background gradient.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_bg_bottom_color(self) -> QColor:
        return self._palette.bg_bottom

    def _set_bg_bottom_color(self, new_color: QColor):
        palette = self.color_palette
        palette.bg_bottom = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    backgroundBottomColor: Color = Property(QColor, fget=_get_bg_bottom_color, fset=_set_bg_bottom_color, designable=True)
    """
    Bottom color of the background gradient.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_bg_top_alt_color(self) -> QColor:
        return self._palette.bg_top_alt

    def _set_bg_top_alt_color(self, new_color: QColor):
        palette = self.color_palette
        palette.bg_top_alt = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    backgroundTopAltColor: Color = Property(QColor, fget=_get_bg_top_alt_color, fset=_set_bg_top_alt_color, designable=True)
    """
    Alternate top color of the background gradient when indicating heartbeat.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_bg_bottom_alt_color(self) -> QColor:
        return self._palette.bg_bottom_alt

    def _set_bg_bottom_alt_color(self, new_color: QColor):
        palette = self.color_palette
        palette.bg_bottom_alt = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    backgroundBottomAltColor: Color = Property(QColor, fget=_get_bg_bottom_alt_color, fset=_set_bg_bottom_alt_color, designable=True)
    """
    Alternate bottom color of the background gradient when indicating heartbeat.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_text_color(self) -> QColor:
        return self._palette.text

    def _set_text_color(self, new_color: QColor):
        palette = self.color_palette
        palette.text = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    textColor: Color = Property(QColor, fget=_get_text_color, fset=_set_text_color, designable=True)
    """
    Default text color of the timing domain and timestamp labels.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_error_text_color(self) -> QColor:
        return self._palette.error_text

    def _set_error_text_color(self, new_color: QColor):
        palette = self.color_palette
        palette.error_text = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    errorTextColor: Color = Property(QColor, fget=_get_error_text_color, fset=_set_error_text_color, designable=True)
    """
    Font color of the error message (displayed when communication with XTIM or CTIM devices fails).

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    def _get_frame_color(self) -> QColor:
        return self._palette.frame

    def _set_frame_color(self, new_color: QColor):
        palette = self.color_palette
        palette.frame = new_color
        self.color_palette = palette

    # Property must stay designable in order to react to QSS styling
    frameColor: Color = Property(QColor, fget=_get_frame_color, fset=_set_frame_color, designable=True)
    """
    Color of the frame around the widget.

    This property exists only for ability to restyle the widget with QSS. For programmatic styling, it is suggested to
    set :attr:`color_palette` property.
    """

    @Slot()
    def showSuperCycle(self):
        """
        Display supercycle part of the bar if it was hidden previously.

        This method can be used as a slot.
        """
        if self.renderSuperCycle:
            return
        spacer = QSpacerItem(0, TimingBarCanvas._SUPERCYCLE_HEIGHT, QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._canvas.layout().addSpacerItem(spacer)
        self._canvas.show_supercycle = True
        self._canvas.update()
        self._update_widget_height()

    @Slot()
    def hideSuperCycle(self):
        """
        Hide supercycle part of the bar if it was shown previously.

        This method can be used as a slot.
        """
        if not self.renderSuperCycle:
            return
        spacer_item = self._canvas.layout().itemAt(1)
        self._canvas.layout().removeItem(spacer_item)
        self._canvas.show_supercycle = False
        self._canvas.update()
        self._update_widget_height()

    @Slot()
    def toggleSuperCycle(self):
        """
        Toggle the display of the supercycle part of the bar and related widget's :attr:`renderSuperCycle` value.

        This method can be used as a slot.
        """
        if self.renderSuperCycle:
            self.hideSuperCycle()
        else:
            self.showSuperCycle()

    def showEvent(self, event: QShowEvent):
        """
        This event handler is reimplemented widget show events so that model initiates RDA connections to XTIM
        devices when shown for the first time.

        Non-spontaneous show events are sent to widgets immediately before they are shown. The spontaneous show
        events of windows are delivered afterwards.

        Note: A widget receives spontaneous show and hide events when its mapping status is changed by the window
        system, e.g. a spontaneous hide event when the user minimizes the window, and a spontaneous show event when
        the window is restored again. After receiving a spontaneous hide event, a widget is still considered visible
        in the sense of :meth:`isVisible`.

        Args:
            event: Show event.
        """
        super().showEvent(event)
        if not event.spontaneous() and not self._model.activated:
            self._model.activate()  # Initialize japc subscriptions

    def minimumSizeHint(self) -> QSize:
        """
        If the value of this property is an invalid size, no minimum size is recommended.  The default
        implementation of :meth:`QWidget.minimumSizeHint` returns an invalid size if there is no layout for
        this widget, and returns the layout's minimum size otherwise. Most built-in widgets reimplement
        :meth:`QWidget.minimumSizeHint`.

        :class:`QLayout` will never resize a widget to a size smaller than the minimum size hint unless
        :meth:`minimumSize` is set or the size policy is set to :attr:`QSizePolicy.Ignore`. If
        :meth:`minimumSize` is set, the minimum size hint will be ignored.

        Returns:
            Recommended minimum size for the widget.
        """
        min_non_supercycle_width = (TimingBarCanvas._NON_SUPERCYCLE_BP_COUNT * 2
                                    + TimingBarCanvas._CYCLE_BAR_MARGIN_LEFT
                                    + TimingBarCanvas._CYCLE_BAR_MARGIN_RIGHT)
        desired_width = max(super().minimumSizeHint().width(), min_non_supercycle_width)
        return QSize(desired_width, self.minimumHeight())

    def _update_label_visibility(self):
        has_error = self._model.has_error
        config = self.labels
        self._lbl_datetime.setVisible(not has_error and (config & TimingBar.Labels.DATETIME) > 0)
        self._lbl_domain.setVisible(not has_error and (config & TimingBar.Labels.TIMING_DOMAIN) > 0)
        self._lbl_beam_offset.setVisible(not has_error and (config & TimingBar.Labels.CYCLE_START) > 0)
        self._lbl_user.setVisible(not has_error and (config & TimingBar.Labels.USER) > 0)
        self._lbl_lsa_name.setVisible(not has_error and (config & TimingBar.Labels.LSA_CYCLE_NAME) > 0)
        self._sep_lsa.setVisible(not has_error and (config & TimingBar.Labels.LSA_CYCLE_NAME) > 0 and len(self._lbl_lsa_name.text()) > 0)

    def _connect_model(self, model: TimingBarModel):
        model.setParent(self)
        model.timingUpdateReceived.connect(self._on_new_timing_info)
        model.timingErrorReceived.connect(self._on_model_error)
        self._lbl_domain.setText(model.domain.value)
        model.domainNameChanged.connect(self._lbl_domain.setText)

    def _disconnect_model(self, model: TimingBarModel):
        model.timingUpdateReceived.disconnect(self._on_new_timing_info)
        model.timingErrorReceived.disconnect(self._on_model_error)
        model.domainNameChanged.disconnect(self._lbl_domain.setText)
        model.setParent(None)
        self._lbl_domain.clear()

    def _on_new_timing_info(self, basic_period_advanced: bool):
        self.setToolTip(None)  # Assume no error

        info = self._model.last_info
        if info:
            time_fmt = "%Y-%m-%d  %H:%M:%S"
            if self.showMicroSeconds:
                time_fmt += ".%f"
            if self.showTimeZone:
                time_fmt += " %Z"
            self._lbl_datetime.setText(info.timestamp.strftime(time_fmt))
            self._lbl_lsa_name.setText(info.lsa_name)
            self._lbl_user.setText(info.user)
            self._lbl_beam_offset.setNum(info.offset + 1)
        else:
            self._lbl_datetime.setText("")
            self._lbl_lsa_name.setText("")
            self._lbl_user.setText("")
            self._lbl_beam_offset.setText("")

        self._update_label_visibility()

        if basic_period_advanced:
            self._tick_bkg = not self._tick_bkg
            self._update_alternate_indication()
        self._redraw()

    def _on_model_error(self, error: str):
        self.setToolTip(error)
        self._update_label_visibility()
        self._canvas.set_alternate_color(False)
        self._canvas.update()

    def _redraw(self):
        self._canvas.update()

        info = self.model.last_info
        if info is None:
            # We still must continue running this method, with some assumed color (because it may influence, e.g.
            # an initial color, before the first update comes in
            color = self._palette.normal_cycle
        else:
            color = self._color_for_cycle(info.user, force_active=not self.model.is_supercycle_mode)

        def get_color_name(col: Color) -> str:
            if isinstance(col, Qt.GlobalColor):
                # GlobalColor has been used (e.g. Qt.black)
                col = QColor(col)
            return cast(QColor, col).name()

        tooltip_base = self.palette().color(QPalette.ToolTipBase)
        tooltip_text = self.palette().color(QPalette.ToolTipText)
        tooltip_style = f"QToolTip {{background-color: {tooltip_base.name()}; color: {tooltip_text.name()};}}"
        cycle_style = f"QLabel{{ background-color: transparent; color: {get_color_name(color)};}}" + tooltip_style

        # We must keep the styling through stylesheets, because they have a priority over
        # palettes. And we don't want external stylesheet that modifies all QLabels to
        # destroy our styling.
        self._lbl_user.setStyleSheet(cycle_style)
        self._lbl_beam_offset.setStyleSheet(cycle_style)
        self._lbl_lsa_name.setStyleSheet(cycle_style)
        self._sep_lsa.setStyleSheet(f"QFrame{{ background-color: transparent; color: {get_color_name(color)};}}" + tooltip_style)

        normal_style = f"QLabel{{ background-color: transparent; color: {get_color_name(self._palette.text)};}}" + tooltip_style
        self._lbl_datetime.setStyleSheet(normal_style)
        self._lbl_domain.setStyleSheet(normal_style)

    def _update_alternate_indication(self):
        self._canvas.set_alternate_color(self.indicateHeartbeat and self._tick_bkg)

    def _update_widget_height(self):
        height = self._canvas.maximumHeight() + self._TOP_PADDING + self._BOTTOM_PADDING
        self.setFixedHeight(height)
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)

    def _color_for_cycle(self, name: str, force_active: bool = False):
        return (self._palette.highlighted_cycle if force_active or not self.highlightedUser or name == self.highlightedUser
                else self._palette.normal_cycle)

    _TOP_PADDING = 0
    _BOTTOM_PADDING = 2


class TimingBarCanvas(QWidget):

    def __init__(self, parent: TimingBar):
        super().__init__(parent)
        self._show_supercycle = False
        self._label_font = self.font()
        self._label_font.setPointSize(7)
        self._error_font = self.font()
        self._error_font.setPointSize(self._FONT_SIZE_ERROR_COLLAPSED)
        self._error_font.setBold(True)
        self._use_alternate_color = False
        self._pixmap = QPixmap(str(Path(__file__).parent / "border.png"))
        self.show_supercycle = self._show_supercycle  # Trigger constraints
        self._normal_gradient = QLinearGradient(0, 0, 0, 0)
        self._alt_gradient = QLinearGradient(0, 0, 0, 0)
        self.update_gradients()
        self.set_alternate_color(False)

    @property
    def show_supercycle(self) -> bool:
        return self._show_supercycle

    @show_supercycle.setter
    def show_supercycle(self, new_val: bool):
        self._show_supercycle = new_val
        height = self._FRAME_FULL_HEIGHT if new_val else self._FRAME_MINIMIZED_HEIGHT
        self._error_font.setPointSize(self._FONT_SIZE_ERROR_FULL if new_val else self._FONT_SIZE_ERROR_COLLAPSED)
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        self.setFixedHeight(height)

    def set_alternate_color(self, alternate: bool):
        self._use_alternate_color = alternate
        self.update()

    def update_gradients(self):
        self._normal_gradient.setColorAt(0, self._bar._palette.bg_top)
        self._normal_gradient.setColorAt(1, self._bar._palette.bg_bottom)
        self._alt_gradient.setColorAt(0, self._bar._palette.bg_top_alt)
        self._alt_gradient.setColorAt(1, self._bar._palette.bg_bottom_alt)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        self._draw_background(painter, event.rect())
        if self._bar.model.has_error:
            self._draw_error(painter, event.rect())
        elif self.show_supercycle:
            self._draw_supercycle(painter, event.rect())
        self._draw_borders(painter, event.rect())

    def _draw_background(self, painter: QPainter, updated_rect: QRect):
        width = self.width()
        height = self.height()
        self._normal_gradient.setFinalStop(0, height)
        self._alt_gradient.setFinalStop(0, height)

        # We can't rely on the standard background drawing through palette, as it sometimes is not respected,
        # e.g. when widget placed into QToolbar, thus enforcing the pen
        painter.setPen(Qt.NoPen)

        pattern_brush = QBrush(self._bar._palette.bg_pattern_alt if self._use_alternate_color else self._bar._palette.bg_pattern)
        pattern_brush.setStyle(Qt.Dense6Pattern)
        bkg_brush = QBrush(self._alt_gradient if self._use_alternate_color else self._normal_gradient)

        def paint_rect(rect: QRect):
            painter.setBrush(bkg_brush)
            painter.drawRect(rect)
            painter.setBrush(pattern_brush)
            painter.drawRect(rect)

        def paint_rounder_rect(x: float, y: float, w: float, h: float, radius: float = self._FRAME_CORNER_RADIUS):
            rect = QRect(x, y, w, h)
            painter.setBrush(bkg_brush)
            painter.drawRoundedRect(rect, radius, radius)
            painter.setBrush(pattern_brush)
            painter.drawRoundedRect(rect, radius, radius)

        # 9 regions for rounded corners

        # Top left corner
        target_rect = QRect(0, 0, self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS)
        if target_rect.intersects(updated_rect):
            # Draw 4x size, for the rounded corners
            paint_rounder_rect(0, 0, self._FRAME_CORNER_RADIUS * 2, self._FRAME_CORNER_RADIUS * 2)

        # Top right corner
        target_rect = QRect(width - self._FRAME_CORNER_RADIUS, 0, self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS)
        if target_rect.intersects(updated_rect):
            # Draw 4x size, for the rounded corners
            paint_rounder_rect(width - self._FRAME_CORNER_RADIUS * 2, 0, self._FRAME_CORNER_RADIUS * 2, self._FRAME_CORNER_RADIUS * 2)

        # Bottom left corner
        target_rect = QRect(0, height - self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS)
        if target_rect.intersects(updated_rect):
            # Draw 4x size, for the rounded corners
            paint_rounder_rect(0, height - self._FRAME_CORNER_RADIUS * 2, self._FRAME_CORNER_RADIUS * 2, self._FRAME_CORNER_RADIUS * 2)

        # Bottom right corner
        target_rect = QRect(width - self._FRAME_CORNER_RADIUS, height - self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS)
        if target_rect.intersects(updated_rect):
            # Draw 4x size, for the rounded corners
            paint_rounder_rect(width - self._FRAME_CORNER_RADIUS * 2, height - self._FRAME_CORNER_RADIUS * 2, self._FRAME_CORNER_RADIUS * 2, self._FRAME_CORNER_RADIUS * 2)

        def draw_rect(x: float, y: float, w: float, h: float):
            rect = QRect(x, y, w, h)
            intersection = rect.intersected(updated_rect)
            if intersection.isValid() and not intersection.isEmpty():
                paint_rect(intersection)

        # Top-to-bottom edge
        draw_rect(self._FRAME_CORNER_RADIUS, 0, width - self._FRAME_CORNER_RADIUS * 2, height)

        # Left edge
        draw_rect(0, self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS, height - self._FRAME_CORNER_RADIUS * 2)

        # Right edge
        draw_rect(width - self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS, height - self._FRAME_CORNER_RADIUS * 2)

    def _draw_supercycle(self, painter: QPainter, updated_rect: QRect):
        # Gather information from the model
        bar = self._bar
        model = bar.model
        active_bp = model.current_basic_period
        cycles_count = model.cycle_count
        width_bp = model.supercycle_duration
        if model.is_supercycle_mode:
            active_cycle = model.current_cycle_index
        else:
            # We should not exceed basic periods beyond the maximum amount that we can show
            active_cycle = active_bp  # Cycles are of length 1, so cycle corresponds to bp here

        # Exit if there's nothing to draw
        if cycles_count == 0 or width_bp <= 0:
            return

        # Draw
        width = self.width()
        height = self.height()

        width_px = width - self._CYCLE_BAR_MARGIN_LEFT - self._CYCLE_BAR_MARGIN_RIGHT - (cycles_count - 1) * self._CYCLE_BAR_SPACING
        height_px = height - self._CYCLE_BAR_MARGIN_TOP - self._CYCLE_BAR_MARGIN_BOTTOM
        px_per_bp = width_px / width_bp

        def draw_rect(rect: QRect):
            intersection = rect.intersected(updated_rect)
            if intersection.isValid() and not intersection.isEmpty():
                painter.drawRect(intersection)
                return True
            return False

        painter.setPen(Qt.NoPen)

        def draw_cycle(cycle_offset: int, duration: int, idx: int, user: str = "", force_active_color: bool = False):
            is_last_cycle = idx == cycles_count - 1
            offset = self._CYCLE_BAR_MARGIN_LEFT + math.ceil(cycle_offset * px_per_bp + idx * self._CYCLE_BAR_SPACING)
            if is_last_cycle:
                # Stretch last bit to the right edge, to account of fraction imperfections in px_per_bp rounding
                cycle_width = width - self._CYCLE_BAR_MARGIN_RIGHT - offset
            else:
                cycle_width = math.floor(px_per_bp * duration)
            if idx == active_cycle:
                cycle_height = height_px
            else:
                cycle_height = self._CYCLE_BAR_NORMAL_HEIGHT
            cycle_rect = QRect(offset, self._CYCLE_BAR_MARGIN_TOP, max(1, cycle_width), cycle_height)
            brush = bar._color_for_cycle(user, force_active=force_active_color)
            painter.setBrush(brush)
            draw_rect(cycle_rect)

        if model.is_supercycle_mode:
            # Draw cycles from the BCD structure
            for idx, cycle in enumerate(model.supercycle):
                draw_cycle(cycle_offset=cycle.offset,
                           duration=cycle.duration,
                           idx=idx,
                           user=cycle.user)
        else:
            # Draw uniformly distributed cycles with length of 1 basic period (do not draw cycles that did not happen yet)
            for idx in range(active_bp + 1):
                draw_cycle(cycle_offset=idx,
                           duration=1,
                           idx=idx,
                           force_active_color=True)

        if active_bp != -1:
            label = f"{active_bp + 1}/{width_bp}"
            metrics = QFontMetrics(self.font())
            text_width = metrics.horizontalAdvance(label)
            text_height = metrics.height() - 1
            # time mark will be in the middle of the basic period block
            time_mark_anchor = self._CYCLE_BAR_MARGIN_LEFT + round((active_bp + 0.5) * px_per_bp - self._TIME_MARK_WIDTH / 2) + active_cycle * self._CYCLE_BAR_SPACING
            text_x = time_mark_anchor + self._TIME_MARK_LABEL_OFFSET
            if text_x + text_width > width - self._CYCLE_BAR_MARGIN_RIGHT:
                text_x = time_mark_anchor - text_width - self._TIME_MARK_LABEL_OFFSET
            text_y = int(self._CYCLE_BAR_MARGIN_TOP + (height_px - text_height) / 2)
            time_marker_rect = QRect(time_mark_anchor, 0, self._TIME_MARK_WIDTH, height)
            painter.setBrush(bar._palette.timing_mark)
            painter.setPen(Qt.NoPen)
            draw_rect(time_marker_rect)
            text_rect = QRect(text_x, text_y, text_width, text_height)
            conn_x_left = min(text_x, time_mark_anchor)
            conn_x_right = max(text_x, time_mark_anchor)
            time_mark_conn_rect = QRect(conn_x_left, text_rect.bottom() - self._TIME_MARK_WIDTH + 1, conn_x_right - conn_x_left, self._TIME_MARK_WIDTH)
            draw_rect(time_mark_conn_rect)
            if draw_rect(text_rect):
                painter.setPen(Qt.black)
                painter.setFont(self._label_font)
                painter.drawText(text_rect, Qt.AlignCenter, label)

    def _draw_borders(self, painter: QPainter, updated_rect: QRect):
        width = self.width()
        height = self.height()

        def create_fragment(tx, ty, sx, sy, w, h, tw=None, th=None) -> Optional[QPainter.PixmapFragment]:
            # If target width (tw) and height (th) are not defined, copy 1-to-1 from pixmap
            # Otherwise, copy a chunk and stretch it. This is an optimization to not create thousands of fragments
            # of 1px width or 1px height, when drawing edge shadows. Rather scale 1px pixmap area into a single
            # large target fragment
            target_rect = QRectF(tx, ty, w if tw is None else tw, h if th is None else th)
            # Must operate on QRectF, for scaling of pixmap fragments to succeed without visual artifacts (gaps)
            intersection: QRectF = target_rect.intersected(QRectF(updated_rect))
            if not intersection.isValid() or intersection.isEmpty():
                return None
            not_scaled_target_rect = QRect(tx, ty, w, h)
            not_scaled_intersection: QRect = not_scaled_target_rect.intersected(updated_rect)
            if not not_scaled_intersection.isValid() or not_scaled_intersection.isEmpty():
                dx = 0
                dy = 0
                dw = 0
                dh = 0
            else:
                dx = max(0, intersection.x() - target_rect.x())
                dy = max(0, intersection.y() - target_rect.y())
                dw = max(0, target_rect.right() - intersection.right()) + dx
                dh = max(0, target_rect.bottom() - intersection.bottom()) + dy
            sx += dx
            sy += dy
            sw = w - dw
            sh = h - dh
            scale_x = intersection.width() / sw if tw is not None else 1.0
            scale_y = intersection.height() / sh if th is not None else 1.0
            return QPainter.PixmapFragment.create(intersection.center(), QRectF(sx, sy, sw, sh), scale_x, scale_y)

        fragments: List[QPainter.PixmapFragment] = []

        def append_if_created(frag: Optional[QPainter.PixmapFragment]):
            if frag:
                fragments.append(frag)

        # Top left corner
        append_if_created(create_fragment(tx=0, ty=0,
                                          sx=0, sy=0,
                                          w=self._PIXMAP_FRAME_WIDTH, h=self._PIXMAP_FRAME_WIDTH))
        # Bottom left corner
        append_if_created(create_fragment(tx=0, ty=height - self._PIXMAP_FRAME_WIDTH,
                                          sx=0, sy=self._PIXMAP_HEIGHT - self._PIXMAP_FRAME_WIDTH,
                                          w=self._PIXMAP_FRAME_WIDTH, h=self._PIXMAP_FRAME_WIDTH))
        # Top right corner
        append_if_created(create_fragment(tx=width - self._PIXMAP_FRAME_WIDTH, ty=0,
                                          sx=self._PIXMAP_WIDTH - self._PIXMAP_FRAME_WIDTH, sy=0,
                                          w=self._PIXMAP_FRAME_WIDTH, h=self._PIXMAP_FRAME_WIDTH))
        # Bottom right corner
        append_if_created(create_fragment(tx=width - self._PIXMAP_FRAME_WIDTH, ty=height - self._PIXMAP_FRAME_WIDTH,
                                          sx=self._PIXMAP_WIDTH - self._PIXMAP_FRAME_WIDTH, sy=self._PIXMAP_HEIGHT - self._PIXMAP_FRAME_WIDTH,
                                          w=self._PIXMAP_FRAME_WIDTH, h=self._PIXMAP_FRAME_WIDTH))

        top_updated_edge = max(self._PIXMAP_FRAME_WIDTH, updated_rect.top())
        bottom_updated_edge = min(height - self._PIXMAP_FRAME_WIDTH, updated_rect.bottom())
        edge_height = bottom_updated_edge - top_updated_edge
        if edge_height > 0:
            # Left edge
            append_if_created(create_fragment(tx=0, ty=top_updated_edge, th=edge_height,
                                              sx=0, sy=self._PIXMAP_FRAME_WIDTH,
                                              w=self._PIXMAP_FRAME_WIDTH, h=1))
            # Right edge
            append_if_created(create_fragment(tx=width - self._PIXMAP_FRAME_WIDTH, ty=top_updated_edge, th=edge_height,
                                              sx=self._PIXMAP_WIDTH - self._PIXMAP_FRAME_WIDTH, sy=self._PIXMAP_FRAME_WIDTH,
                                              w=self._PIXMAP_FRAME_WIDTH, h=1))

        left_updated_edge = max(self._PIXMAP_FRAME_WIDTH, updated_rect.left())
        right_updated_edge = min(width - self._PIXMAP_FRAME_WIDTH, updated_rect.right())
        edge_width = right_updated_edge - left_updated_edge
        if edge_width > 0:
            # Top edge
            append_if_created(create_fragment(tx=left_updated_edge, ty=0, tw=edge_width,
                                              sx=self._PIXMAP_FRAME_WIDTH, sy=0,
                                              w=1, h=self._PIXMAP_FRAME_WIDTH))
            # Bottom edge
            append_if_created(create_fragment(tx=left_updated_edge, ty=height - self._PIXMAP_FRAME_WIDTH, tw=edge_width,
                                              sx=self._PIXMAP_FRAME_WIDTH, sy=self._PIXMAP_HEIGHT - self._PIXMAP_FRAME_WIDTH,
                                              w=1, h=self._PIXMAP_FRAME_WIDTH))

        if fragments:
            painter.drawPixmapFragments(fragments, self._pixmap)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._bar._palette.frame)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRoundedRect(QRect(0, 0, width, height), self._FRAME_CORNER_RADIUS, self._FRAME_CORNER_RADIUS)

    def _draw_error(self, painter: QPainter, updated_rect: QRect):
        metrics = QFontMetrics(self._error_font)
        text_height = metrics.height() - 1
        error_rect = QRect(self._CYCLE_BAR_MARGIN_LEFT,
                           (self.height() - text_height) / 2,
                           self.width() - self._CYCLE_BAR_MARGIN_RIGHT,
                           text_height)
        if error_rect.intersects(updated_rect):
            painter.setPen(self._bar._palette.error_text)
            painter.setFont(self._error_font)
            painter.drawText(error_rect, Qt.AlignCenter, "Connection error")

    @property
    def _bar(self) -> TimingBar:
        return cast(TimingBar, self.parent())

    _PIXMAP_WIDTH = 80
    _PIXMAP_HEIGHT = 54
    _PIXMAP_FRAME_WIDTH = 11
    _FONT_SIZE_ERROR_FULL = 14
    _FONT_SIZE_ERROR_COLLAPSED = 10
    _LABEL_AREA_HEIGHT = 23
    _LABEL_TOP_MARGIN = 6
    _LABEL_BOTTOM_MARGIN = 0
    _CYCLE_BAR_SPACING = 2
    _CYCLE_BAR_NORMAL_HEIGHT = 6
    _SUPERCYCLE_OFFSET = -5
    _CYCLE_BAR_MARGIN_TOP = _LABEL_AREA_HEIGHT + _LABEL_TOP_MARGIN + _SUPERCYCLE_OFFSET
    _CYCLE_BAR_MARGIN_BOTTOM = 6
    _CYCLE_BAR_MARGIN_LEFT = 6
    _CYCLE_BAR_MARGIN_RIGHT = 6
    _SUPERCYCLE_HEIGHT = _CYCLE_BAR_NORMAL_HEIGHT * 2 + _CYCLE_BAR_MARGIN_BOTTOM - _SUPERCYCLE_OFFSET
    _TIME_MARK_WIDTH = 2
    _TIME_MARK_LABEL_OFFSET = 10
    _FRAME_CORNER_RADIUS = 6
    _FRAME_FULL_HEIGHT = _CYCLE_BAR_MARGIN_TOP + _SUPERCYCLE_HEIGHT
    _FRAME_MINIMIZED_HEIGHT = _LABEL_AREA_HEIGHT + _LABEL_TOP_MARGIN + _LABEL_BOTTOM_MARGIN - 1
    _NON_SUPERCYCLE_BP_COUNT = 128
