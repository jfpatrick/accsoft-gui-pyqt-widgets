import pytest
from datetime import datetime
from unittest import mock
from pytestqt.qtbot import QtBot
from dateutil.tz import UTC, tzoffset
from dateutil.parser import isoparse
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QPalette
from accwidgets.timing_bar import TimingBarModel, TimingBar, TimingBarDomain
from accwidgets.timing_bar._model import TimingUpdate
from .fixtures import *  # noqa: F401,F403


def test_timing_bar_set_model_changes_ownership(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    model = TimingBarModel()
    assert model.parent() != view
    view.model = model
    assert model.parent() == view


def test_timing_bar_set_model_disconnects_old_model(qtbot):
    model = TimingBarModel()
    view = TimingBar(model=model)
    qtbot.add_widget(view)
    assert model.receivers(model.timingUpdateReceived) > 0
    assert model.receivers(model.timingErrorReceived) > 0
    assert model.receivers(model.domainNameChanged) > 0
    view.model = TimingBarModel()
    assert model.receivers(model.timingUpdateReceived) == 0
    assert model.receivers(model.timingErrorReceived) == 0
    assert model.receivers(model.domainNameChanged) == 0


def test_timing_bar_set_model_connects_new_model(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    model = TimingBarModel()
    assert model.receivers(model.timingUpdateReceived) == 0
    assert model.receivers(model.timingErrorReceived) == 0
    assert model.receivers(model.domainNameChanged) == 0
    view.model = model
    assert model.receivers(model.timingUpdateReceived) > 0
    assert model.receivers(model.timingErrorReceived) > 0
    assert model.receivers(model.domainNameChanged) > 0


def test_timing_bar_init_connects_provided_model(qtbot):
    model = TimingBarModel()
    assert model.receivers(model.timingUpdateReceived) == 0
    assert model.receivers(model.timingErrorReceived) == 0
    assert model.receivers(model.domainNameChanged) == 0
    view = TimingBar(model=model)
    qtbot.add_widget(view)
    assert model.receivers(model.timingUpdateReceived) > 0
    assert model.receivers(model.timingErrorReceived) > 0
    assert model.receivers(model.domainNameChanged) > 0


def test_timing_bar_init_creates_and_connects_default_model(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    assert view.model is not None
    assert view.model.receivers(view.model.timingUpdateReceived) > 0
    assert view.model.receivers(view.model.timingErrorReceived) > 0
    assert view.model.receivers(view.model.domainNameChanged) > 0


@pytest.mark.parametrize("lsa_name_empty,should_force_hide_separator", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("timestamp,domain,offset,user,lsa_name", [
    (True, True, True, True, True),
    (True, True, True, True, False),
    (True, True, True, False, True),
    (True, True, True, False, False),
    (True, True, False, True, True),
    (True, True, False, True, False),
    (True, True, False, False, True),
    (True, True, False, False, False),
    (True, False, True, True, True),
    (True, False, True, True, False),
    (True, False, True, False, True),
    (True, False, True, False, False),
    (True, False, False, True, True),
    (True, False, False, True, False),
    (True, False, False, False, True),
    (True, False, False, False, False),
    (False, True, True, True, True),
    (False, True, True, True, False),
    (False, True, True, False, True),
    (False, True, True, False, False),
    (False, True, False, True, True),
    (False, True, False, True, False),
    (False, True, False, False, True),
    (False, True, False, False, False),
    (False, False, True, True, True),
    (False, False, True, True, False),
    (False, False, True, False, True),
    (False, False, True, False, False),
    (False, False, False, True, True),
    (False, False, False, True, False),
    (False, False, False, False, True),
    (False, False, False, False, False),
])
@mock.patch("accwidgets.timing_bar.TimingBarModel.has_error", new_callable=mock.PropertyMock)
def test_timing_bar_label_visibility(has_error, qtbot: QtBot, timestamp, offset, user, lsa_name, domain, lsa_name_empty,
                                     should_force_hide_separator):
    config: TimingBar.Labels = TimingBar.Labels(0)
    if timestamp:
        config |= TimingBar.Labels.DATETIME
    if offset:
        config |= TimingBar.Labels.CYCLE_START
    if user:
        config |= TimingBar.Labels.USER
    if lsa_name:
        config |= TimingBar.Labels.LSA_CYCLE_NAME
    if domain:
        config |= TimingBar.Labels.TIMING_DOMAIN

    has_error.return_value = False
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    if not lsa_name_empty:
        view.model._last_info = TimingUpdate(timestamp=datetime.now(),
                                             lsa_name="lsa1",
                                             user="user1",
                                             offset=0)
        view.model.timingUpdateReceived.emit(False)
    with qtbot.wait_exposed(view):
        view.show()
    assert view._lbl_datetime.isVisible()
    assert view._lbl_beam_offset.isVisible()
    assert view._lbl_user.isVisible()
    assert view._lbl_lsa_name.isVisible()
    assert view._sep_lsa.isVisible() != should_force_hide_separator
    assert view._lbl_domain.isVisible()
    view.labels = config
    assert view.labels == config
    assert view._lbl_datetime.isVisible() == timestamp
    assert view._lbl_beam_offset.isVisible() == offset
    assert view._lbl_user.isVisible() == user
    assert view._lbl_lsa_name.isVisible() == lsa_name
    assert view._sep_lsa.isVisible() == (lsa_name and not should_force_hide_separator)
    assert view._lbl_domain.isVisible() == domain
    has_error.return_value = True
    view.model.timingErrorReceived.emit("Test error")
    assert not view._lbl_datetime.isVisible()
    assert not view._lbl_beam_offset.isVisible()
    assert not view._lbl_user.isVisible()
    assert not view._lbl_lsa_name.isVisible()
    assert not view._sep_lsa.isVisible()
    assert not view._lbl_domain.isVisible()
    has_error.return_value = False
    view.model.timingUpdateReceived.emit(False)
    assert view._lbl_datetime.isVisible() == timestamp
    assert view._lbl_beam_offset.isVisible() == offset
    assert view._lbl_user.isVisible() == user
    assert view._lbl_lsa_name.isVisible() == lsa_name
    assert view._sep_lsa.isVisible() == (lsa_name and not should_force_hide_separator)
    assert view._lbl_domain.isVisible() == domain


@pytest.mark.parametrize("initial_alternate,use_heartbeat,updates_count,should_be_alternate", [
    (False, True, 0, False),
    (True, True, 0, True),
    (False, False, 0, False),
    (True, False, 0, False),
    (False, True, 1, True),
    (True, True, 1, False),
    (False, False, 1, False),
    (True, False, 1, False),
    (False, True, 2, False),
    (True, True, 2, True),
    (False, False, 2, False),
    (True, False, 2, False),
    (False, True, 5, True),
    (True, True, 5, False),
    (False, False, 5, False),
    (True, False, 5, False),
])
def test_timing_bar_indicate_heartbeat(qtbot, initial_alternate, use_heartbeat, updates_count, should_be_alternate):
    view = TimingBar()
    qtbot.add_widget(view)
    view._tick_bkg = view._canvas._use_alternate_color = initial_alternate
    view.indicateHeartbeat = use_heartbeat
    assert view.indicateHeartbeat == use_heartbeat
    for _ in range(updates_count):
        view.model.timingUpdateReceived.emit(True)
    assert view._canvas._use_alternate_color == should_be_alternate


@pytest.mark.parametrize("initial_user,initial_bp,expected_initial_color,expected_new_color", [
    ("normal-user-1", 0, Qt.red, Qt.yellow),
    ("normal-user-1", 1, Qt.yellow, Qt.yellow),
    ("normal-user-2", 0, Qt.yellow, Qt.red),
    ("normal-user-2", 2, Qt.red, Qt.red),
    (None, 0, Qt.red, Qt.red),
    (None, 1, Qt.red, Qt.red),
    (None, 2, Qt.red, Qt.red),
])
def test_timing_bar_highlighted_user_affects_advance(qtbot, supercycle_obj, initial_user, initial_bp,
                                                     expected_initial_color, expected_new_color):
    view = TimingBar()
    qtbot.add_widget(view)
    palette = view.color_palette
    palette.normal_cycle = Qt.yellow
    palette.highlighted_cycle = Qt.red
    view.color_palette = palette
    view.model._bcd = supercycle_obj

    def update_last_info(new_bp: int):
        _, new_cycle = supercycle_obj.cycle_at_basic_period(new_bp)
        view.model._last_info = TimingUpdate(timestamp=isoparse("2018-04-02 15:33:21Z"),
                                             offset=new_bp,
                                             lsa_name=new_cycle.lsa_name,
                                             user=new_cycle.user)

    update_last_info(initial_bp)
    view.highlightedUser = initial_user
    view.model.timingUpdateReceived.emit(False)
    expected_color = QColor(expected_initial_color).name()
    assert view._lbl_datetime.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()
    assert view._lbl_domain.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()
    assert expected_color == view._lbl_lsa_name.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_user.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_beam_offset.palette().color(QPalette.WindowText).name()
    assert expected_color == view._sep_lsa.palette().color(QPalette.WindowText).name()
    update_last_info(initial_bp + 1)
    view.model.timingUpdateReceived.emit(True)
    expected_color = QColor(expected_new_color).name()
    assert expected_color == view._lbl_lsa_name.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_user.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_beam_offset.palette().color(QPalette.WindowText).name()
    assert expected_color == view._sep_lsa.palette().color(QPalette.WindowText).name()
    assert view._lbl_datetime.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()
    assert view._lbl_domain.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()


@pytest.mark.parametrize("initial_user,new_user,initial_bp,expected_initial_color,expected_new_color", [
    ("normal-user-1", "normal-user-1", 0, Qt.red, Qt.red),
    ("normal-user-1", "normal-user-1", 1, Qt.yellow, Qt.yellow),
    ("normal-user-1", "normal-user-2", 0, Qt.red, Qt.yellow),
    ("normal-user-1", "normal-user-2", 1, Qt.yellow, Qt.red),
    ("normal-user-2", "normal-user-2", 0, Qt.yellow, Qt.yellow),
    ("normal-user-2", "normal-user-2", 2, Qt.red, Qt.red),
    ("normal-user-2", "normal-user-1", 0, Qt.yellow, Qt.red),
    ("normal-user-2", "normal-user-1", 2, Qt.red, Qt.yellow),
    (None, "normal-user-1", 0, Qt.red, Qt.red),
    (None, "normal-user-1", 2, Qt.red, Qt.yellow),
    (None, "normal-user-2", 0, Qt.red, Qt.yellow),
    (None, "normal-user-2", 2, Qt.red, Qt.red),
    ("normal-user-1", None, 0, Qt.red, Qt.red),
    ("normal-user-1", None, 2, Qt.yellow, Qt.red),
    ("normal-user-2", None, 0, Qt.yellow, Qt.red),
    ("normal-user-2", None, 2, Qt.red, Qt.red),
    (None, None, 0, Qt.red, Qt.red),
    (None, None, 2, Qt.red, Qt.red),
    ("non_existing", "normal-user-1", 0, Qt.yellow, Qt.red),
    ("non_existing", "normal-user-1", 2, Qt.yellow, Qt.yellow),
    ("non_existing", "normal-user-2", 0, Qt.yellow, Qt.yellow),
    ("non_existing", "normal-user-2", 2, Qt.yellow, Qt.red),
    ("normal-user-1", "non_existing", 0, Qt.red, Qt.yellow),
    ("normal-user-1", "non_existing", 2, Qt.yellow, Qt.yellow),
    ("normal-user-2", "non_existing", 0, Qt.yellow, Qt.yellow),
    ("normal-user-2", "non_existing", 2, Qt.red, Qt.yellow),
    ("non_existing", "non_existing", 0, Qt.yellow, Qt.yellow),
    ("non_existing", "non_existing", 2, Qt.yellow, Qt.yellow),
])
def test_timing_bar_highlighted_user_resets_current_color(qtbot, supercycle_obj, initial_user, initial_bp, new_user,
                                                          expected_initial_color, expected_new_color):
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    with qtbot.wait_exposed(view):
        view.show()
    palette = view.color_palette
    palette.normal_cycle = Qt.yellow
    palette.highlighted_cycle = Qt.red
    view.color_palette = palette
    view.model._bcd = supercycle_obj
    _, curr_cycle = supercycle_obj.cycle_at_basic_period(initial_bp)
    view.model._last_info = TimingUpdate(timestamp=isoparse("2018-04-02 15:33:21Z"),
                                         offset=initial_bp,
                                         lsa_name=curr_cycle.lsa_name,
                                         user=curr_cycle.user)
    view.highlightedUser = initial_user
    expected_color = QColor(expected_initial_color).name()
    assert view._lbl_datetime.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()
    assert view._lbl_domain.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()
    assert expected_color == view._lbl_lsa_name.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_user.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_beam_offset.palette().color(QPalette.WindowText).name()
    assert expected_color == view._sep_lsa.palette().color(QPalette.WindowText).name()
    view.highlightedUser = new_user
    expected_color = QColor(expected_new_color).name()
    assert expected_color == view._lbl_lsa_name.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_user.palette().color(QPalette.WindowText).name()
    assert expected_color == view._lbl_beam_offset.palette().color(QPalette.WindowText).name()
    assert expected_color == view._sep_lsa.palette().color(QPalette.WindowText).name()
    assert view._lbl_datetime.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()
    assert view._lbl_domain.palette().color(QPalette.WindowText).name() == QColor(view.color_palette.text).name()


@pytest.mark.parametrize("init_val,new_val,expect_calls_show,expect_calls_hide", [
    (True, False, False, True),
    (False, True, True, False),
    (False, False, False, False),
    (True, True, False, False),
])
@mock.patch("accwidgets.timing_bar.TimingBar.showSuperCycle")
@mock.patch("accwidgets.timing_bar.TimingBar.hideSuperCycle")
def test_timing_bar_set_render_supercycle(hideSuperCycle, showSuperCycle, qtbot, init_val, new_val, expect_calls_hide,
                                          expect_calls_show):
    view = TimingBar()
    qtbot.add_widget(view)

    def side_effect(val: bool):
        view._canvas.show_supercycle = val

    hideSuperCycle.side_effect = lambda *_: side_effect(False)
    showSuperCycle.side_effect = lambda *_: side_effect(True)
    view.renderSuperCycle = init_val
    assert view.renderSuperCycle == init_val
    hideSuperCycle.reset_mock()
    showSuperCycle.reset_mock()
    view.renderSuperCycle = new_val
    assert view.renderSuperCycle == new_val
    if expect_calls_show:
        showSuperCycle.assert_called_once()
    else:
        showSuperCycle.assert_not_called()
    if expect_calls_hide:
        hideSuperCycle.assert_called_once()
    else:
        hideSuperCycle.assert_not_called()


@pytest.mark.parametrize("initial_us_flag,new_us_flag,initial_tz_flag,new_tz_flag,expected_initial_label,expected_new_label", [
    (False, False, False, False, "2018-04-02  15:33:21", "2018-04-02  15:33:21"),
    (False, True, False, False, "2018-04-02  15:33:21", "2018-04-02  15:33:21.543495"),
    (True, False, False, False, "2018-04-02  15:33:21.543495", "2018-04-02  15:33:21"),
    (True, True, False, False, "2018-04-02  15:33:21.543495", "2018-04-02  15:33:21.543495"),
    (False, False, False, True, "2018-04-02  15:33:21", "2018-04-02  15:33:21 UTC"),
    (False, True, False, True, "2018-04-02  15:33:21", "2018-04-02  15:33:21.543495 UTC"),
    (True, False, False, True, "2018-04-02  15:33:21.543495", "2018-04-02  15:33:21 UTC"),
    (True, True, False, True, "2018-04-02  15:33:21.543495", "2018-04-02  15:33:21.543495 UTC"),
    (False, False, True, False, "2018-04-02  15:33:21 UTC", "2018-04-02  15:33:21"),
    (False, True, True, False, "2018-04-02  15:33:21 UTC", "2018-04-02  15:33:21.543495"),
    (True, False, True, False, "2018-04-02  15:33:21.543495 UTC", "2018-04-02  15:33:21"),
    (True, True, True, False, "2018-04-02  15:33:21.543495 UTC", "2018-04-02  15:33:21.543495"),
    (False, False, True, True, "2018-04-02  15:33:21 UTC", "2018-04-02  15:33:21 UTC"),
    (False, True, True, True, "2018-04-02  15:33:21 UTC", "2018-04-02  15:33:21.543495 UTC"),
    (True, False, True, True, "2018-04-02  15:33:21.543495 UTC", "2018-04-02  15:33:21 UTC"),
    (True, True, True, True, "2018-04-02  15:33:21.543495 UTC", "2018-04-02  15:33:21.543495 UTC"),
])
def test_timing_bar_set_show_us_and_tz_affect_current_timestamp(qtbot, initial_us_flag, new_us_flag, initial_tz_flag, new_tz_flag,
                                                                expected_initial_label, expected_new_label):
    view = TimingBar()
    qtbot.add_widget(view)
    view.showMicroSeconds = initial_us_flag
    view.showTimeZone = initial_tz_flag
    view.model._last_info = TimingUpdate(timestamp=isoparse("2018-04-02 15:33:21.543495Z"),
                                         offset=0,
                                         lsa_name="",
                                         user="")
    view.model.timingUpdateReceived.emit(False)
    assert view._lbl_datetime.text() == expected_initial_label
    view.showMicroSeconds = new_us_flag
    view.showTimeZone = new_tz_flag
    assert view._lbl_datetime.text() == expected_new_label


@pytest.mark.parametrize("indicate_advancement", [True, False])
@pytest.mark.parametrize("us_val,tz_val,timing_updates,expected_labels", [
    (False, False, ["2018-04-02 15:33:21.543495Z", "2018-04-02 15:33:22.543495Z"], ["2018-04-02  15:33:21", "2018-04-02  15:33:22"]),
    (True, False, ["2018-04-02 15:33:21.543495Z", "2018-04-02 15:33:22.543495Z"], ["2018-04-02  15:33:21.543495", "2018-04-02  15:33:22.543495"]),
    (False, True, ["2018-04-02 15:33:21.543495Z", "2018-04-02 15:33:22.543495Z"], ["2018-04-02  15:33:21 UTC", "2018-04-02  15:33:22 UTC"]),
    (True, True, ["2018-04-02 15:33:21.543495Z", "2018-04-02 15:33:22.543495Z"], ["2018-04-02  15:33:21.543495 UTC", "2018-04-02  15:33:22.543495 UTC"]),
])
def test_timing_bar_set_show_us_and_tz_affect_new_timestamps(qtbot, us_val, tz_val, timing_updates, indicate_advancement, expected_labels):
    view = TimingBar()
    qtbot.add_widget(view)
    view.showMicroSeconds = us_val
    view.showTimeZone = tz_val
    for timestamp, expected_text in zip(timing_updates, expected_labels):
        view.model._last_info = TimingUpdate(timestamp=isoparse(timestamp),
                                             offset=0,
                                             lsa_name="",
                                             user="")
        view.model.timingUpdateReceived.emit(indicate_advancement)
        assert view._lbl_datetime.text() == expected_text


def test_timing_bar_color_palette_is_copied(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    orig_color = view.color_palette.text
    new_color = QColor(254, 232, 111)
    assert new_color.name() != QColor(orig_color).name()

    # Check cannot change directly
    view.color_palette.text = new_color
    assert QColor(view.color_palette.text).name() != new_color.name()
    assert QColor(view.color_palette.text).name() == QColor(orig_color).name()

    # Check can check by copying
    palette = view.color_palette
    palette.text = new_color
    view.color_palette = palette
    assert QColor(view.color_palette.text).name() == new_color.name()
    assert QColor(view.color_palette.text).name() != QColor(orig_color).name()


def test_timing_bar_updates_colors_on_color_palette_setter(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    color_palette = view.color_palette
    expected_text_color = QColor(color_palette.text).name()
    expected_highlighted_text_color = QColor(color_palette.highlighted_cycle).name()
    view.model._last_info = TimingUpdate(timestamp=datetime.now(),
                                         offset=0,
                                         lsa_name="test",
                                         user="test2")
    view.model.timingUpdateReceived.emit(False)
    assert view._lbl_datetime.palette().color(QPalette.Text).name() == expected_text_color
    assert view._lbl_domain.palette().color(QPalette.Text).name() == expected_text_color
    assert view._lbl_lsa_name.palette().color(QPalette.Text).name() == expected_highlighted_text_color
    assert view._lbl_beam_offset.palette().color(QPalette.Text).name() == expected_highlighted_text_color
    assert view._lbl_user.palette().color(QPalette.Text).name() == expected_highlighted_text_color
    assert view._sep_lsa.palette().color(QPalette.Text).name() == expected_highlighted_text_color
    with mock.patch.object(view._canvas, "update_gradients") as update_gradients:
        color_palette.bg_bottom = QColor(254, 232, 111)
        color_palette.text = QColor(121, 111, 0)
        color_palette.highlighted_cycle = QColor(0, 0, 255)
        view.color_palette = color_palette
        update_gradients.assert_called_once()
        expected_text_color = QColor(color_palette.text).name()
        expected_highlighted_text_color = QColor(color_palette.highlighted_cycle).name()
        assert view._lbl_datetime.palette().color(QPalette.Text).name() == expected_text_color
        assert view._lbl_domain.palette().color(QPalette.Text).name() == expected_text_color
        assert view._lbl_lsa_name.palette().color(QPalette.Text).name() == expected_highlighted_text_color
        assert view._lbl_beam_offset.palette().color(QPalette.Text).name() == expected_highlighted_text_color
        assert view._lbl_user.palette().color(QPalette.Text).name() == expected_highlighted_text_color
        assert view._sep_lsa.palette().color(QPalette.Text).name() == expected_highlighted_text_color


@pytest.mark.parametrize("is_designer_val,initial_domain,expected_initial_domain", [
    (False, TimingBarDomain.LHC, TimingBarDomain.LHC),
    (False, TimingBarDomain.SPS, TimingBarDomain.SPS),
    (False, TimingBarDomain.CPS, TimingBarDomain.CPS),
    (False, TimingBarDomain.PSB, TimingBarDomain.PSB),
    (False, TimingBarDomain.LNA, TimingBarDomain.LNA),
    (False, TimingBarDomain.LEI, TimingBarDomain.LEI),
    (False, TimingBarDomain.ADE, TimingBarDomain.ADE),
    (True, TimingBarDomain.LHC, 0),
    (True, TimingBarDomain.SPS, 1),
    (True, TimingBarDomain.CPS, 2),
    (True, TimingBarDomain.PSB, 3),
    (True, TimingBarDomain.LNA, 4),
    (True, TimingBarDomain.LEI, 5),
    (True, TimingBarDomain.ADE, 6),
])
@mock.patch("accwidgets.timing_bar._widget.is_designer")
def test_timing_bar_get_domain_from_initial(is_designer, qtbot, is_designer_val, initial_domain, expected_initial_domain):
    is_designer.return_value = is_designer_val
    model = TimingBarModel(domain=initial_domain)
    view = TimingBar(model=model)
    qtbot.add_widget(view)
    assert view.domain == expected_initial_domain
    assert type(view.domain) == type(expected_initial_domain)


@pytest.mark.parametrize("is_designer_val,new_domain,expected_new_domain", [
    (False, TimingBarDomain.LHC, TimingBarDomain.LHC),
    (False, TimingBarDomain.SPS, TimingBarDomain.SPS),
    (False, TimingBarDomain.CPS, TimingBarDomain.CPS),
    (False, TimingBarDomain.PSB, TimingBarDomain.PSB),
    (False, TimingBarDomain.LNA, TimingBarDomain.LNA),
    (False, TimingBarDomain.LEI, TimingBarDomain.LEI),
    (False, TimingBarDomain.ADE, TimingBarDomain.ADE),
    (True, 0, 0),
    (True, 1, 1),
    (True, 2, 2),
    (True, 3, 3),
    (True, 4, 4),
    (True, 5, 5),
    (True, 6, 6),
])
@mock.patch("accwidgets.timing_bar._widget.is_designer")
def test_timing_bar_get_domain_from_acquired(is_designer, qtbot, is_designer_val, new_domain, expected_new_domain):
    is_designer.return_value = is_designer_val
    view = TimingBar()
    qtbot.add_widget(view)
    view.domain = new_domain
    assert view.domain == expected_new_domain
    assert type(view.domain) == type(expected_new_domain)


@pytest.mark.parametrize("is_designer_val,expected_default_domain", [
    (False, TimingBarDomain.PSB),
    (True, 3),
])
@mock.patch("accwidgets.timing_bar._widget.is_designer")
def test_timing_bar_get_default_domain(is_designer, qtbot, is_designer_val, expected_default_domain):
    is_designer.return_value = is_designer_val
    view = TimingBar()
    qtbot.add_widget(view)
    assert view.domain == expected_default_domain
    assert type(view.domain) == type(expected_default_domain)


@pytest.mark.parametrize("is_designer_val,new_domain,expected_model_domain", [
    (False, TimingBarDomain.LHC, TimingBarDomain.LHC),
    (False, TimingBarDomain.SPS, TimingBarDomain.SPS),
    (False, TimingBarDomain.CPS, TimingBarDomain.CPS),
    (False, TimingBarDomain.PSB, TimingBarDomain.PSB),
    (False, TimingBarDomain.LNA, TimingBarDomain.LNA),
    (False, TimingBarDomain.LEI, TimingBarDomain.LEI),
    (False, TimingBarDomain.ADE, TimingBarDomain.ADE),
    (True, 0, TimingBarDomain.LHC),
    (True, 1, TimingBarDomain.SPS),
    (True, 2, TimingBarDomain.CPS),
    (True, 3, TimingBarDomain.PSB),
    (True, 4, TimingBarDomain.LNA),
    (True, 5, TimingBarDomain.LEI),
    (True, 6, TimingBarDomain.ADE),
])
@mock.patch("accwidgets.timing_bar._widget.is_designer")
def test_timing_bar_set_domain(is_designer, qtbot, is_designer_val, new_domain, expected_model_domain):
    is_designer.return_value = is_designer_val
    view = TimingBar()
    qtbot.add_widget(view)
    view.domain = new_domain
    assert view.model.domain == expected_model_domain
    assert type(view.model.domain) == type(expected_model_domain)


def test_timing_bar_timing_mark_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.timingMarkColor).name() != new_color.name()
    assert QColor(view.timingMarkColor).name() == QColor(view.color_palette.timing_mark).name()
    view.timingMarkColor = new_color
    assert QColor(view.timingMarkColor).name() == new_color.name()
    assert QColor(view.color_palette.timing_mark).name() == new_color.name()


def test_timing_bar_timing_mark_text_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.timingMarkTextColor).name() != new_color.name()
    assert QColor(view.timingMarkTextColor).name() == QColor(view.color_palette.timing_mark_text).name()
    view.timingMarkTextColor = new_color
    assert QColor(view.timingMarkTextColor).name() == new_color.name()
    assert QColor(view.color_palette.timing_mark_text).name() == new_color.name()


def test_timing_bar_normal_cycle_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.normalCycleColor).name() != new_color.name()
    assert QColor(view.normalCycleColor).name() == QColor(view.color_palette.normal_cycle).name()
    view.normalCycleColor = new_color
    assert QColor(view.normalCycleColor).name() == new_color.name()
    assert QColor(view.color_palette.normal_cycle).name() == new_color.name()


def test_timing_bar_highlighted_cycle_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.highlightedCycleColor).name() != new_color.name()
    assert QColor(view.highlightedCycleColor).name() == QColor(view.color_palette.highlighted_cycle).name()
    view.highlightedCycleColor = new_color
    assert QColor(view.highlightedCycleColor).name() == new_color.name()
    assert QColor(view.color_palette.highlighted_cycle).name() == new_color.name()


def test_timing_bar_bg_pattern_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.backgroundPatternColor).name() != new_color.name()
    assert QColor(view.backgroundPatternColor).name() == QColor(view.color_palette.bg_pattern).name()
    view.backgroundPatternColor = new_color
    assert QColor(view.backgroundPatternColor).name() == new_color.name()
    assert QColor(view.color_palette.bg_pattern).name() == new_color.name()


def test_timing_bar_bg_pattern_alt_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.backgroundPatternAltColor).name() != new_color.name()
    assert QColor(view.backgroundPatternAltColor).name() == QColor(view.color_palette.bg_pattern_alt).name()
    view.backgroundPatternAltColor = new_color
    assert QColor(view.backgroundPatternAltColor).name() == new_color.name()
    assert QColor(view.color_palette.bg_pattern_alt).name() == new_color.name()


