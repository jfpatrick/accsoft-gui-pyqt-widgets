import pytest
from pytestqt.qtbot import QtBot
from unittest import mock
from typing import Optional, cast
from qtpy.QtWidgets import QWidget, QDockWidget, QMenu, QWidgetAction, QToolBar, QMenuBar
from accwidgets.app_frame import ApplicationFrame
from accwidgets.log_console import LogConsoleDock, LogConsole
from accwidgets.timing_bar import TimingBar
from accwidgets.rbac import RbaButton
from accwidgets.screenshot import ScreenshotButton
from accwidgets.app_frame._frame import _strip_mnemonics, ToolBarSpacer


@pytest.mark.parametrize("use_timing_bar,expect_timing_bar_exist", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("use_console,expect_log_console_exist", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("use_rbac,expect_rbac_exists", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("use_screenshot,expect_screenshot_exists", [
    (True, True),
    (False, False),
])
def test_app_frame_init_use_subwidgets(qtbot: QtBot, use_console, use_timing_bar, use_rbac, use_screenshot,
                                       expect_log_console_exist, expect_timing_bar_exist, expect_rbac_exists,
                                       expect_screenshot_exists):
    widget = ApplicationFrame(use_timing_bar=use_timing_bar,
                              use_log_console=use_console,
                              use_rbac=use_rbac,
                              use_screenshot=use_screenshot)
    qtbot.add_widget(widget)
    if expect_timing_bar_exist:
        assert widget.timing_bar is not None
    else:
        assert widget.timing_bar is None
    if expect_log_console_exist:
        assert widget.log_console is not None
    else:
        assert widget.log_console is None
    if expect_rbac_exists:
        assert widget.rba_widget is not None
    else:
        assert widget.rba_widget is None
    if expect_screenshot_exists:
        assert widget.screenshot_widget is not None
    else:
        assert widget.screenshot_widget is None


def test_app_frame_default_subwidget_usage_flags(qtbot: QtBot):
    widget = ApplicationFrame()
    qtbot.add_widget(widget)
    assert widget.useTimingBar is False
    assert widget.useLogConsole is False
    assert widget.useRBAC is False
    assert widget.useScreenshot is False


@mock.patch("accwidgets.app_frame._frame.AboutDialog.exec_")
def test_app_frame_show_about_dialog(exec_, qtbot: QtBot):
    widget = ApplicationFrame()
    qtbot.add_widget(widget)
    exec_.assert_not_called()
    widget.showAboutDialog()
    exec_.assert_called_once()


@pytest.mark.parametrize("initial_fullscreen,expected_new_fullscreen", [
    (True, False),
    (False, True),
])
def test_app_frame_toggle_fullscreen(qtbot: QtBot, initial_fullscreen, expected_new_fullscreen):
    widget = ApplicationFrame()
    qtbot.add_widget(widget)
    if initial_fullscreen:
        widget.showFullScreen()
    else:
        widget.showNormal()
    assert widget.isFullScreen() == initial_fullscreen
    widget.toggleFullScreen()
    assert widget.isFullScreen() == expected_new_fullscreen


@pytest.mark.parametrize("initial_value,new_value,expect_sets_console", [
    (True, True, False),
    (False, False, False),
    (True, False, True),
    (False, True, True),
])
def test_app_frame_use_log_console_noop_on_the_same_value(qtbot: QtBot, initial_value, new_value, expect_sets_console):
    widget = ApplicationFrame(use_log_console=initial_value)
    qtbot.add_widget(widget)
    with mock.patch("accwidgets.app_frame._frame.ApplicationFrame.log_console", new_callable=mock.PropertyMock) as log_console:
        widget.useLogConsole = new_value
        if expect_sets_console:
            log_console.assert_called()
        else:
            log_console.assert_not_called()


def test_app_frame_use_log_console_uses_default_dock(qtbot: QtBot):
    widget = ApplicationFrame(use_log_console=False)
    qtbot.add_widget(widget)
    assert widget.log_console is None
    widget.useLogConsole = True
    assert isinstance(widget.log_console, LogConsoleDock)


@pytest.mark.parametrize("initial_widget,new_widget,expect_dock_widget_update", [
    (None, None, False),
    ("console1", None, True),
    ("console1", "console1", False),
    ("console1", "console2", True),
    ("console1", "console_dock1", True),
    ("console1", "console_dock2", True),
    ("console1", "console3", True),
    ("console1", "console_regular_dock3", True),
    ("console1", "widget1", True),
    ("console1", "widget_dock1", True),
    ("console_dock1", None, True),
    ("console_dock1", "console1", False),
    ("console_dock1", "console2", True),
    ("console_dock1", "console_dock1", False),
    ("console_dock1", "console_dock2", True),
    ("console_dock1", "console3", True),
    ("console_dock1", "console_regular_dock3", True),
    ("console_dock1", "widget1", True),
    ("console_dock1", "widget_dock1", True),
    ("console3", None, True),
    ("console3", "console3", False),
    ("console3", "console2", True),
    ("console3", "console4", True),
    ("console3", "console_regular_dock3", True),
    ("console3", "console_regular_dock4", True),
    ("console3", "console_dock1", True),
    ("console3", "widget1", True),
    ("console3", "widget_dock1", True),
    ("console_regular_dock3", None, True),
    ("console_regular_dock3", "console3", False),
    ("console_regular_dock3", "console1", True),
    ("console_regular_dock3", "console4", True),
    ("console_regular_dock3", "console_regular_dock3", False),
    ("console_regular_dock3", "console_dock1", True),
    ("console_regular_dock3", "console_regular_dock4", True),
    ("console_regular_dock3", "widget1", True),
    ("console_regular_dock3", "widget_dock1", True),
    ("widget1", None, True),
    ("widget1", "widget1", False),
    ("widget1", "widget2", True),
    ("widget1", "console1", True),
    ("widget1", "console3", True),
    ("widget1", "console_regular_dock3", True),
    ("widget1", "console_dock1", True),
    ("widget1", "widget_dock1", True),
    ("widget1", "widget_dock2", True),
    ("widget_dock1", None, True),
    ("widget_dock1", "widget1", False),
    ("widget_dock1", "widget2", True),
    ("widget_dock1", "console1", True),
    ("widget_dock1", "console3", True),
    ("widget_dock1", "console_regular_dock3", True),
    ("widget_dock1", "console_dock1", True),
    ("widget_dock1", "widget_dock1", False),
    ("widget_dock1", "widget_dock2", True),
    (None, "console1", True),
    (None, "console2", True),
    (None, "console3", True),
    (None, "console4", True),
    (None, "console_dock1", True),
    (None, "console_dock2", True),
    (None, "widget1", True),
    (None, "widget2", True),
    (None, "widget_dock1", True),
    (None, "widget_dock2", True),
    (None, "console_regular_dock3", True),
    (None, "console_regular_dock4", True),
])
def test_app_frame_set_log_console_noop_on_the_same_widget(qtbot: QtBot, initial_widget, new_widget, expect_dock_widget_update):
    # Do not add widgets to the qtbot, otherwise it may crash when it tries to close them, but they've already
    # been deleted by the application frame.
    console1 = LogConsole()
    console2 = LogConsole()
    console3 = LogConsole()
    console4 = LogConsole()
    widget1 = QWidget()
    widget2 = QWidget()
    widget_dock1 = QDockWidget()
    widget_dock1.setWidget(widget1)
    widget_dock2 = QDockWidget()
    widget_dock2.setWidget(widget2)
    console_regular_dock3 = QDockWidget()
    console_regular_dock3.setWidget(console3)
    console_regular_dock4 = QDockWidget()
    console_regular_dock4.setWidget(console4)

    subwidgets = {
        "console1": console1,
        "console2": console2,
        "console3": console3,
        "console4": console4,
        "console_dock1": LogConsoleDock(console=console1),
        "console_dock2": LogConsoleDock(console=console2),
        "widget1": widget1,
        "widget2": widget2,
        "widget_dock1": widget_dock1,
        "widget_dock2": widget_dock2,
        "console_regular_dock3": console_regular_dock3,
        "console_regular_dock4": console_regular_dock4,
    }
    widget = ApplicationFrame(use_log_console=False)
    qtbot.add_widget(widget)
    widget.log_console = None if initial_widget is None else subwidgets[initial_widget]
    with mock.patch("accwidgets.app_frame._frame.ApplicationFrame.addDockWidget") as addDockWidget:
        with mock.patch("accwidgets.app_frame._frame.ApplicationFrame.removeDockWidget") as removeDockWidget:
            widget.log_console = None if new_widget is None else subwidgets[new_widget]
            call_count = addDockWidget.call_count + removeDockWidget.call_count
            if expect_dock_widget_update:
                assert call_count > 0
            else:
                assert call_count == 0


@pytest.mark.parametrize("new_subwidget_class", [None, LogConsole, LogConsoleDock, QDockWidget])
def test_app_frame_set_log_console_removes_old_widget(qtbot: QtBot, new_subwidget_class):
    widget = ApplicationFrame(use_log_console=True)
    qtbot.add_widget(widget)
    with qtbot.wait_signal(widget.log_console.destroyed):
        widget.log_console = None if new_subwidget_class is None else new_subwidget_class()


@pytest.mark.parametrize("new_subwidget_class", [LogConsole, LogConsoleDock, QDockWidget])
def test_app_frame_set_log_console_removes_toggle_action_of_old_widget_if_menu_exists(qtbot: QtBot, new_subwidget_class):
    widget = ApplicationFrame(use_log_console=False)
    qtbot.add_widget(widget)
    widget.menuBar().addMenu("Useless")  # To make sure that it's not any menu that is picked up
    view_menu = widget.menuBar().addMenu("View")

    def toggle_actions_count() -> int:
        return len([a for a in view_menu.actions() if a.text() == "Toggle Log Console"])

    assert toggle_actions_count() == 0
    widget.log_console = LogConsoleDock()
    assert toggle_actions_count() == 1
    widget.log_console = new_subwidget_class()
    assert toggle_actions_count() == 1
    widget.log_console = None
    assert toggle_actions_count() == 0


@pytest.mark.parametrize("new_subwidget_class", [LogConsole, LogConsoleDock, QDockWidget])
def test_app_frame_set_log_console_removes_does_not_create_view_menu_if_not_exists(qtbot: QtBot, new_subwidget_class):
    widget = ApplicationFrame(use_log_console=False)
    qtbot.add_widget(widget)
    widget.menuBar().addMenu("Useless")  # To make sure that it's not any menu that is picked up

    def get_view_menu() -> Optional[QMenu]:
        try:
            return next(iter(w for w in widget.menuBar().actions() if w.text() == "View"))
        except StopIteration:
            return None

    assert get_view_menu() is None
    widget.log_console = new_subwidget_class()
    assert get_view_menu() is None
    widget.log_console = None
    assert get_view_menu() is None


@pytest.mark.parametrize("new_subwidget_class,expect_dock_exist", [
    (None, False),
    (LogConsole, True),
    (LogConsoleDock, True),
    (QDockWidget, True),
    (QWidget, True),
])
def test_app_frame_set_log_console_adds_new_widget(qtbot: QtBot, new_subwidget_class, expect_dock_exist):
    widget = ApplicationFrame(use_log_console=False)
    qtbot.add_widget(widget)
    assert len([w for w in widget.children() if isinstance(w, QDockWidget)]) == 0
    widget.log_console = None if new_subwidget_class is None else new_subwidget_class()
    actual_count = len([w for w in widget.children() if isinstance(w, QDockWidget)])
    if expect_dock_exist:
        assert actual_count == 1
    else:
        assert actual_count == 0


@pytest.mark.parametrize("new_subwidget_class,expected_wrapper_class", [
    (LogConsole, QDockWidget),
    (LogConsoleDock, LogConsoleDock),
    (QDockWidget, QDockWidget),
    (QWidget, QDockWidget),
])
def test_app_frame_set_log_console_wraps_in_dock_if_not_dock_widget(qtbot: QtBot, new_subwidget_class, expected_wrapper_class):
    widget = ApplicationFrame(use_log_console=False)
    qtbot.add_widget(widget)
    assert widget.log_console is None
    widget.log_console = new_subwidget_class()
    assert type(widget.log_console) == expected_wrapper_class


@pytest.mark.parametrize("initial_value,new_value,expect_sets_bar", [
    (True, True, False),
    (False, False, False),
    (True, False, True),
    (False, True, True),
])
def test_app_frame_use_timing_bar_noop_on_the_same_value(qtbot: QtBot, initial_value, new_value, expect_sets_bar):
    widget = ApplicationFrame(use_timing_bar=initial_value)
    qtbot.add_widget(widget)
    with mock.patch("accwidgets.app_frame._frame.ApplicationFrame.timing_bar", new_callable=mock.PropertyMock) as timing_bar:
        widget.useTimingBar = new_value
        if expect_sets_bar:
            timing_bar.assert_called()
        else:
            timing_bar.assert_not_called()


def test_app_frame_use_timing_bar_sets_bar_widget(qtbot: QtBot):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    assert widget.timing_bar is None
    widget.useTimingBar = True
    assert isinstance(widget.timing_bar, TimingBar)


@pytest.mark.parametrize("initial_widget,new_widget,expect_widget_update", [
    (None, None, False),
    ("bar1", None, True),
    ("bar1", "bar1", False),
    ("bar1", "bar2", True),
    ("bar1", "widget1", True),
    ("widget1", None, True),
    ("widget1", "widget1", False),
    ("widget1", "widget2", True),
    ("widget1", "bar1", True),
    (None, "bar1", True),
    (None, "widget1", True),
])
def test_app_frame_set_timing_bar_noop_on_the_same_widget(qtbot: QtBot, initial_widget, new_widget, expect_widget_update):
    # Do not add widgets to the qtbot, otherwise it may crash when it tries to close them, but they've already
    # been deleted by the application frame.
    bar1 = TimingBar()
    bar2 = TimingBar()
    widget1 = QWidget()
    widget2 = QWidget()

    subwidgets = {
        "bar1": bar1,
        "bar2": bar2,
        "widget1": widget1,
        "widget2": widget2,
    }
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    widget.timing_bar = None if initial_widget is None else subwidgets[initial_widget]
    with mock.patch("qtpy.QtWidgets.QToolBar.addWidget") as addWidget:
        with mock.patch("qtpy.QtWidgets.QToolBar.removeAction") as removeAction:
            widget.timing_bar = None if new_widget is None else subwidgets[new_widget]
            call_count = addWidget.call_count + removeAction.call_count
            if expect_widget_update:
                assert call_count > 0
            else:
                assert call_count == 0


@pytest.mark.parametrize("old_widget_type", [QWidget, TimingBar])
@pytest.mark.parametrize("new_widget_type", [None, QWidget, TimingBar])
def test_app_frame_set_timing_bar_removes_old_widget(qtbot: QtBot, old_widget_type, new_widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)

    timing_bar_widget = old_widget_type()

    def timing_bar_widget_is_in_toolbar() -> bool:
        for action in widget.main_toolbar().actions():
            if isinstance(action, QWidgetAction) and cast(QWidgetAction, action).defaultWidget() == timing_bar_widget:
                return True
        return False

    assert not timing_bar_widget_is_in_toolbar()
    widget.timing_bar = timing_bar_widget
    assert timing_bar_widget_is_in_toolbar()
    widget.timing_bar = None if new_widget_type is None else new_widget_type()
    assert not timing_bar_widget_is_in_toolbar()


@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
def test_app_frame_set_timing_bar_adds_new_widget_when_toolbar_does_not_exist(qtbot: QtBot, widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    assert widget.main_toolbar(create=False) is None
    new_timing_bar = widget_type()
    widget.timing_bar = new_timing_bar
    assert widget.main_toolbar(create=False) is not None
    main_toolbar = widget.main_toolbar(create=False)
    assert main_toolbar is not None
    assert len(main_toolbar.actions()) == 1
    assert isinstance(main_toolbar.actions()[0], QWidgetAction)
    assert cast(QWidgetAction, main_toolbar.actions()[0]).defaultWidget() == new_timing_bar


@pytest.mark.parametrize("widget_dest,widget_type", [
    ("timing_bar", QWidget),
    ("timing_bar", TimingBar),
    ("rba_widget", QWidget),
    ("rba_widget", RbaButton),
    ("screenshot_widget", QWidget),
    ("screenshot_widget", ScreenshotButton),
])
@pytest.mark.parametrize("another_toolbar_exists", [True, False])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_toolbar_item_adds_toggle_action_when_toolbar_gets_created(_, qtbot: QtBot, widget_type,
                                                                                 another_toolbar_exists, widget_dest):
    app_frame = ApplicationFrame(use_timing_bar=False, use_rbac=False, use_screenshot=False)
    qtbot.add_widget(app_frame)
    assert app_frame.main_toolbar(create=False) is None
    new_widget = widget_type()

    view_menu = app_frame.menuBar().addMenu("View")

    def toggle_actions_count() -> int:
        return len([a for a in view_menu.actions() if a.text() == "Toggle Primary Toolbar"])

    if another_toolbar_exists:
        app_frame.addToolBar("Another toolbar")

    assert toggle_actions_count() == 0
    setattr(app_frame, widget_dest, new_widget)
    assert toggle_actions_count() == 1


@pytest.mark.parametrize("widget_dest,widget_type,expected_actions_count,expected_action_index", [
    ("timing_bar", QWidget, 1, 0),
    ("timing_bar", TimingBar, 1, 0),
    ("rba_widget", QWidget, 2, 1),
    ("rba_widget", RbaButton, 2, 1),
    ("screenshot_widget", QWidget, 2, 1),
    ("screenshot_widget", ScreenshotButton, 2, 1),
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_toolbar_item_adds_new_widget_when_only_main_toolbar_exists(_, qtbot: QtBot, widget_type, widget_dest,
                                                                                  expected_action_index, expected_actions_count):
    app_frame = ApplicationFrame(use_timing_bar=False, use_rbac=False, use_screenshot=False)
    qtbot.add_widget(app_frame)
    main_toolbar = app_frame.main_toolbar()
    assert len(main_toolbar.actions()) == 0
    new_widget = widget_type()
    setattr(app_frame, widget_dest, new_widget)
    assert len(main_toolbar.actions()) == expected_actions_count
    for i in range(0, expected_action_index):
        assert isinstance(main_toolbar.actions()[i], QWidgetAction)
        assert isinstance(cast(QWidgetAction, main_toolbar.actions()[i]).defaultWidget(), ToolBarSpacer)
    assert cast(QWidgetAction, main_toolbar.actions()[expected_action_index]).defaultWidget() == new_widget


@pytest.mark.parametrize("widget_dest,widget_type,expected_actions_count,expected_action_index", [
    ("timing_bar", QWidget, 1, 0),
    ("timing_bar", TimingBar, 1, 0),
    ("rba_widget", QWidget, 2, 1),
    ("rba_widget", RbaButton, 2, 1),
    ("screenshot_widget", QWidget, 2, 1),
    ("screenshot_widget", ScreenshotButton, 2, 1),
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_toolbar_item_adds_new_widget_when_multiple_toolbars_exist(_, qtbot: QtBot, widget_type, widget_dest,
                                                                                 expected_action_index, expected_actions_count):
    app_frame = ApplicationFrame(use_timing_bar=False, use_rbac=False)
    qtbot.add_widget(app_frame)
    another_toolbar = app_frame.addToolBar("Another toolbar")
    main_toolbar = app_frame.main_toolbar()
    assert len(main_toolbar.actions()) == 0
    assert len(another_toolbar.actions()) == 0
    new_widget = widget_type()
    setattr(app_frame, widget_dest, new_widget)
    assert len(main_toolbar.actions()) == expected_actions_count
    assert len(another_toolbar.actions()) == 0
    for i in range(0, expected_action_index):
        assert isinstance(main_toolbar.actions()[i], QWidgetAction)
        assert isinstance(cast(QWidgetAction, main_toolbar.actions()[i]).defaultWidget(), ToolBarSpacer)
    assert cast(QWidgetAction, main_toolbar.actions()[expected_action_index]).defaultWidget() == new_widget


@pytest.mark.parametrize("widget_dest,widget_type,expected_actions_count,expected_action_index,expected_orig_index", [
    ("timing_bar", QWidget, 2, 0, 1),
    ("timing_bar", TimingBar, 2, 0, 1),
    ("rba_widget", QWidget, 3, 2, 0),
    ("rba_widget", RbaButton, 3, 2, 0),
    ("screenshot_widget", QWidget, 3, 2, 0),
    ("screenshot_widget", ScreenshotButton, 3, 2, 0),
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_toolbar_item_adds_new_widget_when_main_toolbar_is_not_empty(_, qtbot: QtBot, widget_type, widget_dest,
                                                                                   expected_action_index,
                                                                                   expected_actions_count,
                                                                                   expected_orig_index):
    app_frame = ApplicationFrame(use_timing_bar=False, use_rbac=False)
    qtbot.add_widget(app_frame)
    main_toolbar = app_frame.main_toolbar()
    main_toolbar.addAction("Test action")
    assert len(main_toolbar.actions()) == 1
    orig_action = main_toolbar.actions()[0]
    assert not isinstance(orig_action, QWidgetAction)
    assert orig_action.text() == "Test action"
    new_widget = widget_type()
    setattr(app_frame, widget_dest, new_widget)
    assert app_frame.main_toolbar(create=False) is not None
    assert len(main_toolbar.actions()) == expected_actions_count
    for i in range(expected_actions_count):
        if i == expected_orig_index:
            assert main_toolbar.actions()[i] is orig_action
        else:
            assert isinstance(main_toolbar.actions()[i], QWidgetAction)
            default_widget = cast(QWidgetAction, main_toolbar.actions()[i]).defaultWidget()
            if i == expected_action_index:
                assert default_widget is new_widget
            else:
                assert isinstance(default_widget, ToolBarSpacer)


@pytest.mark.parametrize("orig_sequence,new_sequence,should_remove_toolbar", [
    ([(QWidget, "timing_bar")], [(None, "timing_bar")], True),
    ([(QWidget, "timing_bar")], [(QWidget, "timing_bar")], False),
    ([(QWidget, "timing_bar")], [(TimingBar, "timing_bar")], False),
    ([(TimingBar, "timing_bar")], [(None, "timing_bar")], True),
    ([(TimingBar, "timing_bar")], [(QWidget, "timing_bar")], False),
    ([(TimingBar, "timing_bar")], [(TimingBar, "timing_bar")], False),
    ([(QWidget, "rba_widget")], [(None, "rba_widget")], True),
    ([(QWidget, "rba_widget")], [(QWidget, "rba_widget")], False),
    ([(QWidget, "rba_widget")], [(RbaButton, "rba_widget")], False),
    ([(RbaButton, "rba_widget")], [(None, "rba_widget")], True),
    ([(RbaButton, "rba_widget")], [(QWidget, "rba_widget")], False),
    ([(RbaButton, "rba_widget")], [(RbaButton, "rba_widget")], False),
    ([(QWidget, "screenshot_widget")], [(None, "screenshot_widget")], True),
    ([(QWidget, "screenshot_widget")], [(QWidget, "screenshot_widget")], False),
    ([(QWidget, "screenshot_widget")], [(ScreenshotButton, "screenshot_widget")], False),
    ([(ScreenshotButton, "screenshot_widget")], [(None, "screenshot_widget")], True),
    ([(ScreenshotButton, "screenshot_widget")], [(QWidget, "screenshot_widget")], False),
    ([(ScreenshotButton, "screenshot_widget")], [(ScreenshotButton, "screenshot_widget")], False),
    ([(TimingBar, "timing_bar"), (RbaButton, "rba_widget")], [(None, "rba_widget")], False),
    ([(TimingBar, "timing_bar"), (RbaButton, "rba_widget")], [(None, "timing_bar")], False),
    ([(TimingBar, "timing_bar"), (ScreenshotButton, "screenshot_widget")], [(None, "screenshot_widget")], False),
    ([(TimingBar, "timing_bar"), (ScreenshotButton, "screenshot_widget")], [(None, "timing_bar")], False),
    ([(RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")], [(None, "screenshot_widget")], False),
    ([(RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")], [(None, "rba_widget")], False),
    ([(TimingBar, "timing_bar"), (RbaButton, "rba_widget")], [(None, "timing_bar"), (None, "rba_widget")], True),
    ([(TimingBar, "timing_bar"), (RbaButton, "rba_widget")], [(None, "rba_widget"), (None, "timing_bar")], True),
    ([(TimingBar, "timing_bar"), (ScreenshotButton, "screenshot_widget")], [(None, "timing_bar"), (None, "screenshot_widget")], True),
    ([(TimingBar, "timing_bar"), (ScreenshotButton, "screenshot_widget")], [(None, "screenshot_widget"), (None, "timing_bar")], True),
    ([(RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")], [(None, "rba_widget"), (None, "screenshot_widget")], True),
    ([(RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")], [(None, "screenshot_widget"), (None, "rba_widget")], True),
    ([(TimingBar, "timing_bar"), (RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")], [(None, "timing_bar"), (None, "screenshot_widget"), (None, "rba_widget")], True),
    ([(TimingBar, "timing_bar"), (RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")], [(None, "timing_bar"), (None, "rba_widget"), (None, "screenshot_widget")], True),
    ([(TimingBar, "timing_bar"), (RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")], [(None, "rba_widget"), (None, "screenshot_widget"), (None, "timing_bar")], True),
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_toolbar_item_to_none_deletes_main_toolbar_if_last_widget(_, qtbot: QtBot, orig_sequence,
                                                                                new_sequence, should_remove_toolbar):
    app_frame = ApplicationFrame(use_timing_bar=False, use_rbac=False, use_screenshot=False)
    qtbot.add_widget(app_frame)
    assert app_frame.main_toolbar(create=False) is None
    for widget_type, widget_dest in orig_sequence:
        setattr(app_frame, widget_dest, widget_type())
    main_toolbar = app_frame.main_toolbar(create=False)
    assert main_toolbar is not None
    with qtbot.wait_signal(main_toolbar.destroyed, raising=False, timeout=100) as blocker:
        for widget_type, widget_dest in new_sequence:
            setattr(app_frame, widget_dest, None if widget_type is None else widget_type())
    assert blocker.signal_triggered == should_remove_toolbar
    assert (app_frame.main_toolbar(create=False) is None) == should_remove_toolbar


@pytest.mark.parametrize("widget_seq", [
    [(TimingBar, "timing_bar")],
    [(RbaButton, "rba_widget")],
    [(ScreenshotButton, "screenshot_widget")],
    [(TimingBar, "timing_bar"), (RbaButton, "rba_widget")],
    [(RbaButton, "rba_widget"), (TimingBar, "timing_bar")],
    [(ScreenshotButton, "screenshot_widget"), (RbaButton, "rba_widget")],
    [(ScreenshotButton, "screenshot_widget"), (TimingBar, "timing_bar")],
    [(TimingBar, "timing_bar"), (ScreenshotButton, "screenshot_widget")],
    [(RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")],
    [(TimingBar, "timing_bar"), (RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget")],
    [(TimingBar, "timing_bar"), (ScreenshotButton, "screenshot_widget"), (RbaButton, "rba_widget")],
    [(RbaButton, "rba_widget"), (ScreenshotButton, "screenshot_widget"), (TimingBar, "timing_bar")],
    [(ScreenshotButton, "screenshot_widget"), (RbaButton, "rba_widget"), (TimingBar, "timing_bar")],
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_toolbar_item_to_none_deletes_main_toolbar_toggle_view_action_if_last_widget_and_menu_exists(_,
                                                                                                                   qtbot: QtBot,
                                                                                                                   widget_seq):
    app_frame = ApplicationFrame(use_timing_bar=False, use_rbac=False, use_screenshot=False)
    qtbot.add_widget(app_frame)
    app_frame.menuBar().addMenu("Useless")  # To make sure that it's not any menu that is picked up
    view_menu = app_frame.menuBar().addMenu("View")

    def toggle_actions_count() -> int:
        return len([a for a in view_menu.actions() if a.text() == "Toggle Primary Toolbar"])

    assert toggle_actions_count() == 0
    for widget_type, widget_dest in widget_seq:
        setattr(app_frame, widget_dest, widget_type())
    assert toggle_actions_count() == 1
    for widget_type, widget_dest in widget_seq:
        setattr(app_frame, widget_dest, widget_type())
    assert toggle_actions_count() == 1
    for _, widget_dest in widget_seq:
        setattr(app_frame, widget_dest, None)
    assert toggle_actions_count() == 0


@pytest.mark.parametrize("widget_type,widget_dest", [
    (TimingBar, "timing_bar"),
    (RbaButton, "rba_widget"),
    (ScreenshotButton, "screenshot_widget"),
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_toolbar_item_main_toolbar_does_not_create_view_menu_if_not_exists(_, qtbot: QtBot,
                                                                                         widget_dest,
                                                                                         widget_type):
    app_frame = ApplicationFrame(use_timing_bar=False, use_rbac=False)
    qtbot.add_widget(app_frame)
    app_frame.menuBar().addMenu("Useless")  # To make sure that it's not any menu that is picked up

    def get_view_menu() -> Optional[QMenu]:
        try:
            return next(iter(w for w in app_frame.menuBar().actions() if w.text() == "View"))
        except StopIteration:
            return None

    assert get_view_menu() is None
    setattr(app_frame, widget_dest, widget_type())
    assert get_view_menu() is None
    setattr(app_frame, widget_dest, None)
    assert get_view_menu() is None


@pytest.mark.parametrize("use_timing_bar,use_rbac,use_screenshot,expected_seq", [
    (False, False, False, []),
    (True, False, False, [TimingBar]),
    (False, True, False, [ToolBarSpacer, RbaButton]),
    (True, True, False, [TimingBar, ToolBarSpacer, RbaButton]),
    (False, False, True, [ToolBarSpacer, ScreenshotButton]),
    (True, False, True, [TimingBar, ToolBarSpacer, ScreenshotButton]),
    (False, True, True, [ToolBarSpacer, ScreenshotButton, RbaButton]),
    (True, True, True, [TimingBar, ToolBarSpacer, ScreenshotButton, RbaButton]),
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_toolbar_contents_with_multiple_toolbar_items_at_init(_, qtbot: QtBot, use_timing_bar, use_rbac,
                                                                        use_screenshot, expected_seq):
    widget = ApplicationFrame(use_timing_bar=use_timing_bar,
                              use_rbac=use_rbac,
                              use_screenshot=use_screenshot)
    qtbot.add_widget(widget)
    main_toolbar = widget.main_toolbar(create=False)
    if len(expected_seq) == 0:
        assert main_toolbar is None
    else:
        assert main_toolbar is not None
        assert len(main_toolbar.actions()) == len(expected_seq)
        for action, expected_type in zip(main_toolbar.actions(), expected_seq):
            assert isinstance(action, QWidgetAction)
            assert isinstance(cast(QWidgetAction, action).defaultWidget(), expected_type)


@pytest.mark.parametrize("set_sequence,expected_seq", [
    ([], []),
    ([("timing_bar", TimingBar)], [TimingBar]),
    ([("rba_widget", RbaButton)], [ToolBarSpacer, RbaButton]),
    ([("screenshot_widget", ScreenshotButton)], [ToolBarSpacer, ScreenshotButton]),
    ([("timing_bar", TimingBar), ("rba_widget", RbaButton)], [TimingBar, ToolBarSpacer, RbaButton]),
    ([("rba_widget", RbaButton), ("timing_bar", TimingBar)], [TimingBar, ToolBarSpacer, RbaButton]),
    ([("timing_bar", TimingBar), ("screenshot_widget", ScreenshotButton)], [TimingBar, ToolBarSpacer, ScreenshotButton]),
    ([("rba_widget", RbaButton), ("screenshot_widget", ScreenshotButton)], [ToolBarSpacer, ScreenshotButton, RbaButton]),
    ([("rba_widget", RbaButton), ("timing_bar", TimingBar), ("screenshot_widget", ScreenshotButton)], [TimingBar, ToolBarSpacer, ScreenshotButton, RbaButton]),
    ([("timing_bar", TimingBar), ("rba_widget", RbaButton), ("screenshot_widget", ScreenshotButton)], [TimingBar, ToolBarSpacer, ScreenshotButton, RbaButton]),
    ([("rba_widget", RbaButton), ("screenshot_widget", ScreenshotButton), ("timing_bar", TimingBar)], [TimingBar, ToolBarSpacer, ScreenshotButton, RbaButton]),
    ([("screenshot_widget", ScreenshotButton), ("rba_widget", RbaButton), ("timing_bar", TimingBar)], [TimingBar, ToolBarSpacer, ScreenshotButton, RbaButton]),
])
@pytest.mark.parametrize("create_toolbar_upfront", [True, False])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_toolbar_contents_with_multiple_toolbar_items_after_init(_, qtbot: QtBot, set_sequence, expected_seq,
                                                                           create_toolbar_upfront):
    widget = ApplicationFrame(use_timing_bar=False, use_rbac=False)
    qtbot.add_widget(widget)
    widget.main_toolbar(create=create_toolbar_upfront)
    for widget_dest, widget_type in set_sequence:
        setattr(widget, widget_dest, widget_type())
    main_toolbar = widget.main_toolbar(create=False)
    if len(expected_seq) == 0 and not create_toolbar_upfront:
        assert main_toolbar is None
    else:
        assert main_toolbar is not None
        assert len(main_toolbar.actions()) == len(expected_seq)
        for action, expected_type in zip(main_toolbar.actions(), expected_seq):
            assert isinstance(action, QWidgetAction)
            assert isinstance(cast(QWidgetAction, action).defaultWidget(), expected_type)


@pytest.mark.parametrize("initial_value,new_value,expect_sets_bar", [
    (True, True, False),
    (False, False, False),
    (True, False, True),
    (False, True, True),
])
def test_app_frame_use_rbac_noop_on_the_same_value(qtbot: QtBot, initial_value, new_value, expect_sets_bar):
    widget = ApplicationFrame(use_rbac=initial_value)
    qtbot.add_widget(widget)
    with mock.patch("accwidgets.app_frame._frame.ApplicationFrame.rba_widget", new_callable=mock.PropertyMock) as rbac:
        widget.useRBAC = new_value
        if expect_sets_bar:
            rbac.assert_called()
        else:
            rbac.assert_not_called()


def test_app_frame_use_rbac_sets_bar_widget(qtbot: QtBot):
    widget = ApplicationFrame(use_rbac=False)
    qtbot.add_widget(widget)
    assert widget.rba_widget is None
    widget.useRBAC = True
    assert isinstance(widget.rba_widget, RbaButton)


@pytest.mark.parametrize("initial_widget,new_widget,expect_widget_update", [
    (None, None, False),
    ("rbac1", None, True),
    ("rbac1", "rbac1", False),
    ("rbac1", "rbac2", True),
    ("rbac1", "widget1", True),
    ("widget1", None, True),
    ("widget1", "widget1", False),
    ("widget1", "widget2", True),
    ("widget1", "rbac1", True),
    (None, "rbac1", True),
    (None, "widget1", True),
])
def test_app_frame_set_rbac_noop_on_the_same_widget(qtbot: QtBot, initial_widget, new_widget, expect_widget_update):
    # Do not add widgets to the qtbot, otherwise it may crash when it tries to close them, but they've already
    # been deleted by the application frame.
    rbac1 = RbaButton()
    rbac2 = RbaButton()
    widget1 = QWidget()
    widget2 = QWidget()

    subwidgets = {
        "rbac1": rbac1,
        "rbac2": rbac2,
        "widget1": widget1,
        "widget2": widget2,
    }
    widget = ApplicationFrame(use_rbac=False)
    qtbot.add_widget(widget)
    widget.rba_widget = None if initial_widget is None else subwidgets[initial_widget]
    with mock.patch("qtpy.QtWidgets.QToolBar.addWidget") as addWidget:
        with mock.patch("qtpy.QtWidgets.QToolBar.removeAction") as removeAction:
            widget.rba_widget = None if new_widget is None else subwidgets[new_widget]
            call_count = addWidget.call_count + removeAction.call_count
            if expect_widget_update:
                assert call_count > 0
            else:
                assert call_count == 0


@pytest.mark.parametrize("old_widget_type", [QWidget, RbaButton])
@pytest.mark.parametrize("new_widget_type", [None, QWidget, RbaButton])
def test_app_frame_set_rbac_removes_old_widget(qtbot: QtBot, old_widget_type, new_widget_type):
    widget = ApplicationFrame(use_rbac=False)
    qtbot.add_widget(widget)

    rbac_widget = old_widget_type()

    def rbac_widget_is_in_toolbar() -> bool:
        for action in widget.main_toolbar().actions():
            if isinstance(action, QWidgetAction) and cast(QWidgetAction, action).defaultWidget() == rbac_widget:
                return True
        return False

    assert not rbac_widget_is_in_toolbar()
    widget.rba_widget = rbac_widget
    assert rbac_widget_is_in_toolbar()
    widget.rba_widget = None if new_widget_type is None else new_widget_type()
    assert not rbac_widget_is_in_toolbar()


@pytest.mark.parametrize("initial_value,new_value,expect_sets_bar", [
    (True, True, False),
    (False, False, False),
    (True, False, True),
    (False, True, True),
])
def test_app_frame_use_screenshot_noop_on_the_same_value(qtbot: QtBot, initial_value, new_value, expect_sets_bar):
    widget = ApplicationFrame(use_screenshot=initial_value)
    qtbot.add_widget(widget)
    with mock.patch("accwidgets.app_frame._frame.ApplicationFrame.screenshot_widget", new_callable=mock.PropertyMock) as prop:
        widget.useScreenshot = new_value
        if expect_sets_bar:
            prop.assert_called()
        else:
            prop.assert_not_called()


@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_use_screenshot_sets_bar_widget(_, qtbot: QtBot):
    widget = ApplicationFrame(use_screenshot=False)
    qtbot.add_widget(widget)
    assert widget.screenshot_widget is None
    widget.useScreenshot = True
    assert isinstance(widget.screenshot_widget, ScreenshotButton)


@pytest.mark.parametrize("initial_widget,new_widget,expect_widget_update", [
    (None, None, False),
    ("scrn1", None, True),
    ("scrn1", "scrn1", False),
    ("scrn1", "scrn2", True),
    ("scrn1", "widget1", True),
    ("widget1", None, True),
    ("widget1", "widget1", False),
    ("widget1", "widget2", True),
    ("widget1", "scrn1", True),
    (None, "scrn1", True),
    (None, "widget1", True),
])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_screenshot_noop_on_the_same_widget(_, qtbot: QtBot, initial_widget, new_widget, expect_widget_update):
    # Do not add widgets to the qtbot, otherwise it may crash when it tries to close them, but they've already
    # been deleted by the application frame.
    scrn1 = ScreenshotButton()
    scrn2 = ScreenshotButton()
    widget1 = QWidget()
    widget2 = QWidget()

    subwidgets = {
        "scrn1": scrn1,
        "scrn2": scrn2,
        "widget1": widget1,
        "widget2": widget2,
    }
    widget = ApplicationFrame(use_rbac=False)
    qtbot.add_widget(widget)
    widget.screenshot_widget = None if initial_widget is None else subwidgets[initial_widget]
    with mock.patch("qtpy.QtWidgets.QToolBar.addWidget") as addWidget:
        with mock.patch("qtpy.QtWidgets.QToolBar.removeAction") as removeAction:
            widget.screenshot_widget = None if new_widget is None else subwidgets[new_widget]
            call_count = addWidget.call_count + removeAction.call_count
            if expect_widget_update:
                assert call_count > 0
            else:
                assert call_count == 0


@pytest.mark.parametrize("old_widget_type", [QWidget, ScreenshotButton])
@pytest.mark.parametrize("new_widget_type", [None, QWidget, ScreenshotButton])
@mock.patch("accwidgets.screenshot._model.LogbookModel")
def test_app_frame_set_screenshot_removes_old_widget(_, qtbot: QtBot, old_widget_type, new_widget_type):
    widget = ApplicationFrame(use_screenshot=False)
    qtbot.add_widget(widget)

    screenshot_widget = old_widget_type()

    def screenshot_widget_is_in_toolbar() -> bool:
        for action in widget.main_toolbar().actions():
            if isinstance(action, QWidgetAction) and cast(QWidgetAction, action).defaultWidget() == screenshot_widget:
                return True
        return False

    assert not screenshot_widget_is_in_toolbar()
    widget.screenshot_widget = screenshot_widget
    assert screenshot_widget_is_in_toolbar()
    widget.screenshot_widget = None if new_widget_type is None else new_widget_type()
    assert not screenshot_widget_is_in_toolbar()


@pytest.mark.parametrize("version", [
    "0.1.0",
    "1.2",
    "3.5-beta4",
    "4.0a0.post0+43ebdc",
])
def test_app_frame_app_version_prop(version, qtbot: QtBot):
    widget = ApplicationFrame()
    qtbot.add_widget(widget)
    assert widget.appVersion == "0.0.1"
    widget.appVersion = version
    assert widget.appVersion == version


@pytest.mark.parametrize("other_toolbars,expected_initial_count,create_if_not_exist,expected_new_count,expected_returned_none", [
    ([], 0, True, 1, False),
    (["one"], 1, True, 2, False),
    (["one", "two"], 2, True, 3, False),
    ([], 0, False, 0, True),
    (["one"], 1, False, 1, True),
    (["one", "two"], 2, False, 2, True),
])
def test_app_frame_main_toolbar_creates_toolbar_if_did_not_exist(qtbot: QtBot, other_toolbars, expected_initial_count, expected_new_count,
                                                                 create_if_not_exist, expected_returned_none):
    widget = ApplicationFrame()
    qtbot.add_widget(widget)
    count_toolbars = lambda: len([w for w in widget.children() if isinstance(w, QToolBar)])
    assert count_toolbars() == 0
    for name in other_toolbars:
        widget.addToolBar(name)
    assert count_toolbars() == expected_initial_count
    main_toolbar = widget.main_toolbar(create=create_if_not_exist)
    assert count_toolbars() == expected_new_count
    if expected_returned_none:
        assert main_toolbar is None
    else:
        assert main_toolbar is not None
        assert main_toolbar in widget.children()


@pytest.mark.parametrize("other_toolbars", [
    [],
    ["one"],
    ["one", "two"],
])
@pytest.mark.parametrize("create_if_not_exist", [True, False])
def test_app_frame_main_toolbar_does_not_create_toolbar_if_existed(qtbot: QtBot, create_if_not_exist, other_toolbars):
    widget = ApplicationFrame()
    qtbot.add_widget(widget)
    count_toolbars = lambda: len([w for w in widget.children() if isinstance(w, QToolBar)])
    main_toolbar = widget.main_toolbar(create=True)
    for name in other_toolbars:
        widget.addToolBar(name)
    orig_count = count_toolbars()
    assert main_toolbar in widget.children()
    new_returned_toolbar = widget.main_toolbar(create=create_if_not_exist)
    assert new_returned_toolbar == main_toolbar
    assert main_toolbar in widget.children()
    assert count_toolbars() == orig_count


@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
def test_app_frame_remove_toolbar_deletes_timing_bar_if_main_toolbar(qtbot: QtBot, widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    widget.timing_bar = widget_type()
    assert widget.useTimingBar is True
    widget.removeToolBar(widget.main_toolbar())
    assert widget.timing_bar is None
    assert widget.useTimingBar is False


@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
def test_app_frame_remove_toolbar_does_not_delete_timing_bar_if_not_main_toolbar(qtbot: QtBot, widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    another_toolbar = widget.addToolBar("Test toolbar")
    widget.timing_bar = widget_type()
    assert widget.useTimingBar is True
    widget.removeToolBar(another_toolbar)
    assert widget.timing_bar is not None
    assert widget.useTimingBar is True


@pytest.mark.parametrize("view_menu_exists,log_console_exist,timing_bar_exists,should_add_log_console_action,should_add_toolbar_action", [
    (True, True, True, True, True),
    (True, True, False, True, False),
    (True, False, True, False, True),
    (True, False, False, False, False),
    (False, True, True, False, False),
    (False, True, False, False, False),
    (False, False, True, False, False),
    (False, False, False, False, False),
])
def test_app_frame_set_menu_bar_populates_toggle_view_actions(qtbot: QtBot, view_menu_exists, log_console_exist, timing_bar_exists,
                                                              should_add_log_console_action, should_add_toolbar_action):
    widget = ApplicationFrame(use_timing_bar=timing_bar_exists, use_log_console=log_console_exist)
    qtbot.add_widget(widget)
    menu_bar = QMenuBar()
    if view_menu_exists:
        menu_bar.addMenu("View")
    widget.setMenuBar(menu_bar)

    for main_menu in menu_bar.actions():
        if main_menu.text() == "View" and main_menu.menu() is not None:
            action_names = [a.text() for a in main_menu.menu().actions()]
            assert ("Toggle Primary Toolbar" in action_names) == should_add_toolbar_action
            assert ("Toggle Log Console" in action_names) == should_add_log_console_action


@pytest.mark.parametrize("log_console_exist,should_add_log_console_action", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("timing_bar_exists,should_add_toolbar_action", [
    (True, True),
    (False, False),
])
@mock.patch("pyjapc.PyJapc")  # Avoid TimingBar making connections
def test_app_frame_show_event_populates_toggle_view_actions(_, qtbot: QtBot, log_console_exist,
                                                            timing_bar_exists, should_add_log_console_action,
                                                            should_add_toolbar_action):
    widget = ApplicationFrame(use_timing_bar=timing_bar_exists, use_log_console=log_console_exist)
    qtbot.add_widget(widget)
    assert "View" not in [a.text() for a in widget.menuBar().actions()]
    view_menu = widget.menuBar().addMenu("View")
    assert "Toggle Primary Toolbar" not in [a.text() for a in view_menu.actions()]
    assert "Toggle Log Console" not in [a.text() for a in view_menu.actions()]
    with qtbot.wait_exposed(widget):
        widget.show()
    assert ("Toggle Primary Toolbar" in (a.text() for a in view_menu.actions())) == should_add_toolbar_action
    assert ("Toggle Log Console" in (a.text() for a in view_menu.actions())) == should_add_log_console_action


@pytest.mark.parametrize("input,expected_output", [
    ("View", "View"),
    ("&View", "View"),
    ("View&", "View"),
    ("V&iew", "View"),
    ("Vi&ew", "View"),
    ("Vie&w", "View"),
    ("&&View", "&&View"),
    ("V&&iew", "V&&iew"),
    ("Vi&&ew", "Vi&&ew"),
    ("Vie&&w", "Vie&&w"),
    ("View&&", "View&&"),
    ("&& View", "&& View"),
    ("& View", " View"),
    ("&Vi&&ew", "Vi&&ew"),
    ("V&&ie&w", "V&&iew"),
])
def test_strip_mnemonics(input, expected_output):
    assert _strip_mnemonics(input) == expected_output
