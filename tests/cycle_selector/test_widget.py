import pytest
from unittest import mock
from asyncio import CancelledError
from pytestqt.qtbot import QtBot
from qtpy.QtCore import QObject
from qtpy.QtWidgets import QComboBox
from accwidgets.cycle_selector import (CycleSelector, CycleSelectorValue, CycleSelectorConnectionError,
                                       CycleSelectorModel)
from accwidgets.cycle_selector._widget import (filter_data, sort_data, convert_data, _STACK_COMPLETE, _STACK_LOADING,
                                               _STACK_ERROR, item_idx)
from ..async_shim import AsyncMock


@pytest.fixture
def populate_widget_menus(event_loop):

    def wrapper(widget: CycleSelector, data_tree: Dict[str, Dict[str, List[str]]]):
        with mock.patch("accwidgets.cycle_selector._model.CycleSelectorModel.fetch", new_callable=AsyncMock) as fetch:
            fetch.return_value = data_tree
            fetch.assert_not_awaited()
            event_loop.run_until_complete(widget._fetch_data())
            fetch.assert_awaited_once()

    return wrapper


def test_cycle_selector_init_default_props(qtbot: QtBot):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    assert widget.requireSelector is False
    assert widget.value is None
    assert widget.enforcedDomain is None
    assert widget.onlyUsers is False
    assert widget.allowAllUser is True


def test_cycle_selector_init_connects_implicit_model(qtbot: QtBot):
    view = CycleSelector()
    qtbot.add_widget(view)
    # Note there's no signals to connect, so we verify by checking ownership
    # (assuming that _connect_model sets ownership)
    assert view.model.parent() is view


def test_cycle_selector_init_connects_provided_model(qtbot: QtBot):
    model = CycleSelectorModel()
    # Note there's no signals to connect, so we verify by checking ownership
    # (assuming that _connect_model sets ownership)
    view = CycleSelector(model=model)
    qtbot.add_widget(view)
    assert model.parent() is view


def test_cycle_selector_set_model_changes_ownership(qtbot: QtBot):
    view = CycleSelector()
    qtbot.add_widget(view)
    model = CycleSelectorModel()
    assert model.parent() != view
    view.model = model
    assert model.parent() == view


@pytest.mark.parametrize("belongs_to_view,should_destroy", [
    (True, True),
    (False, False),
])
def test_cycle_selector_destroys_old_model_when_disconnecting(qtbot: QtBot, belongs_to_view, should_destroy):
    model = CycleSelectorModel()
    view = CycleSelector(model=model)
    qtbot.add_widget(view)
    assert model.parent() == view
    random_parent = QObject()
    if not belongs_to_view:
        model.setParent(random_parent)

    with mock.patch.object(model, "deleteLater") as deleteLater:
        view.model = CycleSelectorModel()
        if should_destroy:
            deleteLater.assert_called_once()
            assert model.parent() is None
        else:
            deleteLater.assert_not_called()
            assert model.parent() is random_parent


@pytest.mark.parametrize("orig_val,new_val,expect_no_selector,expected_machine,expected_group,expected_line", [
    (None, None, True, "LHC", "USER", "ALL"),
    (None, "LHC.USER.ALL", False, "LHC", "USER", "ALL"),
    (None, CycleSelectorValue(domain="LHC", group="USER", line="ALL"), False, "LHC", "USER", "ALL"),
    (None, "SPS.PARTY.ION", False, "SPS", "PARTY", "ION"),
    (None, CycleSelectorValue(domain="SPS", group="PARTY", line="ION"), False, "SPS", "PARTY", "ION"),
    ("LHC.USER.ALL", None, True, "LHC", "USER", "ALL"),
    ("LHC.USER.ALL", "LHC.USER.ALL", False, "LHC", "USER", "ALL"),
    ("LHC.USER.ALL", CycleSelectorValue(domain="LHC", group="USER", line="ALL"), False, "LHC", "USER", "ALL"),
    ("LHC.USER.ALL", "SPS.PARTY.ION", False, "SPS", "PARTY", "ION"),
    ("LHC.USER.ALL", CycleSelectorValue(domain="SPS", group="PARTY", line="ION"), False, "SPS", "PARTY", "ION"),
    ("SPS.PARTY.ION", None, True, "SPS", "PARTY", "ION"),
    ("SPS.PARTY.ION", "LHC.USER.ALL", False, "LHC", "USER", "ALL"),
    ("SPS.PARTY.ION", CycleSelectorValue(domain="LHC", group="USER", line="ALL"), False, "LHC", "USER", "ALL"),
    ("SPS.PARTY.ION", "SPS.PARTY.ION", False, "SPS", "PARTY", "ION"),
    ("SPS.PARTY.ION", CycleSelectorValue(domain="SPS", group="PARTY", line="ION"), False, "SPS", "PARTY", "ION"),
])
@pytest.mark.parametrize("designer", [True, False])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_value_setter_udpates_ui(is_designer, designer, orig_val, new_val, expected_line, expected_group,
                                                expected_machine, expect_no_selector, qtbot: QtBot,
                                                populate_widget_menus):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {
        "SPS": {
            "PARTY": ["ION", "PROTON", "ALL"],
            "USER": ["LHC", "ALL"],
        },
        "LHC": {
            "USER": ["ALL", "MD1"],
        },
    })
    widget.value = orig_val
    widget.value = new_val
    assert widget._ui.no_selector.isChecked() == expect_no_selector
    assert widget._ui.machine_combo.currentText() == expected_machine
    assert widget._ui.group_combo.currentText() == expected_group
    assert widget._ui.line_combo.currentText() == expected_line
    assert widget._ui.machine_combo.isEnabled() != expect_no_selector
    assert widget._ui.group_combo.isEnabled() != expect_no_selector
    assert widget._ui.line_combo.isEnabled() != expect_no_selector