def test_timing_bar_bg_top_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.backgroundTopColor).name() != new_color.name()
    assert QColor(view.backgroundTopColor).name() == QColor(view.color_palette.bg_top).name()
    view.backgroundTopColor = new_color
    assert QColor(view.backgroundTopColor).name() == new_color.name()
    assert QColor(view.color_palette.bg_top).name() == new_color.name()


def test_timing_bar_bg_bottom_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.backgroundBottomColor).name() != new_color.name()
    assert QColor(view.backgroundBottomColor).name() == QColor(view.color_palette.bg_bottom).name()
    view.backgroundBottomColor = new_color
    assert QColor(view.backgroundBottomColor).name() == new_color.name()
    assert QColor(view.color_palette.bg_bottom).name() == new_color.name()


def test_timing_bar_bg_top_alt_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.backgroundTopAltColor).name() != new_color.name()
    assert QColor(view.backgroundTopAltColor).name() == QColor(view.color_palette.bg_top_alt).name()
    view.backgroundTopAltColor = new_color
    assert QColor(view.backgroundTopAltColor).name() == new_color.name()
    assert QColor(view.color_palette.bg_top_alt).name() == new_color.name()


def test_timing_bar_bg_bottom_alt_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.backgroundBottomAltColor).name() != new_color.name()
    assert QColor(view.backgroundBottomAltColor).name() == QColor(view.color_palette.bg_bottom_alt).name()
    view.backgroundBottomAltColor = new_color
    assert QColor(view.backgroundBottomAltColor).name() == new_color.name()
    assert QColor(view.color_palette.bg_bottom_alt).name() == new_color.name()


