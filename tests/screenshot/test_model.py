import pytest
from typing import Optional
from pytestqt.qtbot import QtBot
from unittest import mock
from freezegun import freeze_time
from datetime import datetime
from dateutil.tz import UTC
from qtpy.QtCore import QObject
from pylogbook import Client, NamedActivity, NamedServer
from pylogbook.models import Event
from pylogbook.exceptions import LogbookError
from accwidgets.screenshot import LogbookModel
from .fixtures import *  # noqa: F401,F403


STATIC_TIME = datetime(year=2020, day=1, month=1, hour=12, minute=30, second=55, tzinfo=UTC)


def make_token(result: Optional[str]) -> Optional[mock.MagicMock]:
    if result is None:
        return None
    token = mock.MagicMock()
    token.get_encoded.return_value = result
    token.__str__.return_value = result  # type: ignore
    return token


@pytest.mark.parametrize("parent", [None, QObject()])
@pytest.mark.parametrize("activities,rbac_token,expected_activities", [
    (None, "", ()),
    (None, "abc123", ()),
    ("TEST1", "", ()),
    ("TEST1", "abc123", "TEST1"),
    (("TEST1", "TEST2"), "", ()),
    (("TEST1", "TEST2"), "abc123", ("TEST1", "TEST2")),
])
def test_init_with_existing_pylogbook(logbook, parent, activities, rbac_token, expected_activities):
    client, activities_client = logbook
    client.rbac_b64_token = rbac_token
    model = LogbookModel(logbook=logbook, parent=parent, activities=activities)
    assert model.parent() is parent
    assert model._client is client
    assert model._activities_client is activities_client
    assert model._activities_client.activities == expected_activities


@pytest.mark.parametrize("server_url,expected_url", [
    (None, NamedServer.PRO),
    ("", ""),
    ("http://localhost:3000", "http://localhost:3000"),
    (NamedServer.PRO, NamedServer.PRO),
    (NamedServer.TEST, NamedServer.TEST),
])
@pytest.mark.parametrize("parent", [None, QObject()])
@pytest.mark.parametrize("activities,rbac_token,expected_activities,expected_token", [
    (None, "", (), ""),
    (None, None, (), ""),
    (None, "abc123", (), "abc123"),
    ("TEST1", "", (), ""),
    ("TEST1", None, (), ""),
    ("TEST1", "abc123", "TEST1", "abc123"),
    (("TEST1", "TEST2"), "", (), ""),
    (("TEST1", "TEST2"), None, (), ""),
    (("TEST1", "TEST2"), "abc123", ("TEST1", "TEST2"), "abc123"),
])
@mock.patch("accwidgets.screenshot._model.Client")
@mock.patch("accwidgets.screenshot._model.ActivitiesClient")
def test_init_without_existing_pylogbook(act_client_mock, client_mock, parent, activities, server_url, rbac_token,
                                         expected_token, expected_activities, expected_url):
    result = mock.MagicMock(spec=Client)
    result.rbac_b64_token = ""
    result.server_url = ""

    def init_mock(**kwargs):
        for k, v in kwargs.items():
            if k == "rbac_token":
                k = "rbac_b64_token"
            setattr(result, k, v)
        return result

    client_mock.side_effect = init_mock
    act_client_mock.return_value.activities = ()
    model = LogbookModel(parent=parent,
                         activities=activities,
                         server_url=server_url,
                         rbac_token=rbac_token)
    assert model._client.rbac_b64_token == expected_token
    assert model._client.server_url == expected_url
    assert model.parent() is parent
    assert model._activities_client.activities == expected_activities


@pytest.mark.parametrize("server_url,rbac_token,uses_logbook,expect_raises", [
    (None, None, False, False),
    (None, None, True, False),
    (None, "", False, False),
    (None, "", True, True),
    (None, "abc123", False, False),
    (None, "abc123", True, True),
    ("http://localhost:3000", None, False, False),
    ("http://localhost:3000", None, True, True),
    ("http://localhost:3000", "", False, False),
    ("http://localhost:3000", "", True, True),
    ("http://localhost:3000", "abc123", False, False),
    ("http://localhost:3000", "abc123", True, True),
    (NamedServer.TEST, None, False, False),
    (NamedServer.TEST, None, True, True),
    (NamedServer.TEST, "", False, False),
    (NamedServer.TEST, "", True, True),
    (NamedServer.TEST, "abc123", False, False),
    (NamedServer.TEST, "abc123", True, True),
])
@pytest.mark.parametrize("parent", [None, QObject()])
@pytest.mark.parametrize("activities", [None, "TEST1", ("TEST1", "TEST2")])
@mock.patch("accwidgets.screenshot._model.Client")
def test_init_mutex_logbook_with_activities_and_rbac(_, parent, activities, server_url, rbac_token, uses_logbook,
                                                     expect_raises, logbook):
    kwargs = {
        "parent": parent,
        "activities": activities,
        "server_url": server_url,
        "rbac_token": rbac_token,
    }
    if uses_logbook:
        kwargs["logbook"] = logbook
    if expect_raises:
        with pytest.raises(ValueError, match='"logbook" argument is mutually exclusive with "server_url" or "rbac_token"'):
            _ = LogbookModel(**kwargs)
    else:
        _ = LogbookModel(**kwargs)