@pytest.mark.parametrize("designer,value,expected_error,expect_value_set", [
    (False, None, None, True),
    (False, "", 'Incorrect string format passed \\(""\\), must be of format DOMAIN.GROUP.LINE', False),
    (False, "LHC", 'Incorrect string format passed \\("LHC"\\), must be of format DOMAIN.GROUP.LINE', False),
    (False, "LHC.", 'Incorrect string format passed \\("LHC."\\), must be of format DOMAIN.GROUP.LINE', False),
    (False, "LHC.USER.", 'Incorrect string format passed \\("LHC.USER."\\), must be of format DOMAIN.GROUP.LINE', False),
    (False, "LHC.USER.A", None, True),
    (False, CycleSelectorValue(domain="LHC", group="USER", line="ALL"), None, True),
    (False, CycleSelectorValue(domain="LHC", group="USER", line=""), None, True),
    (True, None, None, True),
    (True, "", None, False),
    (True, "LHC", None, False),
    (True, "LHC.", None, False),
    (True, "LHC.USER.", None, False),
    (True, "LHC.USER.A", None, True),
    (True, CycleSelectorValue(domain="LHC", group="USER", line="ALL"), None, True),
    (True, CycleSelectorValue(domain="LHC", group="USER", line=""), None, True),
])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_value_setter_with_wrong_format_no_throw_in_designer(is_designer, expect_value_set, value,
                                                                            expected_error, qtbot: QtBot, designer):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    if expected_error is None:
        widget.value = value
    else:
        with pytest.raises(ValueError, match=expected_error):
            widget.value = value
    if expect_value_set:
        assert str(widget.value) == str(value)
    else:
        assert widget.value is None


@pytest.mark.parametrize("enforced_domain,value,expected_error,expect_value_set", [
    ("LHC", None, None, True),
    ("LHC", "LHC.USER.ALL", None, True),
    ("LHC", CycleSelectorValue(domain="LHC", group="USER", line="ALL"), None, True),
    ("LHC", "SPS.PARTY.ION", 'Given cycle selector "SPS.PARTY.ION" does not belong to the enforced domain "LHC"', False),
    ("LHC", CycleSelectorValue(domain="SPS", group="PARTY", line="ION"), 'Given cycle selector "SPS.PARTY.ION" does not belong to the enforced domain "LHC"', False),
    ("CPS", "LHC.USER.ALL", 'Given cycle selector "LHC.USER.ALL" does not belong to the enforced domain "CPS"', False),
    ("CPS", CycleSelectorValue(domain="LHC", group="USER", line="ALL"), 'Given cycle selector "LHC.USER.ALL" does not belong to the enforced domain "CPS"', False),
])
@pytest.mark.parametrize("designer", [True, False])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_value_setter_fails_with_enforced_domain(is_designer, value, enforced_domain, expect_value_set,
                                                                expected_error, qtbot, designer):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    widget.enforcedDomain = enforced_domain
    if expected_error is None:
        widget.value = value
    else:
        with pytest.raises(ValueError, match=expected_error):
            widget.value = value
    if expect_value_set:
        assert str(widget.value) == str(value)
    else:
        assert widget.value is None


