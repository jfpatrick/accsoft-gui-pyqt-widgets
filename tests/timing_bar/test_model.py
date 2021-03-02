import pytest
import functools
import operator
import numpy as np
from datetime import datetime
from dateutil.tz import tzoffset, UTC
from dateutil.parser import isoparse
from freezegun import freeze_time
from pytestqt.qtbot import QtBot
from unittest import mock
from typing import Optional, Dict, Any
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QEvent
from accwidgets.timing_bar import TimingBarModel, TimingBarDomain
from accwidgets.timing_bar._model import TimingSuperCycle, TimingCycle, TimingUpdate, PyJapcSubscription
from .fixtures import *  # noqa: F401,F403


# We have to make the freeze time utc, otherwise freeze-gun seems to
# take the current timezone which lets tests fail
STATIC_TIME = datetime(year=2020, day=1, month=1, hour=4, minute=43, second=5, tzinfo=UTC)


@pytest.fixture
def subscribe_param_side_effect():

    def _wrapper(ctim_sub: Optional[mock.MagicMock] = None, xtim_sub: Optional[mock.MagicMock] = None,
                 ctim_payload: Optional[Dict[str, Any]] = None, xtim_payload: Optional[Dict[str, Any]] = None,
                 xtim_header: Optional[Dict[str, Any]] = None):
        ctim_sub = ctim_sub or mock.MagicMock()
        xtim_sub = xtim_sub or mock.MagicMock()
        ctim_payload = ctim_payload or {}
        xtim_payload = xtim_payload or {}
        xtim_header = xtim_header or {}

        def side_effect(parameterName: str, *_, onValueReceived, onException, **__):
            exc = mock.MagicMock()
            exc.getHeader.return_value.isFirstUpdate.return_value = False
            raise_exception = functools.partial(onException, parameterName, "", exc)
            if parameterName.startswith("XTIM"):
                exc.getMessage.return_value = "XTIM exception"
                xtim_sub.raise_exception = raise_exception  # type: ignore
                xtim_sub.value_callback = functools.partial(onValueReceived, parameterName, xtim_payload, xtim_header)  # type: ignore
                return xtim_sub
            exc.getMessage.return_value = "CTIM exception"
            ctim_sub.raise_exception = raise_exception  # type: ignore
            ctim_sub.value_callback = functools.partial(onValueReceived, parameterName, ctim_payload)  # type: ignore
            return ctim_sub

        return side_effect

    return _wrapper


@pytest.mark.parametrize("name", ["", "dev/prop#filed", "dev/prop"])
@pytest.mark.parametrize("selector", ["", "TEST.USER.ALL", "TEST.PARTY.ION"])
@pytest.mark.parametrize("is_monitoring,new_val,expected_orig_val,expected_new_val,should_start,should_stop", [
    (True, True, True, True, True, False),
    (True, False, True, False, False, True),
    (False, True, False, True, True, False),
    (False, False, False, False, False, True),
])
def test_subscription_wrapper_monitoring(name, selector, is_monitoring, new_val, expected_new_val, expected_orig_val,
                                         should_start, should_stop):
    sh = mock.MagicMock()
    sh.monitoring = is_monitoring
    sh.isMonitoring.side_effect = lambda: sh.monitoring

    def start():
        sh.monitoring = True

    def stop():
        sh.monitoring = False

    sh.stopMonitoring.side_effect = stop
    sh.startMonitoring.side_effect = start

    wrapper = PyJapcSubscription(param_name=name,
                                 selector=selector,
                                 handler=sh)
    assert wrapper.monitoring == expected_orig_val
    wrapper.set_monitoring(new_val)
    if should_start:
        sh.startMonitoring.assert_called_once()
    else:
        sh.startMonitoring.assert_not_called()
    if should_stop:
        sh.stopMonitoring.assert_called_once()
    else:
        sh.stopMonitoring.assert_not_called()
    assert wrapper.monitoring == expected_new_val


def test_timing_supercycle_chooses_proper_mode(supercycle_obj: TimingSuperCycle):
    assert len(supercycle_obj.cycles) == 2
    assert supercycle_obj.cycles[0].user == "normal-user-1"
    assert supercycle_obj.cycles[1].user == "normal-user-2"
    supercycle_obj.spare_mode = True
    assert len(supercycle_obj.cycles) == 1
    assert supercycle_obj.cycles[0].user == "spare-user-1"
    supercycle_obj.spare_mode = False
    assert len(supercycle_obj.cycles) == 2
    assert supercycle_obj.cycles[0].user == "normal-user-1"
    assert supercycle_obj.cycles[1].user == "normal-user-2"


def test_timing_supercycle_cycle_basic_period_succeeds(supercycle_obj: TimingSuperCycle):
    with pytest.raises(ValueError):
        # Negative
        supercycle_obj.cycle_at_basic_period(-1)
    assert supercycle_obj.cycle_at_basic_period(0) == (0, supercycle_obj.normal[0])
    assert supercycle_obj.cycle_at_basic_period(1) == (1, supercycle_obj.normal[1])
    assert supercycle_obj.cycle_at_basic_period(2) == (1, supercycle_obj.normal[1])
    assert supercycle_obj.cycle_at_basic_period(3) == (1, supercycle_obj.normal[1])
    with pytest.raises(ValueError):
        # After supercycle ended
        supercycle_obj.cycle_at_basic_period(4)
    with pytest.raises(ValueError):
        # After supercycle ended
        supercycle_obj.cycle_at_basic_period(5)
    supercycle_obj.spare_mode = True
    with pytest.raises(ValueError):
        # Negative
        supercycle_obj.cycle_at_basic_period(-1)
    assert supercycle_obj.cycle_at_basic_period(0) == (0, supercycle_obj.spare[0])
    with pytest.raises(ValueError):
        # After supercycle ended
        supercycle_obj.cycle_at_basic_period(1)
    with pytest.raises(ValueError):
        # After supercycle ended
        supercycle_obj.cycle_at_basic_period(2)
    with pytest.raises(ValueError):
        # After supercycle ended
        supercycle_obj.cycle_at_basic_period(3)