@pytest.mark.parametrize("rbac_token", ["", "abc123"])
@pytest.mark.parametrize("parent", [None, QObject()])
@pytest.mark.parametrize("activities", [None, "TEST1", ("TEST1", "TEST2")])
def test_init_activities_applied_do_not_fire_signal(rbac_token, parent, activities, logbook, qtbot: QtBot):
    client, _ = logbook
    client.rbac_b64_token = rbac_token
    with mock.patch("accwidgets.screenshot._model.LogbookModel._flush_activities_cache") as mocked_method:
        model = LogbookModel(parent=parent,
                             activities=activities,
                             logbook=logbook)
        kwargs = mocked_method.call_args[1]
    # We can't wait for signal of the object that has not been yet created. Therefore, we mock the expected call
    # and call it manually later, setting up the expectation for signals
    with qtbot.wait_signal(model.activities_changed, raising=False, timeout=100) as blocker:
        model._flush_activities_cache(**kwargs)
    assert not blocker.signal_triggered


@pytest.mark.parametrize("token,expect_fires,another_token,expect_fires2", [
    ("", False, "", False),
    ("abc123", True, "", True),
    ("", False, "abc123", True),
    ("abc123", True, "abc123", False),
    ("abc123", True, "cde567", True),
])
def test_reset_rbac_token_fires_signal(logbook, qtbot: QtBot, token, another_token, expect_fires, expect_fires2):
    model = LogbookModel(logbook=logbook)
    with qtbot.wait_signal(model.rbac_token_changed, timeout=100, raising=False) as blocker:
        model.reset_rbac_token(token)
    assert blocker.signal_triggered == expect_fires
    with qtbot.wait_signal(model.rbac_token_changed, timeout=100, raising=False) as blocker:
        model.reset_rbac_token(another_token)
    assert blocker.signal_triggered == expect_fires2


@pytest.mark.parametrize("token_val,expected_token", [
    (None, ""),
    ("", ""),
    ("abc123", "abc123"),
])
def test_reset_rbac_token_sets_client_token(logbook, token_val, expected_token):
    client, _ = logbook
    model = LogbookModel(logbook=logbook)
    assert str(client.rbac_b64_token) == ""
    model.reset_rbac_token(make_token(token_val))
    assert str(client.rbac_b64_token) == expected_token


@pytest.mark.parametrize("initial_activities,new_activities,new_rbac_token,expected_activities,expect_signal", [
    ("", "", "", "", False),
    ("", "", "abc123", "", False),
    ("", "TEST1", "", "", False),
    ("", "TEST1", "abc123", "TEST1", True),
    ("TEST1", "", "", "TEST1", False),
    ("TEST1", "", "abc123", "", True),
    ("TEST1", "TEST1", "", "TEST1", False),
    ("TEST1", "TEST1", "abc123", "TEST1", False),
    ("TEST1", "TEST2", "", "TEST1", False),
    ("TEST1", "TEST2", "abc123", "TEST2", True),
])
def test_reset_rbac_token_reapplies_activities(initial_activities, new_activities, new_rbac_token, expected_activities,
                                               logbook, expect_signal, qtbot: QtBot):
    client, activities_client = logbook
    activities_client.activities = initial_activities
    client.rbac_b64_token = "abc123"
    model = LogbookModel(logbook=logbook)
    assert model.logbook_activities == initial_activities
    client.rbac_b64_token = ""
    model.logbook_activities = new_activities
    assert model.logbook_activities == initial_activities
    with qtbot.wait_signal(model.activities_changed, raising=False, timeout=100) as blocker:
        model.reset_rbac_token(new_rbac_token)
    assert blocker.signal_triggered == expect_signal
    assert model.logbook_activities == expected_activities


@pytest.mark.parametrize("val", [
    "",
    "TEST1",
    ("TEST1", "TEST2"),
    ["TEST1", "TEST2"],
    NamedActivity.LHC,
    (NamedActivity.LHC, NamedActivity.ELENA),
    [NamedActivity.LHC, NamedActivity.ELENA],
])
def test_logbook_activities_prop(val, logbook):
    client, activities_client = logbook
    client.rbac_b64_token = "abc123"
    model = LogbookModel(logbook=logbook)
    assert model.logbook_activities == ()
    model.logbook_activities = val
    assert model.logbook_activities == val
    # Test resetting from previously set value
    model.logbook_activities = ("TEST3",)
    assert model.logbook_activities == ("TEST3",)