@pytest.mark.parametrize("orig_sel,new_sel,expect_noop", [
    (None, None, True),
    (None, "LHC.USER.ALL", False),
    (None, CycleSelectorValue(domain="LHC", group="USER", line="ALL"), False),
    ("LHC.USER.ALL", None, False),
    ("LHC.USER.ALL", "LHC.USER.ALL", True),
    ("LHC.USER.ALL", CycleSelectorValue(domain="LHC", group="USER", line="ALL"), True),
    ("LHC.USER.ALL", "SPS.PARTY.ION", False),
    ("LHC.USER.ALL", CycleSelectorValue(domain="SPS", group="PARTY", line="ION"), False),
])
def test_cycle_selector_value_setter_noop(orig_sel, new_sel, expect_noop, qtbot: QtBot, populate_widget_menus):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {
        "SPS": {
            "PARTY": ["ION", "PROTON", "ALL"],
            "USER": ["LHC", "ALL"],
        },
        "LHC": {
            "USER": ["ALL", "MD1"],
        },
    })
    widget.value = orig_sel
    with qtbot.wait_signal(widget.valueChanged, raising=False, timeout=100) as blocker:
        widget.value = new_sel
    if expect_noop:
        assert not blocker.signal_triggered
    else:
        assert blocker.args == [str(new_sel or "")]


@pytest.mark.parametrize("data_exists,expect_renders", [
    (True, True),
    (False, False),
])
def test_cycle_selector_setter_renders_on_demand(data_exists, expect_renders, qtbot: QtBot, populate_widget_menus):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    if data_exists:
        populate_widget_menus(widget, {
            "SPS": {
                "PARTY": ["ION", "PROTON", "ALL"],
                "USER": ["LHC", "ALL"],
            },
            "LHC": {
                "USER": ["ALL", "MD1"],
            },
        })
    with mock.patch.object(widget, "_render_data_if_needed") as render_data_if_needed:
        widget.value = CycleSelectorValue(domain="SPS", group="PARTY", line="ION")
        if expect_renders:
            render_data_if_needed.assert_called_once()
        else:
            render_data_if_needed.assert_not_called()


@pytest.mark.parametrize("domain,expect_lines_only_users,expect_lines_all", [
    ("LHC", ["USER"], ["USER"]),
    ("SPS", ["USER"], ["USER", "", "PARTY"]),
])
def test_cycle_selector_only_users_prop(populate_widget_menus, qtbot: QtBot, domain, expect_lines_all,
                                        expect_lines_only_users):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {
        "SPS": {
            "PARTY": ["ION", "PROTON", "ALL"],
            "USER": ["LHC", "ALL"],
        },
        "LHC": {
            "USER": ["ALL", "MD1"],
        },
    })

    def group_options():
        widget._do_render_data(widget._processed_data(), domain, None, None)
        return [widget._ui.group_combo.itemText(i) for i in range(widget._ui.group_combo.count())]

    assert group_options() == expect_lines_all
    assert widget.onlyUsers is False
    widget.onlyUsers = True
    assert group_options() == expect_lines_only_users
    assert widget.onlyUsers is True
    widget.onlyUsers = False
    assert group_options() == expect_lines_all
    assert widget.onlyUsers is False


@pytest.mark.parametrize("domain,expect_lines_with_all,expect_lines_without_all", [
    ("LHC", ["ALL", "", "MD1"], ["MD1"]),
    ("SPS", ["ALL", "", "LHC"], ["LHC"]),
])
@pytest.mark.parametrize("only_users", [True, False])
def test_cycle_selector_allow_all_prop(populate_widget_menus, qtbot: QtBot, domain, expect_lines_without_all,
                                       only_users, expect_lines_with_all):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {
        "SPS": {
            "PARTY": ["ION", "PROTON", "ALL"],
            "USER": ["LHC", "ALL"],
        },
        "LHC": {
            "USER": ["ALL", "MD1"],
        },
    })
    widget.onlyUsers = only_users

    def line_options():
        widget._do_render_data(widget._processed_data(), domain, None, None)
        return [widget._ui.line_combo.itemText(i) for i in range(widget._ui.line_combo.count())]

    assert line_options() == expect_lines_with_all
    assert widget.allowAllUser is True
    widget.allowAllUser = False
    assert line_options() == expect_lines_without_all
    assert widget.allowAllUser is False
    widget.allowAllUser = True
    assert line_options() == expect_lines_with_all
    assert widget.allowAllUser is True


def test_cycle_selector_require_selector_prop(populate_widget_menus, qtbot: QtBot):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}})
    widget.value = CycleSelectorValue(domain="LHC", group="USER", line="ALL")
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget._ui.no_selector.isVisible()
    assert not widget._ui.no_selector.isChecked()
    assert widget.requireSelector is False
    widget.requireSelector = True
    assert not widget._ui.no_selector.isVisible()
    assert widget.requireSelector is True
    widget.requireSelector = False
    assert widget._ui.no_selector.isVisible()
    assert widget.requireSelector is False