def test_model_detaches_japc_on_destroy(qtbot):
    _ = qtbot
    japc = mock.MagicMock()
    sh = mock.MagicMock()

    model = TimingBarModel(japc=japc)
    model._active_subs = [PyJapcSubscription(param_name="test",
                                             handler=sh,
                                             selector="")]

    sh.stopMonitoring.assert_not_called()
    QApplication.instance().sendEvent(model, QEvent(QEvent.DeferredDelete))  # The only working way of triggering "destroyed" signal
    sh.stopMonitoring.assert_called_once()


@pytest.mark.parametrize("with_bcd,fails", [
    (True, False),
    (False, True),
])
def test_model_supercycle_fails_without_bcd(with_bcd, fails):
    model = TimingBarModel()
    model._bcd = mock.MagicMock() if with_bcd else None
    if fails:
        with pytest.raises(TypeError):
            model.supercycle
    else:
        assert model.supercycle == model._bcd.cycles


def test_model_cycle_count_fixed_without_bcd():
    model = TimingBarModel()
    model._bcd = None
    assert model.cycle_count == 128


@pytest.mark.parametrize("normal_cycle_count,spare_cycle_count,spare_mode,expected_count", [
    (3, 5, False, 3),
    (3, 5, True, 5),
])
def test_model_cycle_count_calculates_with_bcd(normal_cycle_count, spare_cycle_count, spare_mode, expected_count):
    model = TimingBarModel()
    model._bcd = TimingSuperCycle(normal=[None] * normal_cycle_count,
                                  spare=[None] * spare_cycle_count,
                                  spare_mode=spare_mode)
    assert model.cycle_count == expected_count


def test_model_supercycle_duration_fixed_without_bcd():
    model = TimingBarModel()
    model._bcd = None
    assert model.supercycle_duration == 128


@pytest.mark.parametrize("normal_cycle_lengths,spare_cycle_lengths,spare_mode,expected_duration", [
    ([2, 1, 4], [1, 3, 1], False, 7),
    ([2, 1, 4], [1, 3, 1], True, 5),
])
def test_model_supercycle_duration_calculates_from_bcd(normal_cycle_lengths, spare_cycle_lengths, spare_mode, expected_duration):
    model = TimingBarModel()

    def make_cycle(duration: int):
        obj = mock.MagicMock()
        obj.duration = duration
        return obj
    model._bcd = TimingSuperCycle(normal=list(map(make_cycle, normal_cycle_lengths)),
                                  spare=list(map(make_cycle, spare_cycle_lengths)),
                                  spare_mode=spare_mode)
    assert model.supercycle_duration == expected_duration


def test_model_current_cycle_index_fails_without_bcd():
    model = TimingBarModel()
    model._bcd = None
    with pytest.raises(TypeError):
        model.current_cycle_index


def test_model_current_cycle_index_with_invalid_basic_period():
    model = TimingBarModel()
    model._bcd = mock.MagicMock()
    model._bcd.cycle_at_basic_period.side_effect = ValueError
    assert model.current_cycle_index == -1


@pytest.mark.parametrize("corresponding_cycle", [None, object()])
@pytest.mark.parametrize("cycle_index", [-1, 0, 1, 3])
def test_model_current_cycle_index_with_valid_basic_period(cycle_index, corresponding_cycle):
    model = TimingBarModel()
    model._bcd = mock.MagicMock()
    model._bcd.cycle_at_basic_period.return_value = cycle_index, corresponding_cycle
    assert model.current_cycle_index == cycle_index


@pytest.mark.parametrize("initial_domain,set_domain,reset_domain,should_modify_subs", [
    (TimingBarDomain.LEI, TimingBarDomain.LHC, TimingBarDomain.LHC, False),
    (TimingBarDomain.LEI, TimingBarDomain.LHC, TimingBarDomain.ADE, True),
])
def test_model_reattaches_pyjapc_on_domain_reset(initial_domain, set_domain, reset_domain, should_modify_subs):
    japc_mock = mock.MagicMock()
    subscription_mock = mock.MagicMock()
    japc_mock.subscribeParam.return_value = subscription_mock
    model = TimingBarModel(domain=initial_domain, japc=japc_mock)
    subscription_mock.startMonitoring.assert_not_called()
    subscription_mock.stopMonitoring.assert_not_called()
    japc_mock.subscribeParam.assert_not_called()
    model.domain = set_domain
    japc_mock.subscribeParam.assert_called_once()
    subscription_mock.startMonitoring.assert_called_once()
    subscription_mock.stopMonitoring.assert_not_called()
    japc_mock.subscribeParam.reset_mock()
    subscription_mock.startMonitoring.reset_mock()
    subscription_mock.stopMonitoring.reset_mock()
    model.domain = reset_domain
    if should_modify_subs:
        japc_mock.subscribeParam.assert_called_once()
        subscription_mock.startMonitoring.assert_called_once()
        subscription_mock.stopMonitoring.assert_called_once()
    else:
        japc_mock.subscribeParam.assert_not_called()
        subscription_mock.startMonitoring.assert_not_called()
        subscription_mock.stopMonitoring.assert_not_called()