def test_timing_bar_text_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.textColor).name() != new_color.name()
    assert QColor(view.textColor).name() == QColor(view.color_palette.text).name()
    view.textColor = new_color
    assert QColor(view.textColor).name() == new_color.name()
    assert QColor(view.color_palette.text).name() == new_color.name()


def test_timing_bar_error_text_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.errorTextColor).name() != new_color.name()
    assert QColor(view.errorTextColor).name() == QColor(view.color_palette.error_text).name()
    view.errorTextColor = new_color
    assert QColor(view.errorTextColor).name() == new_color.name()
    assert QColor(view.color_palette.error_text).name() == new_color.name()


def test_timing_bar_frame_color(qtbot):
    view = TimingBar()
    qtbot.add_widget(view)
    new_color = QColor(234, 111, 203)
    assert QColor(view.frameColor).name() != new_color.name()
    assert QColor(view.frameColor).name() == QColor(view.color_palette.frame).name()
    view.frameColor = new_color
    assert QColor(view.frameColor).name() == new_color.name()
    assert QColor(view.color_palette.frame).name() == new_color.name()


def test_timing_bar_qss(qtbot: QtBot):
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    new_text = QColor(1, 2, 3)
    new_error_text = QColor(1, 2, 3)
    new_highlighted_cycle = QColor(1, 2, 3)
    new_normal_cycle = QColor(1, 2, 3)
    new_timing_mark = QColor(1, 2, 3)
    new_timing_mark_text = QColor(1, 2, 3)
    new_frame = QColor(1, 2, 3)
    new_bg_top = QColor(1, 2, 3)
    new_bg_bottom = QColor(1, 2, 3)
    new_bg_pattern = QColor(1, 2, 3)
    new_bg_top_alt = QColor(1, 2, 3)
    new_bg_bottom_alt = QColor(1, 2, 3)
    new_bg_pattern_alt = QColor(1, 2, 3)
    with qtbot.wait_exposed(view):
        view.show()
    assert QColor(view.color_palette.text).name() != new_text.name()
    assert QColor(view.color_palette.error_text).name() != new_error_text.name()
    assert QColor(view.color_palette.highlighted_cycle).name() != new_highlighted_cycle.name()
    assert QColor(view.color_palette.normal_cycle).name() != new_normal_cycle.name()
    assert QColor(view.color_palette.timing_mark).name() != new_timing_mark.name()
    assert QColor(view.color_palette.timing_mark_text).name() != new_timing_mark_text.name()
    assert QColor(view.color_palette.frame).name() != new_frame.name()
    assert QColor(view.color_palette.bg_top).name() != new_bg_top.name()
    assert QColor(view.color_palette.bg_bottom).name() != new_bg_bottom.name()
    assert QColor(view.color_palette.bg_pattern).name() != new_bg_pattern.name()
    assert QColor(view.color_palette.bg_top_alt).name() != new_bg_top_alt.name()
    assert QColor(view.color_palette.bg_bottom_alt).name() != new_bg_bottom_alt.name()
    assert QColor(view.color_palette.bg_pattern_alt).name() != new_bg_pattern_alt.name()

    view.setStyleSheet(f"TimingBar{{"
                       f"  qproperty-textColor: {new_text.name()};"
                       f"  qproperty-errorTextColor: {new_error_text.name()};"
                       f"  qproperty-highlightedCycleColor: {new_highlighted_cycle.name()};"
                       f"  qproperty-normalCycleColor: {new_normal_cycle.name()};"
                       f"  qproperty-timingMarkColor: {new_timing_mark.name()};"
                       f"  qproperty-timingMarkTextColor: {new_timing_mark_text.name()};"
                       f"  qproperty-frameColor: {new_frame.name()};"
                       f"  qproperty-backgroundTopColor: {new_bg_top.name()};"
                       f"  qproperty-backgroundBottomColor: {new_bg_bottom.name()};"
                       f"  qproperty-backgroundPatternColor: {new_bg_pattern.name()};"
                       f"  qproperty-backgroundTopAltColor: {new_bg_top_alt.name()};"
                       f"  qproperty-backgroundBottomAltColor: {new_bg_bottom_alt.name()};"
                       f"  qproperty-backgroundPatternAltColor: {new_bg_pattern_alt.name()};"
                       f"}}")
    assert QColor(view.color_palette.error_text).name() == new_error_text.name()
    assert QColor(view.color_palette.error_text).name() == new_error_text.name()
    assert QColor(view.color_palette.highlighted_cycle).name() == new_highlighted_cycle.name()
    assert QColor(view.color_palette.normal_cycle).name() == new_normal_cycle.name()
    assert QColor(view.color_palette.timing_mark).name() == new_timing_mark.name()
    assert QColor(view.color_palette.timing_mark_text).name() == new_timing_mark_text.name()
    assert QColor(view.color_palette.frame).name() == new_frame.name()
    assert QColor(view.color_palette.bg_top).name() == new_bg_top.name()
    assert QColor(view.color_palette.bg_bottom).name() == new_bg_bottom.name()
    assert QColor(view.color_palette.bg_pattern).name() == new_bg_pattern.name()
    assert QColor(view.color_palette.bg_top_alt).name() == new_bg_top_alt.name()
    assert QColor(view.color_palette.bg_bottom_alt).name() == new_bg_bottom_alt.name()
    assert QColor(view.color_palette.bg_pattern_alt).name() == new_bg_pattern_alt.name()


