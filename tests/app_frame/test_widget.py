import pytest
from pytestqt.qtbot import QtBot
from unittest import mock
from typing import Optional, cast
from qtpy.QtWidgets import QWidget, QDockWidget, QMenu, QWidgetAction, QToolBar, QMenuBar
from accwidgets.app_frame import ApplicationFrame
from accwidgets.log_console import LogConsoleDock, LogConsole
from accwidgets.timing_bar import TimingBar
from accwidgets.app_frame._frame import _strip_mnemonics


@pytest.mark.parametrize("use_timing_bar,use_console,expect_timing_bar_exist,expect_log_console_exist", [
    (True, True, True, True),
    (False, True, False, True),
    (True, False, True, False),
    (False, False, False, False),
])
def test_app_frame_init_use_subwidgets(qtbot: QtBot, use_console, use_timing_bar, expect_log_console_exist,
                                       expect_timing_bar_exist):
    widget = ApplicationFrame(use_timing_bar=use_timing_bar, use_log_console=use_console)
    qtbot.add_widget(widget)
    if expect_timing_bar_exist:
        assert widget.timing_bar is not None
    else:
        assert widget.timing_bar is None
    if expect_log_console_exist:
        assert widget.log_console is not None
    else:
        assert widget.log_console is None


def test_app_frame_default_subwidget_usage_flags(qtbot: QtBot):
    widget = ApplicationFrame()
    qtbot.add_widget(widget)
    assert widget.useTimingBar is False
    assert widget.useLogConsole is False


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
        for action in widget.main_toolbar(create=True).actions():
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
    assert len(main_toolbar.actions()) == 1
    assert isinstance(main_toolbar.actions()[0], QWidgetAction)
    assert cast(QWidgetAction, main_toolbar.actions()[0]).defaultWidget() == new_timing_bar


@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
@pytest.mark.parametrize("another_toolbar_exists", [True, False])
def test_app_frame_set_timing_bar_adds_toggle_action_when_toolbar_gets_created(qtbot: QtBot, widget_type, another_toolbar_exists):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    assert widget.main_toolbar(create=False) is None
    new_timing_bar = widget_type()

    view_menu = widget.menuBar().addMenu("View")

    def toggle_actions_count() -> int:
        return len([a for a in view_menu.actions() if a.text() == "Toggle Primary Toolbar"])

    if another_toolbar_exists:
        widget.addToolBar("Another toolbar")

    assert toggle_actions_count() == 0
    widget.timing_bar = new_timing_bar
    assert toggle_actions_count() == 1


@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
def test_app_frame_set_timing_bar_adds_new_widget_when_only_main_toolbar_exists(qtbot: QtBot, widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    main_toolbar = widget.main_toolbar(create=True)
    assert len(main_toolbar.actions()) == 0
    new_timing_bar = widget_type()
    widget.timing_bar = new_timing_bar
    assert len(main_toolbar.actions()) == 1
    assert isinstance(main_toolbar.actions()[0], QWidgetAction)
    assert cast(QWidgetAction, main_toolbar.actions()[0]).defaultWidget() == new_timing_bar


@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
def test_app_frame_set_timing_bar_adds_new_widget_when_multiple_toolbars_exist(qtbot: QtBot, widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    another_toolbar = widget.addToolBar("Another toolbar")
    main_toolbar = widget.main_toolbar(create=True)
    assert len(main_toolbar.actions()) == 0
    assert len(another_toolbar.actions()) == 0
    new_timing_bar = widget_type()
    widget.timing_bar = new_timing_bar
    assert len(main_toolbar.actions()) == 1
    assert len(another_toolbar.actions()) == 0
    assert isinstance(main_toolbar.actions()[0], QWidgetAction)
    assert cast(QWidgetAction, main_toolbar.actions()[0]).defaultWidget() == new_timing_bar


@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
def test_app_frame_set_timing_bar_adds_new_widget_when_main_toolbar_is_not_empty(qtbot: QtBot, widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    main_toolbar = widget.main_toolbar(create=True)
    main_toolbar.addAction("Test action")
    assert len(main_toolbar.actions()) == 1
    assert not isinstance(main_toolbar.actions()[0], QWidgetAction)
    assert main_toolbar.actions()[0].text() == "Test action"
    new_timing_bar = widget_type()
    widget.timing_bar = new_timing_bar
    assert widget.main_toolbar(create=False) is not None
    assert len(main_toolbar.actions()) == 2
    assert isinstance(main_toolbar.actions()[0], QWidgetAction)
    assert not isinstance(main_toolbar.actions()[1], QWidgetAction)
    assert cast(QWidgetAction, main_toolbar.actions()[0]).defaultWidget() == new_timing_bar
    assert main_toolbar.actions()[1].text() == "Test action"


@pytest.mark.parametrize("has_additional_widgets,new_widget_type,should_remove_toolbar", [
    (False, None, True),
    (True, None, False),
    (False, QWidget, False),
    (True, QWidget, False),
    (False, TimingBar, False),
    (True, TimingBar, False),
])
@pytest.mark.parametrize("widget_type", [QWidget, TimingBar])
def test_app_frame_set_timing_bar_to_none_deletes_main_toolbar_if_last_widget(qtbot: QtBot, widget_type, has_additional_widgets,
                                                                              should_remove_toolbar, new_widget_type):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    assert widget.main_toolbar(create=False) is None
    if has_additional_widgets:
        widget.main_toolbar().addAction("Test action")
    widget.timing_bar = widget_type()
    assert widget.main_toolbar(create=False) is not None
    main_toolbar = widget.main_toolbar(create=False)
    with qtbot.wait_signal(main_toolbar.destroyed, raising=False, timeout=100) as blocker:
        widget.timing_bar = None if new_widget_type is None else new_widget_type()
    if should_remove_toolbar:
        assert blocker.signal_triggered
        assert widget.main_toolbar(create=False) is None
    else:
        assert not blocker.signal_triggered
        assert widget.main_toolbar(create=False) is not None


def test_app_frame_set_timing_bar_to_none_deletes_main_toolbar_toggle_view_action_if_last_widget_and_menu_exists(qtbot: QtBot):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    widget.menuBar().addMenu("Useless")  # To make sure that it's not any menu that is picked up
    view_menu = widget.menuBar().addMenu("View")

    def toggle_actions_count() -> int:
        return len([a for a in view_menu.actions() if a.text() == "Toggle Primary Toolbar"])

    assert toggle_actions_count() == 0
    widget.timing_bar = TimingBar()
    assert toggle_actions_count() == 1
    widget.timing_bar = TimingBar()
    assert toggle_actions_count() == 1
    widget.timing_bar = None
    assert toggle_actions_count() == 0


def test_app_frame_set_timing_bar_main_toolbar_does_not_create_view_menu_if_not_exists(qtbot: QtBot):
    widget = ApplicationFrame(use_timing_bar=False)
    qtbot.add_widget(widget)
    widget.menuBar().addMenu("Useless")  # To make sure that it's not any menu that is picked up

    def get_view_menu() -> Optional[QMenu]:
        try:
            return next(iter(w for w in widget.menuBar().actions() if w.text() == "View"))
        except StopIteration:
            return None

    assert get_view_menu() is None
    widget.timing_bar = TimingBar()
    assert get_view_menu() is None
    widget.timing_bar = None
    assert get_view_menu() is None


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