@pytest.mark.parametrize("initial_domain,new_domain,should_trigger", [
    (TimingBarDomain.LEI, TimingBarDomain.LEI, False),
    (TimingBarDomain.LEI, TimingBarDomain.ADE, True),
])
def test_model_domain_change_issues_signal(qtbot: QtBot, initial_domain, new_domain, should_trigger):
    model = TimingBarModel(domain=initial_domain, japc=mock.MagicMock())
    with qtbot.wait_signal(model.domainNameChanged, raising=False, timeout=100) as blocker:
        model.domain = new_domain
    assert blocker.signal_triggered == should_trigger


@pytest.mark.parametrize("domain,xtim_first_update,xtim_err,ctim_err,expect_err", [
    (TimingBarDomain.PSB, True, True, True, True),
    (TimingBarDomain.PSB, False, True, True, True),
    (TimingBarDomain.PSB, False, False, True, True),
    (TimingBarDomain.PSB, True, True, False, False),
    (TimingBarDomain.PSB, False, True, False, True),
    (TimingBarDomain.PSB, False, False, False, False),
    (TimingBarDomain.LHC, True, True, False, False),
    (TimingBarDomain.LHC, False, True, False, True),
    (TimingBarDomain.LHC, False, False, False, False),
])
def test_model_remote_connection_error(qtbot: QtBot, domain, xtim_err, ctim_err, xtim_first_update, expect_err, subscribe_param_side_effect):
    xtim_sub = mock.MagicMock()
    ctim_sub = mock.MagicMock()

    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(ctim_sub=ctim_sub, xtim_sub=xtim_sub)

    model = TimingBarModel(domain=domain, japc=japc_mock)
    model.activate()
    if xtim_err:
        xtim_sub.raise_exception.args[2].getHeader.return_value.isFirstUpdate.return_value = xtim_first_update
        with qtbot.wait_signal(model.timingErrorReceived, raising=False, timeout=100) as blocker:
            xtim_sub.raise_exception()
        if xtim_first_update:
            assert not blocker.signal_triggered
        else:
            assert blocker.signal_triggered
            assert blocker.args == ["XTIM exception"]
    if ctim_err:
        with qtbot.wait_signal(model.timingErrorReceived) as blocker:
            ctim_sub.raise_exception()
        assert blocker.args == ["CTIM exception"]
    assert model.has_error == expect_err


@pytest.mark.parametrize("domain,xtim_err,ctim_err,expect_errors", [
    (TimingBarDomain.PSB, True, True, ["ctim", "xtim"]),
    (TimingBarDomain.PSB, False, True, ["ctim"]),
    (TimingBarDomain.PSB, True, False, ["xtim"]),
    (TimingBarDomain.PSB, False, False, []),
    (TimingBarDomain.LHC, True, False, ["xtim"]),
    (TimingBarDomain.LHC, False, False, []),
])
def test_model_subscription_monitoring_error(qtbot: QtBot, domain, xtim_err, ctim_err, expect_errors):
    xtim_sub = mock.MagicMock()
    if xtim_err:
        xtim_sub.startMonitoring.side_effect = Exception("xtim")
    ctim_sub = mock.MagicMock()
    if ctim_err:
        ctim_sub.startMonitoring.side_effect = Exception("ctim")

    def subscribe_param(parameterName: str, *_, **__):
        return xtim_sub if parameterName.startswith("XTIM") else ctim_sub

    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param

    should_have_error = len(expect_errors) > 0
    model = TimingBarModel(domain=domain, japc=japc_mock)
    with qtbot.wait_signals([model.timingErrorReceived, model.timingErrorReceived], raising=False, timeout=100, order="strict") as blocker:
        model.activate()
    assert model.has_error == should_have_error
    signal_args = list(map(operator.itemgetter(0), map(operator.attrgetter("args"), blocker.all_signals_and_args)))
    assert signal_args == expect_errors


@pytest.mark.parametrize("domain,xtim_err,ctim_err,expect_errors", [
    (TimingBarDomain.PSB, True, True, ["ctim", "xtim"]),
    (TimingBarDomain.PSB, False, True, ["ctim"]),
    (TimingBarDomain.PSB, True, False, ["xtim"]),
    (TimingBarDomain.PSB, False, False, []),
    (TimingBarDomain.LHC, True, False, ["xtim"]),
    (TimingBarDomain.LHC, False, False, []),
])
def test_model_subscription_creation_error(qtbot: QtBot, domain, xtim_err, ctim_err, expect_errors):

    def subscribe_param(parameterName: str, *_, **__):
        is_xtim = parameterName.startswith("XTIM")
        if is_xtim and xtim_err:
            raise Exception("xtim")
        elif not is_xtim and ctim_err:
            raise Exception("ctim")
        return mock.MagicMock()

    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param

    should_have_error = len(expect_errors) > 0
    model = TimingBarModel(domain=domain, japc=japc_mock)
    with qtbot.wait_signals([model.timingErrorReceived, model.timingErrorReceived], raising=False, timeout=100, order="strict") as blocker:
        model.activate()
    assert model.has_error == should_have_error
    signal_args = list(map(operator.itemgetter(0), map(operator.attrgetter("args"), blocker.all_signals_and_args)))
    assert signal_args == expect_errors


@mock.patch("accwidgets.timing_bar._model.import_pyjapc")
def test_model_activate_imports_pyjapc_only_once(import_pyjapc):
    model = TimingBarModel()
    import_pyjapc.assert_not_called()
    model.activate()
    import_pyjapc.assert_called_once()
    import_pyjapc.reset_mock()
    model.activate()
    import_pyjapc.assert_not_called()


@pytest.mark.parametrize("tz,expected_argument", [
    (None, UTC),
    (tzoffset("CET", 1), tzoffset("CET", 1)),
    (UTC, UTC),
])
@mock.patch("accwidgets.timing_bar._model.import_pyjapc")
def test_model_default_pyjapc_constructor(import_pyjapc, tz, expected_argument):
    model = TimingBarModel(timezone=tz)
    import_pyjapc.assert_not_called()
    model.activate()
    import_pyjapc.return_value.assert_called_once_with(selector="", incaAcceleratorName=None, timeZone=expected_argument)