@pytest.mark.parametrize("initial_show,expect_calls_method", [
    (True, False),
    (False, True),
])
def test_timing_bar_show_supercycle_noop_if_already_showing(qtbot, initial_show, expect_calls_method):
    view = TimingBar()
    qtbot.add_widget(view)
    view.renderSuperCycle = initial_show
    with mock.patch.object(view._canvas, "update") as update_canvas:
        with mock.patch.object(view, "_update_widget_height") as update_height:
            view.showSuperCycle()
            if expect_calls_method:
                update_height.assert_called_once()
                update_canvas.assert_called_once()
            else:
                update_height.assert_not_called()
                update_canvas.assert_not_called()


@pytest.mark.parametrize("initial_show,expected_initial_height,expected_new_height", [
    (True, 49, 49),
    (False, 30, 49),
])
def test_timing_bar_show_supercycle_changes_height(qtbot, initial_show, expected_initial_height, expected_new_height):
    view = TimingBar()
    qtbot.add_widget(view)
    view.renderSuperCycle = initial_show
    assert view.height() == expected_initial_height
    assert view.minimumHeight() == expected_initial_height
    assert view.maximumHeight() == expected_initial_height
    view.showSuperCycle()
    assert view.height() == expected_new_height
    assert view.minimumHeight() == expected_new_height
    assert view.maximumHeight() == expected_new_height


