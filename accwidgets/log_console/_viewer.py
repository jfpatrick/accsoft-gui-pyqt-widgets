import html
import qtawesome as qta
from typing import Optional, Union, Dict
from pathlib import Path
from qtpy.QtWidgets import (QMenu, QWidget, QHBoxLayout, QDockWidget, QToolButton, QLineEdit, QFrame, QVBoxLayout,
                            QPlainTextEdit, QDialog, QMessageBox, QSizePolicy)
from qtpy.QtCore import Qt, Signal, Property, Slot, QVariantAnimation, QEasingCurve, QEvent, QObject
from qtpy.QtGui import QIcon, QCursor, QTextDocument, QTextCursor, QPalette, QColor, QFont, QPaintEvent, QPainter
from qtpy.QtPrintSupport import QPrintPreviewDialog
from qtpy.uic import loadUi
from ._search_dialog import LogSearchDialog
from ._config import LogLevel
from ._fmt import LogConsoleFormatter, AbstractLogConsoleFormatter
from ._prefs_dialog import LogPreferencesDialog, ModelConfiguration, ViewConfiguration, FmtConfiguration
from ._model import AbstractLogConsoleModel, LogConsoleModel, LogConsoleRecord
from ._palette import LogConsolePalette


class LogConsole(QWidget):

    expandedStateChanged = Signal(bool)
    """
    Signal to notify when the widget has been collapsed or expanded. The argument is :obj:`True`, when the console
    is expanded.

    :type: pyqtSignal
    """

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 model: Optional[AbstractLogConsoleModel] = None,
                 formatter: Optional[AbstractLogConsoleFormatter] = None):
        """
        Widget to display logs in a HTML-stylized list.

        The last message is always duplicated in a single-line field and the color related to its severity level
        is flashed in that field to attract end-user's attention. The widget has two modes: collapsed and expanded,
        where a full log view is visible or hidden respectively. The single-line field of the last message is visible
        in either mode.

        The mode change can be forbidden by setting the :attr:`collapsible` property to :obj:`False` in cases, when
        hiding parts of the console is undesirable.

        This widget can work with models that define where logs come from and how they are stored. If no custom model
        is provided, the default implementation, :class:`LogConsoleModel` is created that captures Python
        :mod:`logging` output.

        The widget provides a context menu on the right mouse click to:

        - "Freeze"/"unfreeze" the console ("frozen" console becomes static and does not display new logs, until
          "unfrozen")
        - Search for text visible in the console
        - Print visible console logs
        - Configure the display and capturing of the logs in a "Preferences" dialog

        While capturing and storing the logging records is managed by the :attr:`model`, :attr:`formatter` is
        responsible for producing the final string. Default implementation, :class:`LogConsoleFormatter`, can
        show/hide date, time and logger names of individual records. Custom formatters may have completely different
        settings.

        Log severity associated colors are configurable by the user. When such color is used as background rather than
        foreground (e.g. in last message field; or in the main text view, when color is marked as "inverted") the
        foreground text color is chosen automatically between black and white, to have the best contrast, based on the
        background's intensity.

        Args:
            parent: Owning object.
            model: Custom model that should be used with the widget. Model's ownership gets transferred to the widget.
                   If no model is provided, the default implementation, :class:`LogConsoleModel` is used instead.
            formatter: Custom implementation of the formatter (see :attr:`formatter`). If no formatter is provided,
                       the default implementation, :class:`LogConsoleFormatter` is used instead.
        """
        super().__init__(parent)

        self.__collapsible = False
        self.__expanded = True  # Cannot rely on self._contents.isVisible() since it will be invisible when window is invisible

        self._last_msg_line: LogConsoleLastMessageEdit = None  # type: ignore
        self._contents: QPlainTextEdit = None
        self._hlayout: QHBoxLayout = None

        self._model = model or LogConsoleModel()
        self._connect_model(self._model)
        self._model.setParent(self)
        self._color_scheme = LogConsolePalette()

        # Set these to None for the attribute to exist, to properly execute property setter in the end of this method
        self._formatter: AbstractLogConsoleFormatter = None  # type: ignore

        loadUi(Path(__file__).parent / "widget.ui", self)

        self._restyle_contents()
        self._contents.installEventFilter(self)  # Watch style events

        self._btn_toggle: Optional[LogConsoleCollapseButton] = None

        self.customContextMenuRequested.connect(self._on_context_menu)

        self.formatter = formatter or LogConsoleFormatter()

    def __get_formatter(self) -> AbstractLogConsoleFormatter:
        return self._formatter

    def __set_formatter(self, new_formatter: AbstractLogConsoleFormatter):
        if new_formatter == self._formatter:
            return

        self._formatter = new_formatter
        self._rerender_contents()

    formatter = property(fget=__get_formatter, fset=__set_formatter)
    """
    Formatter is responsible for pre-formatting the log message and adding arbitrary auxiliary information to it,
    e.g. timestamps or logger names.

    It is possible to provide a custom implementation of the formatter.
    """

    def __get_model(self) -> AbstractLogConsoleModel:
        return self._model

    def __set_model(self, new_model: AbstractLogConsoleModel):
        if new_model == self._model:
            return

        if self._model:
            self._disconnect_model(self._model)
            self._model.setParent(None)
            self._model.deleteLater()
        if new_model:
            self._connect_model(new_model)

        self._model = new_model
        new_model.setParent(self)
        self._rerender_contents()

    model = property(fget=__get_model, fset=__set_model)
    """
    Model is responsible for receiving and storing log records that are getting displayed in the widget.

    When assigning a custom model, its ownership is transferred to the widget.
    """

    @Slot()
    def clear(self):
        """
        Clear console from any logs.

        This method can be used as a slot.
        """
        self.model.clear()
        self._last_msg_line.clear()
        self._contents.clear()

    @Slot()
    def freeze(self):
        """
        Freeze console to prevent new logs from appearing, until "unfrozen". The model keeps accumulating incoming
        log records, so that they can be displayed after :meth:`unfreeze` is called.

        This method can be used as a slot. It is also called when the user checks "Freeze" item in the context menu.
        """
        self.model.freeze()

    @Slot()
    def unfreeze(self):
        """
        Undo the effects produced in :meth:`freeze`.

        This method can be used as a slot. It is also called when the user unchecks "Freeze" item in the context menu.
        """
        self.model.unfreeze()

    @Slot()
    def toggleFreeze(self):
        """
        Toggles between "frozen" and "unfrozen" state.

        This method can be used as a slot.
        """
        if self.frozen:
            self.unfreeze()
        else:
            self.freeze()

    @Slot()
    def toggleExpandedMode(self):
        """
        Toggles between expanded and collapsed view mode.

        In expanded mode, the full log view is visible, while hidden in collapsed mode. The single-line field of the
        last message is visible in either mode.

        This method can be used as a slot.
        """
        self.expanded = not self.expanded

    @property
    def frozen(self) -> bool:
        """
        Frozen console does not show new logs, until "unfrozen". The model keeps accumulating incoming
        log records, so that they can be displayed after :meth:`unfreeze` is called.
        """
        return self.model.frozen

    def __get_expanded(self) -> bool:
        return self.__expanded

    def __set_expanded(self, expanded: bool):
        if expanded == self.__expanded:
            return
        self.__expanded = expanded
        if not expanded and not self.collapsible:
            # not expanded view is allowed only on a collapsible configuration, enforce it
            self.collapsible = True

        self._contents.setVisible(expanded)
        if self._btn_toggle:
            self._btn_toggle.set_point_to_close(expanded)

        self.expandedStateChanged.emit(self.expanded)

    expanded = Property(bool, fget=__get_expanded, fset=__set_expanded)
    """
    Flag controlling whether the view is expanded or collapsed. The full log view is visible in expanded mode
    and hidden in collapsed mode. The single-line field of the last message is visible in either mode.

    If :attr:`collapsible` is set to :obj:`False`, setting this flag to :obj:`False` will reset :attr:`collapsible`
    back to :obj:`True`.

    :type: bool
    """

    def __get_collapsible(self) -> bool:
        return self.__collapsible

    def __set_collapsible(self, collapsible: bool):
        if collapsible == self.__collapsible:
            return

        self.__collapsible = collapsible
        if collapsible:
            if not self._btn_toggle:
                self._btn_toggle = LogConsoleCollapseButton(self)
                self._btn_toggle.set_point_to_close(self.expanded)
                self._btn_toggle.clicked.connect(self.toggleExpandedMode)
                self._hlayout.addWidget(self._btn_toggle)
        else:
            if not self.expanded:
                # Non-collapsible views should always show full contents
                self.expanded = True
            if self._btn_toggle:
                self._hlayout.removeWidget(self._btn_toggle)
                self._btn_toggle.deleteLater()
                self._btn_toggle = None

    collapsible = Property(bool, fget=__get_collapsible, fset=__set_collapsible)
    """
    Specifies whether the widget can be toggle between "collapsed" and "expanded" modes. If not, the arrow button
    to toggle the modes is removed.

    If :attr:`expanded` is set to :obj:`False`, setting this flag to :obj:`False` will reset :attr:`expanded` back to
    :obj:`True`.

    :type: bool
    """

    def __get_error_color(self) -> str:
        return self._color_scheme.color(LogLevel.ERROR)

    def __set_error_color(self, color: QColor):
        self._set_color_to_scheme(color=color, level=LogLevel.ERROR)

    errorColor = Property(QColor, fget=__get_error_color, fset=__set_error_color, designable=True)
    """
    Default error color, which can also be configured by the user in "Preferences" dialog. This property
    enables ability to restyle the widget with QSS.

    :type: QColor
    """

    def __get_warn_color(self) -> str:
        return self._color_scheme.color(LogLevel.WARNING)

    def __set_warn_color(self, color: QColor):
        self._set_color_to_scheme(color=color, level=LogLevel.WARNING)

    warningColor = Property(QColor, fget=__get_warn_color, fset=__set_warn_color, designable=True)
    """
    Default warning color, which can also be configured by the user in "Preferences" dialog. This property
    enables ability to restyle the widget with QSS.

    :type: QColor
    """

    def __get_critical_color(self) -> str:
        return self._color_scheme.color(LogLevel.CRITICAL)

    def __set_critical_color(self, color: QColor):
        self._set_color_to_scheme(color=color, level=LogLevel.CRITICAL)

    criticalColor = Property(QColor, fget=__get_critical_color, fset=__set_critical_color, designable=True)
    """
    Default critical color, which can also be configured by the user in "Preferences" dialog. This property
    enables ability to restyle the widget with QSS.

    :type: QColor
    """

    def __get_info_color(self) -> str:
        return self._color_scheme.color(LogLevel.INFO)

    def __set_info_color(self, color: QColor):
        self._set_color_to_scheme(color=color, level=LogLevel.INFO)

    infoColor = Property(QColor, fget=__get_info_color, fset=__set_info_color, designable=True)
    """
    Default info color, which can also be configured by the user in "Preferences" dialog. This property
    enables ability to restyle the widget with QSS.

    :type: QColor
    """

    def __get_debug_color(self) -> str:
        return self._color_scheme.color(LogLevel.DEBUG)

    def __set_debug_color(self, color: QColor):
        self._set_color_to_scheme(color=color, level=LogLevel.DEBUG)

    debugColor = Property(QColor, fget=__get_debug_color, fset=__set_debug_color, designable=True)
    """
    Default debug color, which can also be configured by the user in "Preferences" dialog. This property
    enables ability to restyle the widget with QSS.

    :type: QColor
    """

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        This filter handler is reimplemented to react to the external style change, e.g. via QSS, to adjust
        background colors painted in the log contents.

        Filters events if this object has been installed as an event filter for the ``watched`` object.

        In your reimplementation of this function, if you want to

        Args:
            watched: Object related to the event.
            event: Event object to be considered for filtering.

        Returns:
            :obj:`True` for filtering the event out, i.e. stop it being handled further, otherwise :obj:`False`.
        """
        res = super().eventFilter(watched, event)
        if event.type() == QEvent.StyleChange and watched == self._contents:
            self._restyle_contents()
        return res

    def _set_color_to_scheme(self, color: QColor, level: LogLevel):
        color_map = self._color_scheme.color_map
        invert = color_map[level][1]
        color_map[level] = (color.name(), invert)
        self._color_scheme.update_color_map(color_map)

    def _connect_model(self, model: AbstractLogConsoleModel):
        model.new_log_record_received.connect(self._on_new_message)
        model.freeze_changed.connect(self._on_freeze_changed)

    def _disconnect_model(self, model: AbstractLogConsoleModel):
        model.new_log_record_received.disconnect(self._on_new_message)
        model.freeze_changed.disconnect(self._on_freeze_changed)

    def _rerender_contents(self):
        model = self.model

        # Try to avoid jumping of the scrolling as much as possible
        scrollbar = self._contents.verticalScrollBar()
        is_scrollable = scrollbar.minimum() < scrollbar.maximum()
        scrolled_to_bottom = scrollbar.value() == scrollbar.maximum()
        prev_scroll_y = None if (not is_scrollable or scrolled_to_bottom) else scrollbar.value()

        self._last_msg_line.clear()
        html_contents = ""
        last_message: Optional[str] = None
        last_record: Optional[LogConsoleRecord] = None
        for record in model.all_records:
            formatted_message = self.formatter.format(record)
            html_contents += _format_html_message(record=record, formatted_message=formatted_message)
            last_message = formatted_message
            last_record = record
        self._contents.document().setHtml(html_contents)

        if prev_scroll_y is None:
            # Scroll to bottom
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(prev_scroll_y)

        if last_message and last_record:
            main_color = self._color_scheme.color(last_record.level)
            alternate_color = self._color_scheme.color(last_record.level, alternate=True)
            self._last_msg_line.set_styled_text(text=last_message,
                                                background_color=main_color,
                                                foreground_color=alternate_color,
                                                animate=False)

    def _on_context_menu(self):
        ctx_menu = QMenu(self)
        text_color = self.palette().color(QPalette.Text)
        ctx_menu.addAction(qta.icon("fa5s.eraser", color=text_color), "Clear", self._clear_if_confirmed)
        ctx_menu.addAction(qta.icon("fa5s.search", color=text_color), "Find", self._open_search_dialog)
        ctx_menu.addAction(qta.icon("ei.print", color=text_color), "Print", self._open_print_dialog)
        ctx_menu.addSeparator()
        freeze = ctx_menu.addAction("Freeze", self.toggleFreeze)
        freeze.setCheckable(True)
        freeze.setChecked(self.frozen)
        ctx_menu.addSeparator()
        ctx_menu.addAction("Preferences", self._open_prefs_dialog)
        ctx_menu.exec_(QCursor.pos())

    def _clear_if_confirmed(self):
        reply = QMessageBox().question(self,
                                       "Please confirm",
                                       "Do you really want to clear all logs?",
                                       QMessageBox.Yes,
                                       QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.clear()

    def _on_search_requested(self, match_string: str, search_flags: QTextDocument.FindFlags):
        found = self._contents.find(match_string, search_flags)
        self._sig_match_result.emit(found)

    def _on_search_direction_changed(self, search_backwards: bool):
        if self._contents.textCursor().hasSelection():
            # Ignore as we have selection, and just care only if there's no selection, so we'd be placing
            # cursor in the opposite sides of the text
            return

        self._contents.moveCursor(QTextCursor.End if search_backwards else QTextCursor.Start, QTextCursor.MoveAnchor)

    def _open_search_dialog(self):
        if self._contents.textCursor().hasSelection():
            # Clean up selection, so that we can start searching from the beginning of the log
            self._contents.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)
            cursor = self._contents.textCursor()
            cursor.clearSelection()
            self._contents.setTextCursor(cursor)
        # Search is defaulting to backwards, so make sure that we are always in the end of the document
        self._contents.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)
        dialog = LogSearchDialog(parent=self)
        dialog.search_requested.connect(self._on_search_requested)
        dialog.search_direction_changed.connect(self._on_search_direction_changed)
        self._sig_match_result.connect(dialog.on_search_result)
        dialog.exec_()

    def _open_prefs_dialog(self):
        model = self.model

        model_config = ModelConfiguration(buffer_size=model.buffer_size,
                                          visible_levels=model.visible_levels,
                                          selected_logger_levels=model.selected_logger_levels,
                                          available_logger_levels=model.available_logger_levels,
                                          notice=model.level_notice)
        model_config.validate()

        fmt_config: Dict[str, FmtConfiguration] = {}
        for attr_name, title in self.formatter.configurable_attributes().items():
            attr_val = getattr(self.formatter, attr_name)
            fmt_config[attr_name] = FmtConfiguration(value=attr_val, title=title)

        view_config = ViewConfiguration(fmt_config=fmt_config,
                                        color_map=self._color_scheme.color_map)
        dialog = LogPreferencesDialog(model_config=model_config,
                                      view_config=view_config,
                                      sample_formatter_type=type(self.formatter),
                                      parent=self)
        if dialog.exec_() == QDialog.Accepted:
            model.buffer_size = dialog.model_config.buffer_size
            model.visible_levels = dialog.model_config.visible_levels
            model.selected_logger_levels = dialog.model_config.selected_logger_levels
            self._color_scheme.update_color_map(dialog.view_config.color_map)
            self._restyle_contents()

            fmt_kwargs = {attr_name: val.value for attr_name, val in dialog.view_config.fmt_config.items()}
            # This call will cause re-rendering of all contents
            self.formatter = type(self.formatter).create(**fmt_kwargs)

    def _restyle_contents(self):
        stylesheet = self._color_scheme.style_sheet(base_color=self._contents.palette().color(QPalette.Base))
        self._contents.document().setDefaultStyleSheet(stylesheet)

    def _open_print_dialog(self):
        """Open print preview for the contents of the console."""
        dialog = QPrintPreviewDialog(self)
        dialog.paintRequested.connect(self._contents.print_)
        dialog.exec_()

    def _on_freeze_changed(self, frozen: bool):
        if not frozen:
            # After unfreezing, re-render contents to display new messages that were hidden
            # during the frozen time.
            self._rerender_contents()
        self._last_msg_line.set_show_lock(frozen)

    def _on_new_message(self, record: LogConsoleRecord, pop_earliest_message: bool):
        if pop_earliest_message:
            self._pop_first_message()
        self._append_message(record=record, animate=True)

    def _pop_first_message(self):
        if self._contents.document().blockCount() < 1:
            return
        cursor = QTextCursor(self._contents.document().firstBlock())
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()
        self._contents.document().clearUndoRedoStacks()

    def _append_message(self, record: LogConsoleRecord, animate: bool):
        main_color = self._color_scheme.color(record.level)
        alternate_color = self._color_scheme.color(record.level, alternate=True)
        message = self.formatter.format(record)
        self._last_msg_line.set_styled_text(text=message,
                                            background_color=main_color,
                                            foreground_color=alternate_color,
                                            animate=animate)
        html_contents = _format_html_message(record=record, formatted_message=message)
        self._contents.appendHtml(html_contents)
        self._contents.document().clearUndoRedoStacks()

    _sig_match_result = Signal(bool)


def _format_html_message(record: LogConsoleRecord, formatted_message: str) -> str:
    css_class = LogLevel.level_name(record.level)
    escaped_msg = html.escape(formatted_message)
    html_body = escaped_msg.replace("\n", "<br/>")
    # We must wrap <span> inside <p>, otherwise QPlainTextEdit is buggy and will apply custom background to the
    # whole document, if the first element will be colored, and will not apply it, if only subsequent elements
    # are colored.
    html_line = f'<p><span class="{css_class}">{html_body}</span></p>'
    return html_line


class LogConsoleCollapseButton(QToolButton):

    def set_point_to_close(self, point_to_close: bool):
        self.setArrowType(Qt.DownArrow if point_to_close else Qt.UpArrow)


class LogConsoleLastMessageEdit(QLineEdit):

    def __init__(self, parent: Optional[QWidget] = None, animation_duration: int = 5000):
        """
        Custom :class:`QLineEdit` derivative that displays the last log message arriving to the :class:`LogConsole`.

        It animates with the background color corresponding to the log severity level configured by the user.

        Args:
            parent: Owning object.
            animation_duration: Duration in milliseconds for the fade effect of the background color.
        """
        super().__init__(parent)
        self._orig_bkg_color = self.palette().color(QPalette.Base)
        self._orig_text_color = self.palette().color(QPalette.Text)
        self._curr_bkg_color = self._orig_bkg_color
        self._curr_text_color = self._orig_text_color
        self._fg_anim = QVariantAnimation()
        self._bg_anim = QVariantAnimation()
        self._fg_anim.setDuration(animation_duration)
        self._bg_anim.setDuration(animation_duration)
        self._fg_anim.setEasingCurve(QEasingCurve.InExpo)
        self._bg_anim.setEasingCurve(QEasingCurve.InExpo)
        self._fg_anim.valueChanged.connect(self._on_fg_anim_progress)
        self._bg_anim.valueChanged.connect(self._on_bg_anim_progress)
        self._bg_anim.finished.connect(self._on_animation_finished)  # Expect both animations synchronized
        self._icon: Optional[QIcon] = None
        self._showing_lock: bool = False
        self._animating: bool = False
        self._orig_text_margins = self.textMargins()
        font = QFont("Monospace")
        font.setItalic(True)
        self.setFont(font)
        self._reset_colors()

    def set_styled_text(self, text: str, background_color: QColor, foreground_color: QColor, animate: bool):
        """
        Set the text of the line edit to the given string and paint the background and text color according
        to the provided arguments.

        Args:
            text: String to be displayed in the line edit.
            background_color: Background color of the line edit.
            foreground_color: Text color in the line edit.
            animate: Animate with fade effect. When set to :obj:`False` the effects are not activated, and the
                     colors are set to default ones, ignoring the arguments.
        """
        self.setText(text)
        if animate:
            self.animate(background_color, foreground_color)
        else:
            self._animating = False
            self._reset_colors()

    def set_show_lock(self, show: bool):
        """
        Toggle the display of the lock icon in the right corner (that represents the :attr:`~LogConsole.frozen`
        state of the :class:`LogConsole`).

        Args:
            show: Display the lock icon when set to :obj:`True`.
        """

        if self._showing_lock == show:
            return

        self._showing_lock = show
        if show:
            if self._icon is None:
                self._icon = self._make_lock_icon()
            self.setTextMargins(self._orig_text_margins.left(),
                                self._orig_text_margins.top(),
                                self.height(),
                                self._orig_text_margins.bottom())
        else:
            self.setTextMargins(self._orig_text_margins)
        self.update()

    def animate(self, background_color: QColor, foreground_color: QColor):
        """
        Activate the fade effect, transitioning from the background and text colors corresponding to log's
        severity level back into standard color scheme.

        Args:
            background_color: Background color corresponding to log's severity level.
            foreground_color: Text color corresponding to log's severity level.
        """
        self._bg_anim.stop()
        self._fg_anim.stop()
        self._animating = True
        # Set to color without animation (don't just rely on animation start value), because sometimes animation
        # state may end up in the middle, hence showing light text on light background.
        self._curr_text_color = foreground_color
        self._curr_bkg_color = background_color
        self._apply_colors()
        self._fg_anim.setStartValue(foreground_color)
        self._bg_anim.setStartValue(background_color)
        self._fg_anim.setEndValue(self._orig_text_color)
        self._bg_anim.setEndValue(self._orig_bkg_color)
        self._fg_anim.start()
        self._bg_anim.start()

    def setPalette(self, palette: QPalette):
        """
        This property describes the widget's palette. The palette is used by the widget's style when rendering
        standard components, and is available as a means to ensure that custom widgets can maintain consistency with
        the native platform's look and feel. It's common that different platforms, or different styles, have
        different palettes.

        When you assign a new palette to a widget, the color roles from this palette are combined with the widget's
        default palette to form the widget's final palette. The palette entry for the widget's background role is
        used to fill the widget's background (see :meth:`QWidget.autoFillBackground`), and the foreground role
        initializes :class:`QPainter`'s pen.

        Args:
            palette: New palette.
        """
        super().setPalette(palette)
        self._orig_bkg_color = palette.color(QPalette.Base)
        self._orig_text_color = palette.color(QPalette.Text)
        if not self._animating:
            self._curr_bkg_color = self._orig_bkg_color
            self._curr_text_color = self._orig_text_color
        if self._icon is not None:
            # Make sure the color of the icon is correct
            self._icon = self._make_lock_icon()

    def clear(self):
        """Clears the contents of the line edit and stops any ongoing animations."""
        self._bg_anim.stop()
        self._fg_anim.stop()
        self._reset_colors()
        super().clear()

    def paintEvent(self, event: QPaintEvent):
        """
        A paint event is a request to repaint all or part of a widget.

        This implementation augments the standard :meth:`QLineEdit.paintEvent` with rendering of the
        lock icon (see :meth:`set_show_lock`).

        Args:
            event: Paint event.
        """
        super().paintEvent(event)
        if self._showing_lock and self._icon is not None:
            painter = QPainter(self)
            edge = self.height()
            pixmap = self._icon.pixmap(edge, edge)
            painter.drawPixmap(self.width() - edge, 0, pixmap)

    def event(self, event: QEvent) -> bool:
        """
        This event handler is reimplemented to react to the external style change, e.g. via QSS, to adjust
        colors painted in the line edit.

        This is the main event handler; it handles event ``event``. You can reimplement this function in a
        subclass, but we recommend using one of the specialized event handlers instead.

        Args:
            event: Handled event.

        Returns:
            :obj:`True` if the event was recognized, otherwise it returns :obj:`False`. If the recognized event
            was accepted (see :meth:`QEvent.accepted`), any further processing such as event propagation to the
            parent widget stops.
        """
        res = super().event(event)
        if event.type() == QEvent.StyleChange and not self._animating:
            self.setPalette(self.palette())
        return res

    def _reset_colors(self):
        self._curr_bkg_color = self._orig_bkg_color
        self._curr_text_color = self._orig_text_color
        self._apply_colors()

    def _apply_colors(self):
        # Styling must be done with style sheets and not QPalette, to stay compatible with external QSS stylesheets,
        # as explained here: https://doc.qt.io/qt-5/qwidget.html#palette-prop
        if self.testAttribute(Qt.WA_StyleSheet):
            self.setStyleSheet(f"LogConsoleLastMessageEdit{{background-color: {self._curr_bkg_color.name()};"
                               f"color: {self._curr_text_color.name()}}}")
        else:
            palette = self.palette()
            palette.setColor(QPalette.Text, self._curr_text_color)
            palette.setColor(QPalette.Base, self._curr_bkg_color)
            super().setPalette(palette)

    def _on_bg_anim_progress(self, interpolated_value: QColor):
        self._curr_bkg_color = interpolated_value
        self._apply_colors()

    def _on_fg_anim_progress(self, interpolated_value: QColor):
        self._curr_text_color = interpolated_value
        self._apply_colors()

    def _on_animation_finished(self):
        self._animating = False

    def _make_lock_icon(self):
        return qta.icon("fa.lock", color=self._orig_text_color)


class LogConsoleDockContainer(QWidget):
    # This widget is needed to set the combined size policy for the log console and its decorations, that
    # is noticed by the dock widget.

    def __init__(self, parent: Optional[QWidget] = None, console: Optional[LogConsole] = None):
        super().__init__(parent)
        inner_console = console or LogConsole()
        inner_console.collapsible = True
        inner_console.expandedStateChanged.connect(self._on_console_expanded_changed)
        self.console = inner_console
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        vbar = QFrame()
        vbar.setFrameShape(QFrame.HLine)
        vbar.setFrameShadow(QFrame.Raised)
        layout.addWidget(vbar)
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(5, 5, 5, 5)
        inner_layout.addWidget(inner_console)
        layout.addLayout(inner_layout)
        self.setLayout(layout)

    def _on_console_expanded_changed(self, expanded: bool):
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), (QSizePolicy.Preferred
                                                                  if expanded else QSizePolicy.Fixed))


class LogConsoleDock(QDockWidget):

    def __init__(self,
                 title: str = "Log Console",
                 parent: Optional[QWidget] = None,
                 console: Optional[LogConsole] = None,
                 allowed_areas: Optional[Qt.DockWidgetAreas] = None):
        """
        Dock widget that accommodates :class:`LogConsole` widget inside a :class:`QMainWindow`.

        By convention, log console is displayed in the bottom part of the windows. However, this
        widget also permits displaying it on the top of the window (user is able to drag the dock widget
        at runtime). Side areas are disabled, as log console squeezed in the sidebar brings little value.

        When log console is in the "expanded" mode (see :attr:`~LogConsole.expanded`), the dock widget can be
        vertically resized. In the "collapsed" mode, the resizing is not possible and is fixed to only accommodate the
        single-line last message field.

        Args:
            title: Title displayed in the dock widget. The default is "Log Console".
            parent: Owning object.
            console: Instance of the log console (can be a subclass) that should be accommodated in the dock widget.
                     If none is provided, the default widget, :class:`LogConsole`, is created.
            allowed_areas: Override the allowed areas, that by default are assigned to top or bottom of the window only.
        """
        super().__init__(title, parent)
        self.setWidget(LogConsoleDockContainer(console=console))
        if allowed_areas is None:
            super().setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        else:
            super().setAllowedAreas(allowed_areas)

    def setAllowedAreas(self, areas: Union[Qt.DockWidgetAreas, Qt.DockWidgetArea]):
        """
        Overridden to prevent users from setting the allowed areas. If you need to override this,
        set it in the constructor.

        Args:
            areas: Areas where the dock widget may be placed.
        """
        pass

    @property
    def console(self) -> LogConsole:
        """
        Handle on the actual log console widget that is accommodated inside the log widget.
        """
        if not isinstance(self.widget(), LogConsoleDockContainer):
            raise AttributeError("Dock contents have been modified. Cannot retrieve the console widget")
        container: LogConsoleDockContainer = self.widget()
        return container.console