@mock.patch("accwidgets.timing_bar._model.import_pyjapc")
def test_model_activate_does_not_import_pyjapc_if_provided(import_pyjapc):
    model = TimingBarModel(japc=mock.MagicMock())
    import_pyjapc.assert_not_called()
    model.activate()
    import_pyjapc.assert_not_called()


@pytest.mark.parametrize("is_designer_value,should_import", [
    (True, False),
    (False, True),
])
@mock.patch("accwidgets.timing_bar._model.import_pyjapc")
@mock.patch("accwidgets.timing_bar._model.is_designer")
def test_model_activate_does_not_import_pyjapc_in_designer(is_designer, import_pyjapc, is_designer_value, should_import):
    is_designer.return_value = is_designer_value
    model = TimingBarModel()
    import_pyjapc.assert_not_called()
    model.activate()
    if should_import:
        import_pyjapc.assert_called_once()
    else:
        import_pyjapc.assert_not_called()


@pytest.mark.parametrize("is_designer_value,should_issue_update", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.timing_bar._model.import_pyjapc")
@mock.patch("accwidgets.timing_bar._model.is_designer")
def test_model_activate_issues_fake_update_in_designer(is_designer, _, qtbot: QtBot, is_designer_value, should_issue_update):
    is_designer.return_value = is_designer_value
    model = TimingBarModel()
    with qtbot.wait_signal(model.timingUpdateReceived, raising=False, timeout=100) as blocker:
        model.activate()
    assert blocker.signal_triggered == should_issue_update
    if should_issue_update:
        assert blocker.args == [True]


@pytest.mark.parametrize("has_pre_ctim_err,has_pre_xtim_err,ctim_callback_fired,xtim_callback_fired,should_clear_err_state", [
    (True, True, True, False, False),
    (True, False, True, False, True),
    (False, True, True, False, False),
    (True, True, True, True, True),
    (True, False, True, True, True),
    (False, True, True, True, True),
    (True, True, False, True, False),
    (True, False, False, True, False),
    (False, True, False, True, True),
])
def test_model_time_callback_removes_error_state(subscribe_param_side_effect, has_pre_ctim_err, has_pre_xtim_err,
                                                 xtim_callback_fired, ctim_callback_fired, should_clear_err_state):
    ctim_sub = mock.MagicMock()
    xtim_sub = mock.MagicMock()

    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(ctim_sub=ctim_sub, xtim_sub=xtim_sub)

    model = TimingBarModel(domain=TimingBarDomain.PSB, japc=japc_mock)
    model.activate()
    if has_pre_xtim_err:
        xtim_sub.raise_exception()
    if has_pre_ctim_err:
        ctim_sub.raise_exception()
    assert model.has_error
    if ctim_callback_fired:
        ctim_sub.value_callback()
    if xtim_callback_fired:
        xtim_sub.value_callback()
    assert model.has_error != should_clear_err_state


def test_model_ctim_callback_creates_new_bcd(qtbot: QtBot, subscribe_param_side_effect):
    ctim_sub = mock.MagicMock()
    ctim_payload = {
        "normalBcdBeamOffsetsBp": np.array([0, 3, 7]),
        "normalCycleLengthsBp": np.array([3, 4, 2]),
        "normalLsaCycleNames": np.array(["norm1", "norm2", "norm3"]),
        "normalUsers": np.array(["nuser1", "nuser2", "nuser3"]),
        # Spares are not participating, until XTIM callback switches the supercycle into the spare mode
        "spareBcdBeamOffsetsBp": np.array([1, 2]),
        "spareCycleLengthsBp": np.array([1, 3]),
        "spareLsaCycleNames": np.array(["spare1", "spare2"]),
        "spareUsers": np.array(["suser1", "suser2"]),
    }
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(ctim_sub=ctim_sub, ctim_payload=ctim_payload)

    model = TimingBarModel(domain=TimingBarDomain.PSB, japc=japc_mock)
    model.activate()
    with pytest.raises(TypeError):
        model.supercycle
    with qtbot.wait_signal(model.timingUpdateReceived) as blocker:
        with qtbot.assert_not_emitted(model.timingErrorReceived):
            ctim_sub.value_callback()
    assert blocker.args == [False]
    assert list(map(operator.attrgetter("offset"), model.supercycle)) == [0, 3, 7]
    assert list(map(operator.attrgetter("duration"), model.supercycle)) == [3, 4, 2]
    assert list(map(operator.attrgetter("lsa_name"), model.supercycle)) == ["norm1", "norm2", "norm3"]
    assert list(map(operator.attrgetter("user"), model.supercycle)) == ["nuser1", "nuser2", "nuser3"]


def test_model_ctim_callback_creates_empty_bcd_with_missing_keys(qtbot: QtBot, subscribe_param_side_effect):
    ctim_sub = mock.MagicMock()
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(ctim_sub=ctim_sub)

    model = TimingBarModel(domain=TimingBarDomain.PSB, japc=japc_mock)
    model.activate()
    with pytest.raises(TypeError):
        model.supercycle
    with qtbot.wait_signal(model.timingUpdateReceived) as blocker:
        with qtbot.assert_not_emitted(model.timingErrorReceived):
            ctim_sub.value_callback()
    assert blocker.args == [False]
    assert list(map(operator.attrgetter("offset"), model.supercycle)) == []
    assert list(map(operator.attrgetter("duration"), model.supercycle)) == []
    assert list(map(operator.attrgetter("lsa_name"), model.supercycle)) == []
    assert list(map(operator.attrgetter("user"), model.supercycle)) == []


def test_model_ctim_callback_fails_on_inconsistent_data(qtbot: QtBot, subscribe_param_side_effect):
    ctim_sub = mock.MagicMock()
    ctim_payload = {
        "normalBcdBeamOffsetsBp": np.array([0, 3]),
        "normalCycleLengthsBp": np.array([3, 4]),
        "normalLsaCycleNames": np.array(["norm1", "norm2", "norm3"]),
        "normalUsers": np.array(["nuser1", "nuser2", "nuser3"]),
    }
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(ctim_sub=ctim_sub, ctim_payload=ctim_payload)

    model = TimingBarModel(domain=TimingBarDomain.PSB, japc=japc_mock)
    model.activate()
    with qtbot.wait_signal(model.timingErrorReceived) as blocker:
        with qtbot.assert_not_emitted(model.timingUpdateReceived):
            ctim_sub.value_callback()
    assert model.has_error
    assert blocker.args == ["Received contradictory supercycle structure."]


@pytest.mark.parametrize("flag_exists,flag_val,should_update", [
    (True, True, False),
    (True, False, True),
    (False, False, True),
])
def test_model_xtim_callback_ignores_first_update(qtbot: QtBot, subscribe_param_side_effect, flag_exists, flag_val, should_update):
    xtim_sub = mock.MagicMock()
    xtim_header = {"isFirstUpdate": flag_val} if flag_exists else {}

    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_sub=xtim_sub, xtim_header=xtim_header)

    model = TimingBarModel(japc=japc_mock)
    model.activate()
    with qtbot.wait_signal(model.timingUpdateReceived, raising=False, timeout=100) as blocker:
        xtim_sub.value_callback()
    assert blocker.signal_triggered == should_update