@pytest.mark.skip("Flaky test. wait_exposed sometimes causes segfault (potentially in couple with repaint())")
@pytest.mark.parametrize("has_error,should_render_supercycle", [
    (True, False),
    (False, True),
])
@mock.patch("accwidgets.timing_bar._widget.TimingBarCanvas._draw_supercycle")
@mock.patch("accwidgets.timing_bar.TimingBarModel.has_error", new_callable=mock.PropertyMock)
def test_timing_bar_show_supercycle_renders_subwidget(has_error_mock, draw_supercycle, qtbot: QtBot, has_error, should_render_supercycle):
    has_error_mock.return_value = has_error
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    view.renderSuperCycle = False
    with qtbot.wait_exposed(view):
        view.show()
    draw_supercycle.assert_not_called()
    view.showSuperCycle()
    view.repaint()
    if should_render_supercycle:
        draw_supercycle.assert_called_once()
    else:
        draw_supercycle.assert_not_called()


@pytest.mark.parametrize("initial_show,expect_calls_method", [
    (True, True),
    (False, False),
])
def test_timing_bar_hide_supercycle_noop_if_already_hidden(qtbot, initial_show, expect_calls_method):
    view = TimingBar()
    qtbot.add_widget(view)
    view.renderSuperCycle = initial_show
    with mock.patch.object(view._canvas, "update") as update_canvas:
        with mock.patch.object(view, "_update_widget_height") as update_height:
            view.hideSuperCycle()
            if expect_calls_method:
                update_height.assert_called_once()
                update_canvas.assert_called_once()
            else:
                update_height.assert_not_called()
                update_canvas.assert_not_called()