@pytest.mark.parametrize("value,designer,expect_error", [
    (None, True, False),
    (None, False, True),
    ("LHC.USER.ALL", True, False),
    ("LHC.USER.ALL", False, False),
])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_require_selector_setter_no_fail_in_designer(is_designer, value, designer, expect_error, qtbot,
                                                                    populate_widget_menus):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    widget.value = value
    populate_widget_menus(widget, {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}})
    assert widget.requireSelector is False
    if expect_error:
        with pytest.raises(ValueError, match="Cannot set requireSelector to True, because current value is None"):
            widget.requireSelector = True
    else:
        widget.requireSelector = True


@pytest.mark.parametrize("value,orig_combo,enforced_domain,expected_combo", [
    (None, "LHC", "LHC", "LHC"),
    (None, "LHC", "SPS", "SPS"),
    ("LHC.USER.ALL", "LHC", "LHC", "LHC"),
    ("SPS.PARTY.ION", "SPS", "SPS", "SPS"),
])
def test_cycle_selector_enforced_domain_prop(value, enforced_domain, orig_combo, expected_combo, qtbot,
                                             populate_widget_menus):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    widget.value = value
    populate_widget_menus(widget, {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}})
    assert widget._ui.machine_combo.currentText() == orig_combo
    widget.enforcedDomain = enforced_domain
    assert widget._ui.machine_combo.currentText() == expected_combo
    assert widget.enforcedDomain == enforced_domain


@pytest.mark.parametrize("designer,value,enforced_domain,expected_error", [
    (False, None, "LHC", None),
    (False, "LHC.USER.ALL", "LHC", None),
    (False, "SPS.PARTY.ION", "LHC", 'Cannot set enforcedDomain to LHC, because current value "SPS.PARTY.ION" is incompatible'),
    (False, "LHC.USER.LHC", "CPS", 'Cannot set enforcedDomain to CPS, because current value "LHC.USER.LHC" is incompatible'),
    (True, None, "LHC", None),
    (True, "LHC.USER.ALL", "LHC", None),
    (True, "SPS.PARTY.ION", "LHC", None),
    (True, "LHC.USER.LHC", "CPS", None),
])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_enforced_domain_fails_if_contradicts_existing_value(is_designer, value, enforced_domain,
                                                                            expected_error, qtbot, designer):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    widget.value = value
    if expected_error is None:
        widget.enforcedDomain = enforced_domain
    else:
        with pytest.raises(ValueError, match=expected_error):
            widget.enforcedDomain = enforced_domain


@pytest.mark.parametrize("data_exists,expect_fetches", [
    (True, False),
    (False, True),
])
@mock.patch("accwidgets.cycle_selector._widget.CycleSelector._render_data_if_needed")
@mock.patch("accwidgets.cycle_selector._widget.CycleSelector.refetch")
def test_cycle_selector_fetches_on_show(refetch, render_data, data_exists, expect_fetches, qtbot: QtBot):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    if data_exists:
        widget._orig_data = [("LHC", [("USER", ["ALL"])])]

    with qtbot.wait_exposed(widget):
        widget.show()
    if expect_fetches:
        refetch.assert_called_once()
        # This would be called originally from within refetch, but since it's mocked here, it's not called
        render_data.assert_not_called()
    else:
        refetch.assert_not_called()
        render_data.assert_called_once()


@mock.patch("accwidgets.cycle_selector._widget.CycleSelector._cancel_running_tasks")
def test_cycle_selector_stops_active_tasks_on_hide(cancel_running_tasks, qtbot: QtBot, event_loop):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    cancel_running_tasks.assert_not_called()
    widget.hide()
    cancel_running_tasks.assert_called_once()


def test_cycle_selector_on_fetch_rolls_back_ui_on_cancel(qtbot: QtBot, event_loop):
    widget = CycleSelector()
    qtbot.add_widget(widget)

    def side_effect():
        assert widget._ui.activity.animating
        assert widget._ui.stack.currentIndex() == _STACK_LOADING
        raise CancelledError

    with mock.patch("accwidgets.cycle_selector._model.CycleSelectorModel.fetch", new_callable=AsyncMock) as fetch:
        fetch.side_effect = side_effect
        event_loop.run_until_complete(widget._fetch_data())
        assert not widget._ui.activity.animating
        assert widget._ui.stack.currentIndex() == _STACK_COMPLETE