@pytest.mark.parametrize("header,data,expected_time", [
    ({"acqStamp": isoparse("2020-01-01 05:11:03Z")}, {}, isoparse("2020-01-01 05:11:03Z")),
    ({}, {"acqStamp": isoparse("2019-03-02 03:18:04Z")}, isoparse("2019-03-02 03:18:04Z")),
    (
        {"acqStamp": isoparse("2020-01-01 05:11:03Z")},
        {"acqStamp": isoparse("2019-03-02 03:18:04Z")},
        isoparse("2019-03-02 03:18:04Z"),
    ),
    ({}, {}, STATIC_TIME),
])
@freeze_time(STATIC_TIME)
def test_model_xtim_callback_merges_acq_stamp(subscribe_param_side_effect, header, data, expected_time):
    xtim_sub = mock.MagicMock()
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_sub=xtim_sub,
                                                                       xtim_header=header,
                                                                       xtim_payload=data)

    model = TimingBarModel(japc=japc_mock)
    model.activate()
    assert model.last_info is None
    xtim_sub.value_callback()
    assert model.last_info is not None
    assert model.last_info.timestamp.timestamp() == expected_time.timestamp()


@pytest.mark.parametrize("orig_bp,arriving_period_numbers,expected_bps,expected_changes", [
    (-1, [1000, 1001, 1002], [0, 1, 2], [True, True, True]),
    (-1, [1000, 45, 942], [0, 1, 2], [True, True, True]),
    (0, [1000, 1001, 1002], [1, 2, 3], [True, True, True]),
    (0, [1000, 45, 942], [1, 2, 3], [True, True, True]),
    (126, [1000, 1001, 1002], [127, 0, 1], [True, True, True]),
    (126, [1000, 45, 942], [127, 0, 1], [True, True, True]),
    # Should not advance on identical period numbers arriving
    (-1, [1000, 1000, 1000], [0, 0, 0], [True, False, False]),
    (4, [1000, 1000, 1000], [5, 5, 5], [True, False, False]),
    (126, [1000, 1000, 1000], [127, 127, 127], [True, False, False]),
    (127, [1000, 1000, 1000], [0, 0, 0], [True, False, False]),
])
def test_model_xtim_callback_basic_period_advances_in_non_supercycle_mode(qtbot: QtBot, subscribe_param_side_effect, orig_bp, arriving_period_numbers, expected_bps, expected_changes):
    xtim_sub = mock.MagicMock()
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_sub=xtim_sub)

    model = TimingBarModel(japc=japc_mock)
    model._bcd = None
    model.activate()
    model._current_bp = orig_bp
    for remote_number, expected_bp, expect_change in zip(arriving_period_numbers, expected_bps, expected_changes):
        # Replace args of functools.partial
        args = list(xtim_sub.value_callback.args)
        args[1] = {"BASIC_PERIOD_NB": remote_number}
        xtim_sub.value_callback = functools.partial(xtim_sub.value_callback.func, *args)
        with qtbot.wait_signal(model.timingUpdateReceived) as blocker:
            xtim_sub.value_callback()
        assert blocker.args == [expect_change]
        assert model.current_basic_period == expected_bp