@pytest.mark.parametrize("initial_show,expected_initial_height,expected_new_height", [
    (False, 30, 30),
    (True, 49, 30),
])
def test_timing_bar_hide_supercycle_changes_height(qtbot, initial_show, expected_initial_height, expected_new_height):
    view = TimingBar()
    qtbot.add_widget(view)
    view.renderSuperCycle = initial_show
    assert view.height() == expected_initial_height
    assert view.minimumHeight() == expected_initial_height
    assert view.maximumHeight() == expected_initial_height
    view.hideSuperCycle()
    assert view.height() == expected_new_height
    assert view.minimumHeight() == expected_new_height
    assert view.maximumHeight() == expected_new_height


@pytest.mark.skip("Flaky test. wait_exposed sometimes causes segfault (potentially in couple with repaint())")
@pytest.mark.parametrize("has_error,should_render_initial_supercycle", [
    (True, False),
    (False, True),
])
@mock.patch("accwidgets.timing_bar._widget.TimingBarCanvas._draw_supercycle")
@mock.patch("accwidgets.timing_bar.TimingBarModel.has_error", new_callable=mock.PropertyMock)
def test_timing_bar_hide_supercycle_renders_subwidget(has_error_mock, draw_supercycle, qtbot: QtBot, has_error,
                                                      should_render_initial_supercycle):
    has_error_mock.return_value = has_error
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    view.renderSuperCycle = True
    with qtbot.wait_exposed(view):
        view.show()
    if should_render_initial_supercycle:
        draw_supercycle.assert_called_once()
    else:
        draw_supercycle.assert_not_called()
    draw_supercycle.reset_mock()
    view.hideSuperCycle()
    view.repaint()
    draw_supercycle.assert_not_called()


@pytest.mark.parametrize("initial_renders,should_call_hide,should_call_show", [
    (True, True, False),
    (False, False, True),
])
def test_timing_bar_toggle_supercycle(qtbot: QtBot, initial_renders, should_call_hide, should_call_show):
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    view.renderSuperCycle = initial_renders
    with mock.patch.object(view, "showSuperCycle") as showSuperCycle:
        with mock.patch.object(view, "hideSuperCycle") as hideSuperCycle:
            view.toggleSuperCycle()
            if should_call_show:
                showSuperCycle.assert_called_once()
            else:
                showSuperCycle.assert_not_called()
            if should_call_hide:
                hideSuperCycle.assert_called_once()
            else:
                hideSuperCycle.assert_not_called()