def test_cycle_selector_on_fetch_sets_ui_on_connection_error(qtbot: QtBot, event_loop):
    widget = CycleSelector()
    qtbot.add_widget(widget)

    with mock.patch("accwidgets.cycle_selector._model.CycleSelectorModel.fetch", new_callable=AsyncMock) as fetch:
        fetch.side_effect = CycleSelectorConnectionError("Test error")
        event_loop.run_until_complete(widget._fetch_data())
        assert not widget._ui.activity.animating
        assert widget._ui.stack.currentIndex() == _STACK_ERROR
        assert widget._ui.error.text() == "Test error"


def test_cycle_selector_on_fetch_sets_ui_on_empty(qtbot: QtBot, event_loop):
    widget = CycleSelector()
    qtbot.add_widget(widget)

    def side_effect():
        assert widget._ui.activity.animating
        assert widget._ui.stack.currentIndex() == _STACK_LOADING
        return {}

    with mock.patch("accwidgets.cycle_selector._model.CycleSelectorModel.fetch", new_callable=AsyncMock) as fetch:
        fetch.side_effect = side_effect
        event_loop.run_until_complete(widget._fetch_data())
        assert not widget._ui.activity.animating
        assert widget._ui.stack.currentIndex() == _STACK_ERROR
        assert widget._ui.error.text() == "Received empty data from CCDB"


def test_cycle_selector_on_fetch_success_sets_ui(qtbot: QtBot, event_loop):
    widget = CycleSelector()
    qtbot.add_widget(widget)

    def side_effect():
        assert widget._ui.activity.animating
        assert widget._ui.stack.currentIndex() == _STACK_LOADING
        return {"LHC": {"USER": ["ALL"]}}

    with mock.patch("accwidgets.cycle_selector._model.CycleSelectorModel.fetch", new_callable=AsyncMock) as fetch:
        fetch.side_effect = side_effect
        event_loop.run_until_complete(widget._fetch_data())
        assert not widget._ui.activity.animating
        assert widget._ui.stack.currentIndex() == _STACK_COMPLETE


@pytest.mark.parametrize("error_type", [TypeError, ValueError])
def test_cycle_selector_on_fetch_throws_on_unknown_error(error_type, qtbot: QtBot, event_loop):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    with mock.patch("accwidgets.cycle_selector._model.CycleSelectorModel.fetch", new_callable=AsyncMock) as fetch:
        fetch.side_effect = error_type("Test error")
        with pytest.raises(error_type, match="Test error"):
            event_loop.run_until_complete(widget._fetch_data())


@pytest.mark.parametrize("enforced_domain,value,expected_machine,expected_group,expected_line", [
    (None, "LHC.USER.ALL", "LHC", "USER", "ALL"),
    (None, "SPS.PARTY.PROTON", "SPS", "PARTY", "PROTON"),
    ("LHC", "LHC.USER.ALL", "LHC", "USER", "ALL"),
    ("SPS", "SPS.PARTY.PROTON", "SPS", "PARTY", "PROTON"),
])
@pytest.mark.parametrize("designer", [True, False])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_render_data_if_needed_preset_value(is_designer, designer, expected_group, expected_line,
                                                           expected_machine, populate_widget_menus, enforced_domain,
                                                           qtbot: QtBot, recwarn, value):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    widget.enforcedDomain = enforced_domain
    widget.value = value
    populate_widget_menus(widget, {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}})
    assert widget._ui.machine_combo.currentText() == expected_machine
    assert widget._ui.group_combo.currentText() == expected_group
    assert widget._ui.line_combo.currentText() == expected_line