@pytest.mark.parametrize("orig_bp,arriving_period_numbers,expected_bps,expected_changes", [
    (-1, [1000, 1001, 1002], [999, 1000, 1001], [True, True, True]),
    (-1, [1000, 45, 942], [999, 44, 941], [True, True, True]),
    (0, [1000, 1001, 1002], [999, 1000, 1001], [True, True, True]),
    (0, [1000, 45, 942], [999, 44, 941], [True, True, True]),
    (126, [1000, 1001, 1002], [999, 1000, 1001], [True, True, True]),
    (126, [1000, 45, 942], [999, 44, 941], [True, True, True]),
    # Should not advance on identical period numbers arriving
    (-1, [1000, 1000, 1000], [999, 999, 999], [True, False, False]),
    (4, [1000, 1000, 1000], [999, 999, 999], [True, False, False]),
    (126, [1000, 1000, 1000], [999, 999, 999], [True, False, False]),
    (127, [1000, 1000, 1000], [999, 999, 999], [True, False, False]),
])
def test_model_xtim_callback_basic_period_advances_in_supercycle_mode(qtbot: QtBot, subscribe_param_side_effect, orig_bp, arriving_period_numbers, expected_bps, expected_changes):
    xtim_sub = mock.MagicMock()
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_sub=xtim_sub)

    model = TimingBarModel(japc=japc_mock)
    model.activate()
    model._bcd = mock.MagicMock()
    model._current_bp = orig_bp
    for remote_number, expected_bp, expect_change in zip(arriving_period_numbers, expected_bps, expected_changes):
        # Replace args of functools.partial
        args = list(xtim_sub.value_callback.args)
        args[1] = {"BASIC_PERIOD_NB": remote_number}
        xtim_sub.value_callback = functools.partial(xtim_sub.value_callback.func, *args)
        with qtbot.wait_signal(model.timingUpdateReceived) as blocker:
            xtim_sub.value_callback()
        assert blocker.args == [expect_change]
        assert model.current_basic_period == expected_bp


def test_model_detach_pyjapc_only_affects_known_subscriptions():
    japc_mock = mock.MagicMock()
    japc_mock._transformSubscribeCacheKey.side_effect = lambda param, sel: param + "@" + (sel or "")
    pre_existing_sub = mock.MagicMock()
    xtim_sub = mock.MagicMock()
    ctim_sub = mock.MagicMock()
    japc_mock._subscriptionHandleDict = {
        "dummy": [pre_existing_sub],
    }

    def subscribe_side_effect(parameterName: str, *_, timingSelectorOverride, **__):
        sub = xtim_sub if parameterName.startswith("XTIM") else ctim_sub
        japc_mock._subscriptionHandleDict[japc_mock._transformSubscribeCacheKey(parameterName, timingSelectorOverride)] = [sub]
        return sub

    japc_mock.subscribeParam.side_effect = subscribe_side_effect

    def meaningful_subscriptions():
        def calc(key: str):
            try:
                return len(japc_mock._subscriptionHandleDict[key])
            except KeyError:
                return 0

        return [key for key in japc_mock._subscriptionHandleDict.keys() if calc(key) > 0]

    model = TimingBarModel(japc=japc_mock)
    pre_existing_sub.stopMonitoring.assert_not_called()
    xtim_sub.startMonitoring.assert_not_called()
    xtim_sub.stopMonitoring.assert_not_called()
    ctim_sub.startMonitoring.assert_not_called()
    ctim_sub.stopMonitoring.assert_not_called()
    japc_mock.startSubscriptions.assert_not_called()
    assert meaningful_subscriptions() == ["dummy"]
    model.activate()
    xtim_sub.startMonitoring.assert_called_once()
    xtim_sub.stopMonitoring.assert_not_called()
    xtim_sub.startMonitoring.reset_mock()
    ctim_sub.startMonitoring.assert_called_once()
    ctim_sub.stopMonitoring.assert_not_called()
    ctim_sub.startMonitoring.reset_mock()
    pre_existing_sub.stopMonitoring.assert_not_called()
    japc_mock.startSubscriptions.assert_not_called()
    assert len(meaningful_subscriptions()) == 3
    model._detach_japc()
    xtim_sub.startMonitoring.assert_not_called()
    xtim_sub.stopMonitoring.assert_called_once()
    ctim_sub.startMonitoring.assert_not_called()
    ctim_sub.stopMonitoring.assert_called_once()
    pre_existing_sub.stopMonitoring.assert_not_called()
    japc_mock.clearSubscriptions.assert_not_called()
    japc_mock.stopSubscriptions.assert_not_called()
    assert meaningful_subscriptions() == ["dummy"]


def test_model_detach_pyjapc_resets_properties(subscribe_param_side_effect):
    xtim_sub = mock.MagicMock()
    xtim_data = {"BASIC_PERIOD_NB": 14}
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_sub=xtim_sub, xtim_payload=xtim_data)

    model = TimingBarModel(japc=japc_mock)
    model.activate()
    assert model.current_basic_period == -1
    assert model.last_info is None
    xtim_sub.value_callback()
    assert model.current_basic_period != -1
    assert model.last_info is not None
    model._bcd = mock.MagicMock()
    model._detach_japc()
    assert model.current_basic_period == -1
    assert model.last_info is None
    assert model._bcd is None


def test_model_detach_pyjapc_does_not_fail_on_gc_call(subscribe_param_side_effect):
    xtim_sub = mock.MagicMock()
    xtim_data = {"BASIC_PERIOD_NB": 14}
    japc_mock = mock.MagicMock()
    japc_mock._java_gc.trigger.side_effect = AttributeError
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_sub=xtim_sub, xtim_payload=xtim_data)

    model = TimingBarModel(japc=japc_mock)
    model.activate()
    assert model.current_basic_period == -1
    assert model.last_info is None
    xtim_sub.value_callback()
    assert model.current_basic_period != -1
    assert model.last_info is not None
    model._bcd = mock.MagicMock()
    model._detach_japc()
    # If succeeded, means java_gc Attribute error was properly caught
    assert model.current_basic_period == -1
    assert model.last_info is None
    assert model._bcd is None


def test_model_detach_pyjapc_does_not_fail_without_japc():
    model = TimingBarModel()
    assert model._japc is None
    model._bcd = mock.MagicMock()
    model._detach_japc()
    assert model._japc is None
    assert model._bcd is None


def test_model_attach_japc_clears_bcd():
    japc_mock = mock.MagicMock()
    model = TimingBarModel(japc=japc_mock)
    model._bcd = mock.MagicMock()
    assert model.supercycle is not None
    model.activate()
    with pytest.raises(TypeError):
        model.supercycle