def test_timing_bar_activates_model_on_first_show_only_once(qtbot: QtBot):
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    assert view.model.activated is False
    with qtbot.wait_exposed(view):
        view.show()
    assert view.model.activated is True
    with mock.patch.object(view.model, "activate") as activate:
        view.hide()
        with qtbot.wait_exposed(view):
            view.show()
        activate.assert_not_called()


@mock.patch("accwidgets.timing_bar.TimingBarModel.activated", new_callable=mock.PropertyMock, return_value=True)
def test_timing_bar_noop_activated_model_on_first_show(_, qtbot: QtBot):
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    with mock.patch.object(view.model, "activate") as activate:
        with qtbot.wait_exposed(view):
            view.show()
        activate.assert_not_called()


@pytest.mark.parametrize("timing_update,show_us,show_tz,tz,expected_datetime,expected_lsa_name,expected_user,expected_offset,expect_visible_separator", [
    (None, True, False, None, "", "", "", "", False),
    (None, False, False, None, "", "", "", "", False),
    (
        TimingUpdate(user="user1",
                     lsa_name="lsa1",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, False, None, "2018-04-02  15:33:21.294238", "lsa1", "user1", "5", True,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="lsa2",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, False, None, "2018-04-02  15:33:21", "lsa2", "user2", "6", True,
    ), (
        TimingUpdate(user="user1",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, False, None, "2018-04-02  15:33:21.294238", "", "user1", "5", False,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, False, None, "2018-04-02  15:33:21", "", "user2", "6", False,
    ),
    (None, True, False, UTC, "", "", "", "", False),
    (None, False, False, UTC, "", "", "", "", False),
    (
        TimingUpdate(user="user1",
                     lsa_name="lsa1",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, False, UTC, "2018-04-02  15:33:21.294238", "lsa1", "user1", "5", True,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="lsa2",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, False, UTC, "2018-04-02  15:33:21", "lsa2", "user2", "6", True,
    ), (
        TimingUpdate(user="user1",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, False, UTC, "2018-04-02  15:33:21.294238", "", "user1", "5", False,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, False, UTC, "2018-04-02  15:33:21", "", "user2", "6", False,
    ),
    (None, True, False, tzoffset(name="CET", offset=1), "", "", "", "", False),
    (None, False, False, tzoffset(name="CET", offset=1), "", "", "", "", False),
    (
        TimingUpdate(user="user1",
                     lsa_name="lsa1",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=4),
        True, False, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21.294238", "lsa1", "user1", "5", True,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="lsa2",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=5),
        False, False, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21", "lsa2", "user2", "6", True,
    ), (
        TimingUpdate(user="user1",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=4),
        True, False, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21.294238", "", "user1", "5", False,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=5),
        False, False, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21", "", "user2", "6", False,
    ),
    (None, True, True, None, "", "", "", "", False),
    (None, False, True, None, "", "", "", "", False),
    (
        TimingUpdate(user="user1",
                     lsa_name="lsa1",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, True, None, "2018-04-02  15:33:21.294238 UTC", "lsa1", "user1", "5", True,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="lsa2",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, True, None, "2018-04-02  15:33:21 UTC", "lsa2", "user2", "6", True,
    ), (
        TimingUpdate(user="user1",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, True, None, "2018-04-02  15:33:21.294238 UTC", "", "user1", "5", False,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, True, None, "2018-04-02  15:33:21 UTC", "", "user2", "6", False,
    ),
    (None, True, True, UTC, "", "", "", "", False),
    (None, False, True, UTC, "", "", "", "", False),
    (
        TimingUpdate(user="user1",
                     lsa_name="lsa1",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, True, UTC, "2018-04-02  15:33:21.294238 UTC", "lsa1", "user1", "5", True,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="lsa2",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, True, UTC, "2018-04-02  15:33:21 UTC", "lsa2", "user2", "6", True,
    ), (
        TimingUpdate(user="user1",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=4),
        True, True, UTC, "2018-04-02  15:33:21.294238 UTC", "", "user1", "5", False,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238Z"),
                     offset=5),
        False, True, UTC, "2018-04-02  15:33:21 UTC", "", "user2", "6", False,
    ),
    (None, True, True, tzoffset(name="CET", offset=1), "", "", "", "", False),
    (None, False, True, tzoffset(name="CET", offset=1), "", "", "", "", False),
    (
        TimingUpdate(user="user1",
                     lsa_name="lsa1",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=4),
        True, True, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21.294238 CET", "lsa1", "user1", "5", True,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="lsa2",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=5),
        False, True, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21 CET", "lsa2", "user2", "6", True,
    ), (
        TimingUpdate(user="user1",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=4),
        True, True, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21.294238 CET", "", "user1", "5", False,
    ), (
        TimingUpdate(user="user2",
                     lsa_name="",
                     timestamp=isoparse("2018-04-02 15:33:21.294238+01:00").replace(tzinfo=tzoffset("CET", 1)),
                     offset=5),
        False, True, tzoffset(name="CET", offset=1), "2018-04-02  15:33:21 CET", "", "user2", "6", False,
    ),
])
def test_timing_bar_on_new_timing_info(timing_update, show_us, show_tz, tz, expect_visible_separator, expected_datetime, expected_lsa_name,
                                       expected_offset, expected_user, qtbot: QtBot):
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock(), timezone=tz))
    qtbot.add_widget(view)
    view.showMicroSeconds = show_us
    view.showTimeZone = show_tz
    with qtbot.wait_exposed(view):
        view.show()
    view.model._last_info = timing_update
    view.model.timingUpdateReceived.emit(True)
    assert view._lbl_user.text() == expected_user
    assert view._lbl_beam_offset.text() == expected_offset
    assert view._lbl_lsa_name.text() == expected_lsa_name
    assert view._lbl_datetime.text() == expected_datetime
    assert view._sep_lsa.isVisible() == expect_visible_separator


@pytest.mark.parametrize("timing_update", [
    None,
    TimingUpdate(user="user2", lsa_name="", timestamp=datetime.now(), offset=5),
])
@pytest.mark.parametrize("initial_alt,info_advance,expected_alt", [
    (True, True, False),
    (False, True, True),
    (True, False, True),
    (False, False, False),
])
def test_timing_bar_on_new_timing_info_causes_alternate_background(initial_alt, info_advance, expected_alt, timing_update,
                                                                   qtbot: QtBot):
    view = TimingBar()
    qtbot.add_widget(view)
    view.model._last_info = timing_update
    view._tick_bkg = initial_alt
    view._update_alternate_indication()
    assert view._canvas._use_alternate_color == initial_alt
    view.model.timingUpdateReceived.emit(info_advance)
    assert view._canvas._use_alternate_color == expected_alt


@pytest.mark.parametrize("timing_update", [
    None,
    TimingUpdate(user="user2", lsa_name="", timestamp=datetime.now(), offset=5),
])
@pytest.mark.parametrize("info_advance", [True, False])
def test_timing_bar_on_new_timing_info_causes_canvas_redraw(qtbot: QtBot, timing_update, info_advance):
    view = TimingBar()
    qtbot.add_widget(view)
    view.model._last_info = timing_update
    with mock.patch.object(view._canvas, "update") as update:
        view.model.timingUpdateReceived.emit(info_advance)
        update.assert_called()


@pytest.mark.parametrize("timing_update", [
    None,
    TimingUpdate(user="user2", lsa_name="", timestamp=datetime.now(), offset=5),
])
@pytest.mark.parametrize("info_advance", [True, False])
def test_timing_bar_on_new_timing_info_removes_error(qtbot: QtBot, timing_update, info_advance):
    view = TimingBar()
    qtbot.add_widget(view)
    assert view.toolTip() == ""
    view.model.timingErrorReceived.emit("Test error")
    assert view.toolTip() == "Test error"
    view.model._last_info = timing_update
    view.model.timingUpdateReceived.emit(info_advance)
    assert view.toolTip() == ""


@pytest.mark.parametrize("timing_update", [
    None,
    TimingUpdate(user="user2", lsa_name="lsa1", timestamp=datetime.now(), offset=5),
])
@mock.patch("accwidgets.timing_bar.TimingBarModel.has_error", new_callable=mock.PropertyMock)
def test_timing_bar_model_error_hides_labels(has_error, qtbot: QtBot, timing_update):
    has_error.return_value = False
    view = TimingBar(model=TimingBarModel(japc=mock.MagicMock()))
    qtbot.add_widget(view)
    view.model._last_info = timing_update
    view.model.timingUpdateReceived.emit(False)
    with qtbot.wait_exposed(view):
        view.show()
    assert view._lbl_lsa_name.isVisible()
    assert view._lbl_datetime.isVisible()
    assert view._lbl_beam_offset.isVisible()
    assert view._lbl_user.isVisible()
    assert view._lbl_domain.isVisible()
    assert view._sep_lsa.isVisible() == (timing_update is not None)
    has_error.return_value = True
    view.model.timingErrorReceived.emit("Test error")
    assert not view._lbl_lsa_name.isVisible()
    assert not view._lbl_datetime.isVisible()
    assert not view._lbl_beam_offset.isVisible()
    assert not view._lbl_user.isVisible()
    assert not view._lbl_domain.isVisible()
    assert not view._sep_lsa.isVisible()


@pytest.mark.parametrize("initial_alt,indicate_heartbeat,expected_real_alt_val", [
    (True, True, True),
    (True, False, False),
    (False, True, False),
    (False, False, False),
])
@mock.patch("accwidgets.timing_bar.TimingBarModel.has_error", new_callable=mock.PropertyMock)
def test_timing_bar_model_error_disables_alternate_background(has_error, initial_alt, indicate_heartbeat,
                                                              expected_real_alt_val, qtbot: QtBot):
    has_error.return_value = False
    view = TimingBar()
    qtbot.add_widget(view)
    view.indicateHeartbeat = indicate_heartbeat
    view._tick_bkg = initial_alt
    view._update_alternate_indication()
    assert view._canvas._use_alternate_color == expected_real_alt_val
    has_error.return_value = True
    with mock.patch.object(view._canvas, "update") as update:
        view.model.timingErrorReceived.emit("Test error")
        assert view._canvas._use_alternate_color is False
        update.assert_called()


# TODO: Introduce screenshot-based tests to verify painting of the canvas


@pytest.mark.parametrize("initial_show,expected_initial_height,new_show,expected_new_height", [
    (True, 47, True, 47),
    (False, 28, True, 47),
    (True, 47, False, 28),
    (False, 28, False, 28),
])
def test_timing_canvas_set_show_supercycle_affects_height(qtbot: QtBot, initial_show, expected_initial_height, new_show,
                                                          expected_new_height):
    view = TimingBar()
    qtbot.add_widget(view)
    view._canvas.show_supercycle = initial_show
    assert view._canvas.height() == expected_initial_height
    assert view._canvas.minimumHeight() == expected_initial_height
    assert view._canvas.maximumHeight() == expected_initial_height
    view._canvas.show_supercycle = new_show
    assert view._canvas.height() == expected_new_height
    assert view._canvas.minimumHeight() == expected_new_height
    assert view._canvas.maximumHeight() == expected_new_height


@pytest.mark.parametrize("initial_show,expected_initial_size,new_show,expected_new_size", [
    (True, 14, True, 14),
    (False, 10, True, 14),
    (True, 14, False, 10),
    (False, 10, False, 10),
])
def test_timing_canvas_set_show_supercycle_affects_error_font(qtbot: QtBot, initial_show, expected_initial_size, new_show,
                                                              expected_new_size):
    view = TimingBar()
    qtbot.add_widget(view)
    view._canvas.show_supercycle = initial_show
    assert view._canvas._error_font.pointSize() == expected_initial_size
    view._canvas.show_supercycle = new_show
    assert view._canvas._error_font.pointSize() == expected_new_size


@pytest.mark.parametrize("alt", [True, False])
def test_timing_canvas_set_alternate_color(qtbot: QtBot, alt):
    view = TimingBar()
    qtbot.add_widget(view)
    with mock.patch.object(view._canvas, "update") as update:
        view._canvas.set_alternate_color(alt)
        assert view._canvas._use_alternate_color == alt
        update.assert_called()


@pytest.mark.parametrize("bg_top_color,bg_bottom_color,bg_top_alt_color,bg_bottom_alt_color", [
    (Qt.black, Qt.red, Qt.yellow, Qt.blue),
    (QColor(4, 5, 2), QColor("#23cece"), QColor(255, 255, 1), Qt.white),
])
def test_timing_canvas_update_gradients(qtbot: QtBot, bg_top_color, bg_bottom_color, bg_top_alt_color, bg_bottom_alt_color):
    view = TimingBar()
    qtbot.add_widget(view)
    palette = view.color_palette
    palette.bg_bottom_alt = bg_bottom_alt_color
    palette.bg_top_alt = bg_top_alt_color
    palette.bg_bottom = bg_bottom_color
    palette.bg_top = bg_top_color
    view.color_palette = palette
    with mock.patch.object(view._canvas._normal_gradient, "setColorAt") as set_normal_color:
        with mock.patch.object(view._canvas._alt_gradient, "setColorAt") as set_alt_color:
            view._canvas.update_gradients()
            assert set_normal_color.call_count == 2
            set_normal_color.assert_has_calls([
                mock.call(0, bg_top_color),
                mock.call(1, bg_bottom_color),
            ], any_order=True)
            assert set_alt_color.call_count == 2
            set_alt_color.assert_has_calls([
                mock.call(0, bg_top_alt_color),
                mock.call(1, bg_bottom_alt_color),
            ], any_order=True)