@pytest.mark.parametrize("token,val,expect_applied,expect_signal", [
    ("", "", False, False),
    ("", (), False, False),
    ("", "TEST1", False, False),
    ("", ("TEST1", "TEST2"), False, False),
    ("", ["TEST1", "TEST2"], False, False),
    ("", NamedActivity.LHC, False, False),
    ("", (NamedActivity.LHC, NamedActivity.ELENA), False, False),
    ("", [NamedActivity.LHC, NamedActivity.ELENA], False, False),
    ("abc123", "", True, True),
    ("abc123", (), True, False),
    ("abc123", "TEST1", True, True),
    ("abc123", ("TEST1", "TEST2"), True, True),
    ("abc123", ["TEST1", "TEST2"], True, True),
    ("abc123", NamedActivity.LHC, True, True),
    ("abc123", (NamedActivity.LHC, NamedActivity.ELENA), True, True),
    ("abc123", [NamedActivity.LHC, NamedActivity.ELENA], True, True),
])
def test_logbook_activities_applies_only_with_rbac_token(val, token, logbook, expect_applied, expect_signal, qtbot: QtBot):
    client, activities_client = logbook
    client.rbac_b64_token = token
    model = LogbookModel(logbook=logbook)
    assert model.logbook_activities == ()
    with qtbot.wait_signal(model.activities_changed, raising=False, timeout=100) as blocker:
        model.logbook_activities = val
    assert blocker.signal_triggered == expect_signal
    if expect_applied:
        assert model.logbook_activities == val
    else:
        assert model.logbook_activities == ()


@pytest.mark.asyncio
@pytest.mark.parametrize("message", ["", "Test message"])
async def test_create_logbook_event_succeeds(logbook, message):
    _, activities_client = logbook
    model = LogbookModel(logbook=logbook)
    activities_client.add_event.assert_not_called()
    res = await model.create_logbook_event(message)
    activities_client.add_event.assert_called_once_with(message)
    assert res == activities_client.add_event.return_value


@pytest.mark.asyncio
@pytest.mark.parametrize("message", ["", "Test message"])
async def test_create_logbook_event_fails(logbook, message):
    _, activities_client = logbook
    activities_client.add_event.side_effect = LogbookError("Test error", response=mock.MagicMock())
    model = LogbookModel(logbook=logbook)
    with pytest.raises(LogbookError, match="Test error"):
        await model.create_logbook_event(message)


@pytest.mark.asyncio
@pytest.mark.parametrize("event_id", [0, 1, 12552])
async def test_get_logbook_event_succeeds(logbook, event_id):
    client, _ = logbook
    model = LogbookModel(logbook=logbook)
    client.get_event.assert_not_called()
    res = await model.get_logbook_event(event_id)
    client.get_event.assert_called_once_with(event_id)
    assert res == client.get_event.return_value