def test_model_ctim_subscription_does_not_fail_for_unknown_domain():
    japc_mock = mock.MagicMock()
    import accwidgets.timing_bar._model
    assert TimingBarDomain.LHC not in accwidgets.timing_bar._model._CTIM_MAPPING
    model = TimingBarModel(japc=japc_mock, domain=TimingBarDomain.LHC)
    japc_mock.subsribeParam.assert_not_called()
    model._listen_supercycle_updates()
    japc_mock.subscribeParam.assert_not_called()


def test_model_ctim_subscription_does_not_fail_without_japc():
    model = TimingBarModel(japc=None, domain=TimingBarDomain.LHC)
    model._listen_supercycle_updates()
    assert model._japc is None


def test_model_xtim_subscription_fails_for_unknown_domain():
    japc_mock = mock.MagicMock()
    import accwidgets.timing_bar._model

    assert "NOT_EXISTING" not in accwidgets.timing_bar._model._XTIM_MAPPING
    model = TimingBarModel(japc=japc_mock, domain="NOT_EXISTING")
    japc_mock.subsribeParam.assert_not_called()
    with pytest.raises(ValueError, match="Unknown timing domain 'NOT_EXISTING'."):
        model._listen_timing_events()


def test_model_xtim_subscription_does_not_fail_without_japc():
    model = TimingBarModel(japc=None, domain=TimingBarDomain.LHC)
    model._listen_timing_events()
    assert model._japc is None


@pytest.mark.parametrize("timing_update,expected_timestamp", [
    (None, isoparse("2018-04-02 15:33:21Z")),
    ({}, isoparse("2018-04-02 15:33:21Z")),
    ({"acqStamp": isoparse("2019-05-01 14:31:24Z")}, isoparse("2019-05-01 14:31:24Z")),
])
@freeze_time(STATIC_TIME)
def test_model_recalculate_last_info_adjusts_timestamps(timing_update, expected_timestamp, subscribe_param_side_effect):
    xtim_sub = mock.MagicMock()
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_payload=timing_update, xtim_sub=xtim_sub)
    model = TimingBarModel(japc=japc_mock)
    model.activate()
    model._last_info = TimingUpdate(timestamp=isoparse("2018-04-02 15:33:21Z"),
                                    offset=0,
                                    lsa_name="lsa1",
                                    user="user1")
    assert model.last_info.timestamp.timestamp() == isoparse("2018-04-02 15:33:21Z").timestamp()
    xtim_sub.value_callback()
    assert model.last_info.timestamp.timestamp() == expected_timestamp.timestamp()


@pytest.mark.parametrize("is_supercycle,initial_is_spare,timing_update,expected_cycles_length", [
    (True, False, {"BEAM_LEVEL_NORMAL": True}, 2),
    (True, False, {"BEAM_LEVEL_SPARE": False}, 2),
    (True, False, {"BEAM_LEVEL_NORMAL": True, "BEAM_LEVEL_SPARE": False}, 2),
    (True, False, {}, 2),
    (True, True, {"BEAM_LEVEL_NORMAL": True}, 2),
    (True, True, {"BEAM_LEVEL_SPARE": False}, 2),
    (True, True, {"BEAM_LEVEL_NORMAL": True, "BEAM_LEVEL_SPARE": False}, 2),
    (True, True, {}, 2),
    (True, False, {"BEAM_LEVEL_SPARE": True}, 1),
    (True, False, {"BEAM_LEVEL_NORMAL": False}, 1),
    (True, False, {"BEAM_LEVEL_SPARE": True, "BEAM_LEVEL_NORMAL": False}, 1),
    (True, False, {"BEAM_LEVEL_SPARE": True}, 1),
    (True, False, {"BEAM_LEVEL_NORMAL": False}, 1),
    (True, False, {"BEAM_LEVEL_SPARE": True, "BEAM_LEVEL_NORMAL": False}, 1),
    (False, False, {"BEAM_LEVEL_NORMAL": True}, 128),
    (False, False, {"BEAM_LEVEL_SPARE": False}, 128),
    (False, False, {"BEAM_LEVEL_NORMAL": True, "BEAM_LEVEL_SPARE": False}, 128),
    (False, False, {}, 128),
    (False, True, {"BEAM_LEVEL_NORMAL": True}, 128),
    (False, True, {"BEAM_LEVEL_SPARE": False}, 128),
    (False, True, {"BEAM_LEVEL_NORMAL": True, "BEAM_LEVEL_SPARE": False}, 128),
    (False, True, {}, 128),
    (False, False, {"BEAM_LEVEL_SPARE": True}, 128),
    (False, False, {"BEAM_LEVEL_NORMAL": False}, 128),
    (False, False, {"BEAM_LEVEL_SPARE": True, "BEAM_LEVEL_NORMAL": False}, 128),
    (False, False, {"BEAM_LEVEL_SPARE": True}, 128),
    (False, False, {"BEAM_LEVEL_NORMAL": False}, 128),
    (False, False, {"BEAM_LEVEL_SPARE": True, "BEAM_LEVEL_NORMAL": False}, 128),
])
def test_model_recalculate_last_info_switches_supercycle_spare(is_supercycle, initial_is_spare, timing_update,
                                                               expected_cycles_length, supercycle_obj,
                                                               subscribe_param_side_effect):
    xtim_sub = mock.MagicMock()
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_payload=timing_update, xtim_sub=xtim_sub)
    model = TimingBarModel(japc=japc_mock)
    model.activate()
    supercycle_obj.spare_mode = initial_is_spare
    model._bcd = supercycle_obj if is_supercycle else None
    assert model.is_supercycle_mode == is_supercycle
    xtim_sub.value_callback()

    if is_supercycle:
        assert len(model.supercycle) == expected_cycles_length
    else:
        with pytest.raises(TypeError):
            model.supercycle