@pytest.mark.parametrize("designer,enforced_domain,fetch_data,expected_machine,expected_group,expected_line", [
    (False, None, {"LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (False, "LHC", {"LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (False, "NOT_EXISTING", {"LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (False, "LHC", {"SPS": {"USER": ["ALL"]}}, "SPS", "USER", "ALL"),
    (False, None, {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (False, None, {"SPS": {"PARTY": ["ION", "PROTON"]}, "V": {"USER": ["ALL"]}}, "SPS", "PARTY", "ION"),
    (False, "LHC", {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (False, "NOT_EXISTING", {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (True, None, {"LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (True, "LHC", {"LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (True, "NOT_EXISTING", {"LHC": {"USER": ["ALL"]}}, "", "", ""),
    (True, "LHC", {"SPS": {"USER": ["ALL"]}}, "", "", ""),
    (True, None, {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (True, None, {"SPS": {"PARTY": ["ION", "PROTON"]}, "V": {"USER": ["ALL"]}}, "SPS", "PARTY", "ION"),
    (True, "LHC", {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}}, "LHC", "USER", "ALL"),
    (True, "NOT_EXISTING", {"SPS": {"PARTY": ["ION", "PROTON"]}, "LHC": {"USER": ["ALL"]}}, "", "", ""),
])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_render_data_if_needed_no_value(is_designer, designer, expected_group, expected_line,
                                                       expected_machine, populate_widget_menus, fetch_data,
                                                       enforced_domain, qtbot: QtBot, recwarn):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    widget.enforcedDomain = enforced_domain
    populate_widget_menus(widget, fetch_data)
    assert widget._ui.machine_combo.currentText() == expected_machine
    assert widget._ui.group_combo.currentText() == expected_group
    assert widget._ui.line_combo.currentText() == expected_line


@pytest.mark.parametrize("designer,enforced_domain,value,fetch_data,expected_warning", [
    (False, None, None, {"LHC": {"USER": ["ALL"]}}, None),
    (False, "LHC", None, {"LHC": {"USER": ["ALL"]}}, None),
    (False, "SPS", None, {"LHC": {"USER": ["ALL"]}}, "Wanted machine SPS does not exist in the list. Falling back to LHC"),
    (False, "NOT_EXISTING", None, {"LHC": {"USER": ["ALL"]}}, "Wanted machine NOT_EXISTING does not exist in the list. Falling back to LHC"),
    (False, None, "LHC.USER.LHC", {"LHC": {"USER": ["ALL"]}}, "Wanted line LHC does not exist in the list. Falling back to ALL"),
    (False, "LHC", "LHC.USER.LHC", {"LHC": {"USER": ["ALL"]}}, "Wanted line LHC does not exist in the list. Falling back to ALL"),
    (False, None, "SPS.USER.MD1", {"LHC": {"USER": ["ALL"]}}, "Wanted machine SPS does not exist in the list. Falling back to LHC"),
    (False, None, "SPS.USER.MD1", {"LHC": {"PARTY": ["ION"]}}, "Wanted machine SPS does not exist in the list. Falling back to LHC"),
    (False, None, "SPS.USER.MD1", {"SPS": {"PARTY": ["ION"]}}, "Wanted line MD1 does not exist in the list. Falling back to ION"),
    (False, None, "SPS.PARTY.ION", {"SPS": {"USER": ["MD1"]}}, "Wanted group PARTY does not exist in the list. Falling back to USER"),
    (False, None, "SPS.PARTY.ION", {"SPS": {}}, "Groups corresponding to the machine SPS are empty. UI bails out."),
    (False, "SPS", "SPS.PARTY.ION", {"SPS": {}}, "Groups corresponding to the machine SPS are empty. UI bails out."),
    (False, None, "SPS.USER.MD1", {"SPS": {"USER": []}}, "Lines corresponding to the group SPS.USER are empty. UI bails out."),
    (False, "SPS", "SPS.USER.MD1", {"SPS": {"USER": []}}, "Lines corresponding to the group SPS.USER are empty. UI bails out."),
    (True, None, None, {"LHC": {"USER": ["ALL"]}}, None),
    (True, "LHC", None, {"LHC": {"USER": ["ALL"]}}, None),
    (True, "SPS", None, {"LHC": {"USER": ["ALL"]}}, None),
    (True, "NOT_EXISTING", None, {"LHC": {"USER": ["ALL"]}}, None),
    (True, None, "LHC.USER.LHC", {"LHC": {"USER": ["ALL"]}}, None),
    (True, "LHC", "LHC.USER.LHC", {"LHC": {"USER": ["ALL"]}}, None),
    (True, None, "SPS.USER.MD1", {"LHC": {"USER": ["ALL"]}}, None),
    (True, None, "SPS.USER.MD1", {"LHC": {"PARTY": ["ION"]}}, None),
    (True, None, "SPS.USER.MD1", {"SPS": {"PARTY": ["ION"]}}, None),
    (True, None, "SPS.PARTY.ION", {"SPS": {"USER": ["MD1"]}}, None),
    (True, None, "SPS.PARTY.ION", {"SPS": {}}, "Groups corresponding to the machine SPS are empty. UI bails out."),
    (True, "SPS", "SPS.PARTY.ION", {"SPS": {}}, "Groups corresponding to the machine SPS are empty. UI bails out."),
    (True, None, "SPS.USER.MD1", {"SPS": {"USER": []}}, "Lines corresponding to the group SPS.USER are empty. UI bails out."),
    (True, "SPS", "SPS.USER.MD1", {"SPS": {"USER": []}}, "Lines corresponding to the group SPS.USER are empty. UI bails out."),
])
@mock.patch("accwidgets.cycle_selector._widget.is_designer")
def test_cycle_selector_render_data_if_needed_warns(is_designer, designer, enforced_domain, value, qtbot: QtBot,
                                                    recwarn, populate_widget_menus, fetch_data, expected_warning):
    is_designer.return_value = designer
    widget = CycleSelector()
    qtbot.add_widget(widget)
    widget.enforcedDomain = enforced_domain
    widget.value = value
    populate_widget_menus(widget, fetch_data)
    if expected_warning is None:
        relevant_warnings = [w for w in recwarn if w.filename.endswith("accwidgets/cycle_selector/_widget.py")]
        assert len(relevant_warnings) == 0, list(reversed(relevant_warnings)).pop().message
    else:
        with pytest.warns(UserWarning, match=expected_warning):
            widget._render_data_if_needed()


def test_cycle_selector_machine_combo_populates_dependants(qtbot: QtBot, populate_widget_menus):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {
        "LHC": {"PARTY": ["ION", "PROTON"], "USER": ["LHC1", "LHC2"]},
        "SPS": {"PARTY": ["ION", "PROTON"], "USER": ["MD1", "MD2"]},
    })
    widget._ui.no_selector.setChecked(False)
    assert widget._ui.machine_combo.currentText() == "LHC"
    assert widget._ui.group_combo.currentText() == "USER"
    assert widget._ui.line_combo.currentText() == "LHC1"
    assert widget.value == CycleSelectorValue(domain="LHC", group="USER", line="LHC1")
    with qtbot.wait_signal(widget.valueChanged) as blocker:
        widget._ui.machine_combo.setCurrentText("SPS")
        widget._on_machine_selected(widget._ui.machine_combo.currentIndex())  # setCurrentText does not trigger "activated" signal
    assert widget._ui.group_combo.currentText() == "USER"
    assert widget._ui.line_combo.currentText() == "MD1"
    assert blocker.args == ["SPS.USER.MD1"]
    assert widget.value == CycleSelectorValue(domain="SPS", group="USER", line="MD1")


def test_cycle_selector_group_combo_populates_dependants(qtbot: QtBot, populate_widget_menus):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {"LHC": {"USER": ["LHC1", "LHC2"], "PARTY": ["ION", "PROTON"]}})
    widget._ui.no_selector.setChecked(False)
    assert widget._ui.group_combo.currentText() == "USER"
    assert widget._ui.line_combo.currentText() == "LHC1"
    assert widget.value == CycleSelectorValue(domain="LHC", group="USER", line="LHC1")
    with qtbot.wait_signal(widget.valueChanged) as blocker:
        widget._ui.group_combo.setCurrentText("PARTY")
        # hardcode index (we can't use currentIndex(), because it gets skewed by separator in the menu)
        widget._on_group_selected(1)  # setCurrentText does not trigger "activated" signal
    assert widget._ui.line_combo.currentText() == "ION"
    assert blocker.args == ["LHC.PARTY.ION"]
    assert widget.value == CycleSelectorValue(domain="LHC", group="PARTY", line="ION")


def test_cycle_selector_line_combo_fires_signal(qtbot: QtBot, populate_widget_menus):
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {"LHC": {"USER": ["LHC1", "LHC2"]}})
    assert widget._ui.line_combo.currentText() == "LHC1"
    widget._ui.no_selector.setChecked(False)
    assert widget.value == CycleSelectorValue(domain="LHC", group="USER", line="LHC1")
    with qtbot.wait_signal(widget.valueChanged) as blocker:
        widget._ui.line_combo.setCurrentText("LHC2")
        widget._on_line_selected()  # setCurrentText does not trigger "activated" signal
    assert blocker.args == ["LHC.USER.LHC2"]
    assert widget.value == CycleSelectorValue(domain="LHC", group="USER", line="LHC2")


def test_cycle_selector_toggle_selector(qtbot: QtBot, populate_widget_menus):
    lhc_sel = CycleSelectorValue(domain="LHC", group="USER", line="LHC")
    widget = CycleSelector()
    qtbot.add_widget(widget)
    populate_widget_menus(widget, {"LHC": {"USER": ["LHC"]}})
    assert widget._ui.no_selector.isChecked()
    assert not widget._ui.machine_combo.isEnabled()
    assert not widget._ui.group_combo.isEnabled()
    assert not widget._ui.line_combo.isEnabled()
    assert widget.value is None
    with qtbot.wait_signal(widget.valueChanged) as blocker:
        widget._ui.no_selector.toggle()
    assert blocker.args == [str(lhc_sel)]
    assert widget.value == lhc_sel
    assert not widget._ui.no_selector.isChecked()
    assert widget._ui.machine_combo.isEnabled()
    assert widget._ui.group_combo.isEnabled()
    assert widget._ui.line_combo.isEnabled()
    with qtbot.wait_signal(widget.valueChanged) as blocker:
        widget._ui.no_selector.toggle()
    assert blocker.args == [""]
    assert widget.value is None
    assert widget._ui.no_selector.isChecked()
    assert not widget._ui.machine_combo.isEnabled()
    assert not widget._ui.group_combo.isEnabled()
    assert not widget._ui.line_combo.isEnabled()


@pytest.mark.parametrize("items,search,expected_index", [
    ([], "One", -1),
    ([None], "One", -1),
    (["One", "Two"], "One", 0),
    (["One", "Two"], "Two", 1),
    (["One", None, "Two"], "One", 0),
    (["One", None, "Two"], "Two", 1),
    ([None, "One", None, None, "Two"], "Two", 1),
    (["One", None, "Two"], "Three", -1),
])
def test_item_idx(items, search, expected_index, qtbot: QtBot):
    widget = QComboBox()
    qtbot.add_widget(widget)
    for i, name in enumerate(items):
        if name is None:
            widget.insertSeparator(i)
        else:
            widget.addItem(name)
    assert item_idx(widget, search) == expected_index


def test_convert_data():
    data = {
        "LHC": {
            "PARTY": ["ION", "PROTON"],
            "USER": ["ALL", "LHC"],
        },
        "SPS": {
            "USER": ["ALL", "MD3", "MD1", "MD2"],
        },
    }
    assert convert_data(data) == [
        ("LHC", [("PARTY", ["ION", "PROTON"]), ("USER", ["ALL", "LHC"])]),
        ("SPS", [("USER", ["ALL", "MD3", "MD1", "MD2"])]),
    ]


@pytest.mark.parametrize("allow_all_user,only_users,data,expected_res", [
    (True, True,
     [
         ("LHC", [("PARTY", ["ION", "PROTON"]), ("USER", ["ALL", "LHC"])]),
         ("SPS", [("USER", ["ALL", "MD3", "MD1", "MD2"])]),
     ],
     [
         ("LHC", [("USER", ["ALL", "LHC"])]),
         ("SPS", [("USER", ["ALL", "MD3", "MD1", "MD2"])]),
     ],
     ),
    (True, False,
     [
         ("LHC", [("USER", ["ALL", "LHC"]), ("PARTY", ["ION", "PROTON"])]),
         ("SPS", [("USER", ["ALL", "MD3", "MD1", "MD2"])]),
     ],
     [
         ("LHC", [("USER", ["ALL", "LHC"]), ("PARTY", ["ION", "PROTON"])]),
         ("SPS", [("USER", ["ALL", "MD3", "MD1", "MD2"])]),
     ],
     ),
    (False, True,
     [
         ("LHC", [("USER", ["ALL", "LHC"]), ("PARTY", ["ION", "PROTON"])]),
         ("SPS", [("USER", ["ALL", "MD3", "MD1", "MD2"])]),
     ],
     [
         ("LHC", [("USER", ["LHC"])]),
         ("SPS", [("USER", ["MD3", "MD1", "MD2"])]),
     ],
     ),
    (False, False,
     [
         ("LHC", [("USER", ["ALL", "LHC"]), ("PARTY", ["ION", "PROTON"])]),
         ("SPS", [("USER", ["ALL", "MD3", "MD1", "MD2"])]),
     ],
     [
         ("LHC", [("USER", ["LHC"]), ("PARTY", ["ION", "PROTON"])]),
         ("SPS", [("USER", ["MD3", "MD1", "MD2"])]),
     ],
     ),
    (False, False,
     [
         ("LHC", [("USER", ["ALL", "LHC"]), ("PARTY", ["ION", "PROTON", "ALL"])]),
     ],
     [
         ("LHC", [("USER", ["LHC"]), ("PARTY", ["ION", "PROTON", "ALL"])]),
     ],
     ),
])
def test_filter_data(data, allow_all_user, only_users, expected_res):
    res = filter_data(data, allow_all_user=allow_all_user, only_users=only_users)
    assert res == expected_res


@pytest.mark.parametrize("data,expected_res", [
    ([], []),
    ([("one", [])], [("one", [])]),
    ([("one", []), ("two", [])], [("one", []), ("two", [])]),
    ([("two", []), ("one", [])], [("one", []), ("two", [])]),
    (
        [
            ("c", [("cb", ["cba", "cbc", "cbb"]), ("ca", ["caa", "cac"])]),
            ("a", [("ab", ["aba", "abc", "abb"]), ("aa", ["aaa", "aac"])]),
        ],
        [
            ("a", [("aa", ["aaa", "aac"]), ("ab", ["aba", "abb", "abc"])]),
            ("c", [("ca", ["caa", "cac"]), ("cb", ["cba", "cbb", "cbc"])]),
        ],
    ),
])
def test_sort_data(data, expected_res):
    sort_data(data)
    assert data == expected_res