@pytest.mark.asyncio
@pytest.mark.parametrize("event_id", [0, 1, 12552])
async def test_get_logbook_event_fails(logbook, event_id):
    client, _ = logbook
    client.get_event.side_effect = LogbookError("Test error", response=mock.MagicMock())
    model = LogbookModel(logbook=logbook)
    with pytest.raises(LogbookError, match="Test error"):
        await model.get_logbook_event(event_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("screenshot", [b"", b"\x01\x95\x0e\x1b"])
@pytest.mark.parametrize("seq,expected_filename", [
    (0, "capture_0.png"),
    (1, "capture_1.png"),
    (2, "capture_2.png"),
])
async def test_attach_screenshot_succeeds(logbook, screenshot, seq, expected_filename):
    model = LogbookModel(logbook=logbook)
    event = mock.MagicMock(spec=Event)
    event.attach_content.assert_not_called()
    await model.attach_screenshot(event=event, screenshot=screenshot, seq=seq)
    event.attach_content.assert_called_once_with(screenshot, "image/png", expected_filename)


@pytest.mark.asyncio
@pytest.mark.parametrize("screenshot", [b"", b"\x01\x95\x0e\x1b"])
@pytest.mark.parametrize("seq", [0, 1, 2])
async def test_attach_screenshot_fails(logbook, screenshot, seq):
    model = LogbookModel(logbook=logbook)
    event = mock.MagicMock(spec=Event)
    event.attach_content.side_effect = LogbookError("Test error", response=mock.MagicMock())
    with pytest.raises(LogbookError, match="Test error"):
        await model.attach_screenshot(event=event, screenshot=screenshot, seq=seq)


@freeze_time(STATIC_TIME)
@pytest.mark.asyncio
@pytest.mark.parametrize("past_days,max_events,returned_events,expected_start_date,expected_result", [
    (0, 0, [], {"year": 2020, "day": 1, "month": 1, "hour": 12, "minute": 30, "second": 55}, []),
    (1, 0, [], {"year": 2019, "day": 31, "month": 12, "hour": 12, "minute": 30, "second": 55}, []),
    (5, 0, [], {"year": 2019, "day": 27, "month": 12, "hour": 12, "minute": 30, "second": 55}, []),
    (0, 1, ["Ev1"], {"year": 2020, "day": 1, "month": 1, "hour": 12, "minute": 30, "second": 55}, ["Ev1"]),
    (1, 1, ["Ev1"], {"year": 2019, "day": 31, "month": 12, "hour": 12, "minute": 30, "second": 55}, ["Ev1"]),
    (5, 1, ["Ev1"], {"year": 2019, "day": 27, "month": 12, "hour": 12, "minute": 30, "second": 55}, ["Ev1"]),
    (0, 1, [], {"year": 2020, "day": 1, "month": 1, "hour": 12, "minute": 30, "second": 55}, []),
    (1, 1, [], {"year": 2019, "day": 31, "month": 12, "hour": 12, "minute": 30, "second": 55}, []),
    (5, 1, [], {"year": 2019, "day": 27, "month": 12, "hour": 12, "minute": 30, "second": 55}, []),
    (0, 10, ["Ev1", "Ev2"], {"year": 2020, "day": 1, "month": 1, "hour": 12, "minute": 30, "second": 55}, ["Ev1", "Ev2"]),
    (1, 10, ["Ev1", "Ev2"], {"year": 2019, "day": 31, "month": 12, "hour": 12, "minute": 30, "second": 55}, ["Ev1", "Ev2"]),
    (5, 10, ["Ev1", "Ev2"], {"year": 2019, "day": 27, "month": 12, "hour": 12, "minute": 30, "second": 55}, ["Ev1", "Ev2"]),
    (0, 10, [], {"year": 2020, "day": 1, "month": 1, "hour": 12, "minute": 30, "second": 55}, []),
    (1, 10, [], {"year": 2019, "day": 31, "month": 12, "hour": 12, "minute": 30, "second": 55}, []),
    (5, 10, [], {"year": 2019, "day": 27, "month": 12, "hour": 12, "minute": 30, "second": 55}, []),
])
async def test_get_logbook_events_succeeds(logbook, past_days, max_events, returned_events, expected_result,
                                           expected_start_date):
    _, activities_client = logbook
    remote_result = mock.MagicMock()
    remote_result.get_page.return_value = returned_events
    activities_client.get_events.return_value = remote_result
    model = LogbookModel(logbook=logbook)
    activities_client.get_events.assert_not_called()
    res = await model.get_logbook_events(past_days=past_days, max_events=max_events)
    activities_client.get_events.assert_called_once_with(from_date=datetime(**expected_start_date))
    remote_result.get_page.assert_called_once_with(0)
    assert res == expected_result


@pytest.mark.asyncio
async def test_get_logbook_events_fails(logbook):
    _, activities_client = logbook
    activities_client.get_events.side_effect = LogbookError("Test error", response=mock.MagicMock())
    model = LogbookModel(logbook=logbook)
    with pytest.raises(LogbookError, match="Test error"):
        await model.get_logbook_events(past_days=1, max_events=10)


@pytest.mark.parametrize("activities,token,expected_error", [
    (None, "", "RBAC login is required to write to the e-logbook"),
    ("", "", "RBAC login is required to write to the e-logbook"),
    (None, "abc123", "No e-logbook activity is defined"),
    ("", "abc123", "No e-logbook activity is defined"),
    ("TEST1", "abc123", None),
    (["TEST1", "TEST2"], "abc123", None),
    ("TEST1", "", "RBAC login is required to write to the e-logbook"),
    (["TEST1", "TEST2"], "", "RBAC login is required to write to the e-logbook"),
])
def test_validate(logbook, activities, token, expected_error):
    client, activities_client = logbook
    activities_client.activities = activities
    client.rbac_b64_token = token
    model = LogbookModel(activities=activities, logbook=logbook)

    if expected_error is None:
        model.validate()
    else:
        with pytest.raises(ValueError, match=expected_error):
            model.validate()


@mock.patch("accwidgets.screenshot._model.ThreadPoolExecutor")
def test_shuts_down_thread_pool_on_destruction(ThreadPoolExecutor):
    ThreadPoolExecutor.return_value.shutdown.assert_not_called()

    def scope():
        _ = LogbookModel(server_url="http://localhost:3000")
        ThreadPoolExecutor.return_value.shutdown.assert_not_called()

    scope()
    ThreadPoolExecutor.return_value.shutdown.assert_called_once()