@pytest.mark.parametrize("is_supercycle,timing_update,expected_new_timestamp", [
    (True, {"acqStamp": isoparse("2015-05-21 21:54:23Z")}, STATIC_TIME),
    (True, {"acqStamp": isoparse("2015-05-21 21:54:23Z"), "BASIC_PERIOD_NB": -1}, STATIC_TIME),
    (True, {"acqStamp": isoparse("2015-05-21 21:54:23Z"), "BASIC_PERIOD_NB": 999}, STATIC_TIME),
    (True, {"acqStamp": isoparse("2015-05-21 21:54:23Z"), "BASIC_PERIOD_NB": 1}, isoparse("2015-05-21 21:54:23Z")),
    (False, {"acqStamp": isoparse("2015-05-21 21:54:23Z")}, isoparse("2015-05-21 21:54:23")),
    (False, {"acqStamp": isoparse("2015-05-21 21:54:23Z"), "BASIC_PERIOD_NB": -1}, isoparse("2015-05-21 21:54:23Z")),
    (False, {"acqStamp": isoparse("2015-05-21 21:54:23Z"), "BASIC_PERIOD_NB": 999}, isoparse("2015-05-21 21:54:23Z")),
    (False, {"acqStamp": isoparse("2015-05-21 21:54:23Z"), "BASIC_PERIOD_NB": 1}, isoparse("2015-05-21 21:54:23Z")),
])
@freeze_time(STATIC_TIME)
def test_model_recalculate_last_info_does_not_update_on_invalid_basic_period(supercycle_obj, is_supercycle, timing_update, expected_new_timestamp,
                                                                             subscribe_param_side_effect):
    xtim_sub = mock.MagicMock()
    japc_mock = mock.MagicMock()
    japc_mock.subscribeParam.side_effect = subscribe_param_side_effect(xtim_payload=timing_update, xtim_sub=xtim_sub)
    model = TimingBarModel(japc=japc_mock)
    model.activate()
    model._last_info = TimingUpdate(timestamp=STATIC_TIME,
                                    offset=0,
                                    lsa_name="lsa1",
                                    user="user1")
    model._bcd = supercycle_obj if is_supercycle else None
    assert model.is_supercycle_mode == is_supercycle
    xtim_sub.value_callback()

    assert model.last_info.timestamp.timestamp() == expected_new_timestamp.timestamp()


@pytest.mark.parametrize("data,expected_cycles", [(
    {"offsets": np.array([0]), "lengths": np.array([1]), "lsa": np.array(["lsa1"]), "users": np.array(["user1"])},
    [TimingCycle(user="user1", lsa_name="lsa1", duration=1, offset=0)],
), (
    {"offsets": 0, "lengths": np.array([1]), "lsa": np.array(["lsa1"]), "users": np.array(["user1"])},
    [TimingCycle(user="user1", lsa_name="lsa1", duration=1, offset=0)],
), (
    {"offsets": np.array([0]), "lengths": 1, "lsa": np.array(["lsa1"]), "users": np.array(["user1"])},
    [TimingCycle(user="user1", lsa_name="lsa1", duration=1, offset=0)],
), (
    {"offsets": 0, "lengths": 1, "lsa": "lsa1", "users": "user1"},
    [TimingCycle(user="user1", lsa_name="lsa1", duration=1, offset=0)],
), (
    {"offsets": np.array([0, 2]), "lengths": np.array([2, 3]), "lsa": np.array(["lsa1", "lsa2"]), "users": np.array(["user1", "user2"])},
    [
        TimingCycle(user="user1", lsa_name="lsa1", duration=2, offset=0),
        TimingCycle(user="user2", lsa_name="lsa2", duration=3, offset=2),
    ],
)])
def test_model_create_supercycle_succeeds(data, expected_cycles):
    model = TimingBarModel()
    actual_cycles = model._create_supercycle(offsets_key="offsets",
                                             lengths_key="lengths",
                                             lsa_key="lsa",
                                             users_key="users",
                                             data=data)
    assert actual_cycles == expected_cycles


@pytest.mark.parametrize("data", [{
    "offsets": np.array([0]),
    "lengths": np.array([1, 2]),
    "lsa": np.array([]),
    "users": np.array([]),
}, {
    "offsets": np.array([0]),
}, {
    "lengths": np.array([0]),
}, {
    "lsa": np.array(["lsa1"]),
}, {
    "users": np.array(["user1"]),
}])
def test_model_create_supercycle_fails(data):
    model = TimingBarModel()
    with pytest.raises(ValueError):
        model._create_supercycle(offsets_key="offsets",
                                 lengths_key="lengths",
                                 lsa_key="lsa",
                                 users_key="users",
                                 data=data)


@pytest.mark.parametrize("subs_monitoring", [
    [],
    [True],
    [True, False],
    [True, True],
    [False, False],
    [False, True],
    [True, False, False, True, False],
])
@pytest.mark.parametrize("initial_val,new_val,expected_inner_value", [
    (False, True, True),
    (False, False, None),
    (True, False, False),
    (True, True, None),
])
def test_model_monitoring_affects_all_properties(subs_monitoring, initial_val, new_val, expected_inner_value):

    def create_sub(monitoring: bool):
        sub = mock.MagicMock(spec=PyJapcSubscription)
        sub.monitoring = monitoring
        return sub

    model = TimingBarModel(japc=mock.MagicMock(), monitoring=initial_val)
    model._active_subs = list(map(create_sub, subs_monitoring))
    for sub in model._active_subs:
        sub.set_monitoring.assert_not_called()
    model.monitoring = new_val
    for sub in model._active_subs:
        if expected_inner_value is None:
            sub.set_monitoring.assert_not_called()
        else:
            sub.set_monitoring.assert_called_once_with(expected_inner_value)
