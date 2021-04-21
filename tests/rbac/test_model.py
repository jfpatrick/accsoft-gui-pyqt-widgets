import pytest
import base64
from unittest import mock
from pytestqt.qtbot import QtBot
from pyrbac import Token, AuthenticationError
from qtpy.QtCore import QObject, Signal, Qt
from accwidgets.rbac import RbaButtonModel, RbaToken
from accwidgets.rbac._model import RbaAuthService, RbaAuthListener


def test_model_default_token():
    model = RbaButtonModel()
    assert model.token is None


@pytest.mark.parametrize("token_auto_renewable", [True, False])
def test_model_logout_only_once(qtbot: QtBot, token_auto_renewable):
    model = RbaButtonModel()
    model._token = mock.MagicMock()
    if token_auto_renewable:
        model._login_service = mock.MagicMock()
    else:
        assert model._login_service is None
    assert model.token is not None
    with qtbot.wait_signal(model.logout_finished):
        model.logout()
    assert model.token is None
    assert model._login_service is None
    for _ in range(3):
        with qtbot.wait_signal(model.logout_finished, raising=False, timeout=100) as blocker:
            model.logout()
        assert not blocker.signal_triggered
        assert model.token is None
        assert model._login_service is None


def test_model_logout_disconnects_service():
    model = RbaButtonModel()
    model._token = mock.MagicMock()
    login_service = RbaAuthService()
    model._login_service = login_service
    login_service.login_failed.connect(model.login_failed)
    login_service.login_failed.connect(model.login_finished)
    login_service.login_succeeded.connect(model._token_obtained)
    login_service.login_succeeded.connect(model.login_finished)
    login_service.token_expired.connect(model.token_expired)
    assert login_service.receivers(login_service.login_failed) == 2
    assert login_service.receivers(login_service.login_succeeded) == 2
    assert login_service.receivers(login_service.token_expired) == 1
    with mock.patch.object(login_service, "deleteLater") as deleteLater:
        model.logout()
        deleteLater.assert_called_once()
    assert model._login_service is None
    assert login_service.receivers(login_service.login_failed) == 0
    assert login_service.receivers(login_service.login_succeeded) == 0
    assert login_service.receivers(login_service.token_expired) == 0


@pytest.mark.parametrize("login_method,kwargs,expected_login_method", [
    ("login_by_location", {}, RbaToken.LoginMethod.LOCATION),
    ("login_explicitly", {"username": "test_user", "password": "test_password"}, RbaToken.LoginMethod.EXPLICIT),
])
@mock.patch("accwidgets.rbac._model.RbaAuthService.login", autospec=True)
def test_model_non_interactive_login_succeeds(login, qtbot: QtBot, login_method, kwargs, expected_login_method):

    returned_token = Token.create_empty_token()

    def side_effect(obj: RbaAuthService, *_, login_method: RbaToken.LoginMethod):
        obj.login_succeeded.emit(returned_token, login_method.value)

    login.side_effect = side_effect
    model = RbaButtonModel()
    with qtbot.wait_signals([model.login_started, model.login_finished, model.login_succeeded]) as blocker:
        getattr(model, login_method)(**kwargs, interactively_select_roles=False)
    for sig_args in blocker.all_signals_and_args:
        if sig_args.signal_name.startswith("login_succeeded"):
            assert sig_args.args == (returned_token,)
        elif sig_args.signal_name.startswith("login_started"):
            assert sig_args.args == (expected_login_method.value,)


@pytest.mark.parametrize("login_method,kwargs,expected_login_method", [
    ("login_by_location", {}, RbaToken.LoginMethod.LOCATION),
    ("login_explicitly", {"username": "test_user", "password": "test_password"}, RbaToken.LoginMethod.EXPLICIT),
])
@mock.patch("accwidgets.rbac._model.RbaAuthService.login", autospec=True)
def test_model_non_interactive_login_fails(login, qtbot: QtBot, login_method, kwargs, expected_login_method):

    def side_effect(obj: RbaAuthService, *_, login_method: RbaToken.LoginMethod):
        obj.login_failed.emit("Test error", login_method.value)

    login.side_effect = side_effect
    model = RbaButtonModel()
    with qtbot.wait_signals([model.login_started, model.login_finished, model.login_failed]) as blocker:
        getattr(model, login_method)(**kwargs, interactively_select_roles=False)
    for sig_args in blocker.all_signals_and_args:
        if sig_args.signal_name.startswith("login_failed"):
            assert sig_args.args == ("Test error", expected_login_method.value)
        elif sig_args.signal_name.startswith("login_started"):
            assert sig_args.args == (expected_login_method.value,)


@pytest.mark.parametrize("login_method,kwargs,pyrbac_mocked_method,expected_login_method", [
    ("login_by_location", {}, "login_location", RbaToken.LoginMethod.LOCATION),
    ("login_explicitly", {"username": "test_user", "password": "test_password"}, "login_explicit", RbaToken.LoginMethod.EXPLICIT),
])
@mock.patch("accwidgets.rbac._model.select_roles_interactively", return_value=["Role1", "MCS-Role3"])
def test_model_interactive_login_succeeds(select_roles_interactively, qtbot: QtBot, login_method, kwargs,
                                          pyrbac_mocked_method, expected_login_method):
    returned_token = Token.create_empty_token()
    model = RbaButtonModel()

    def side_effect(*args):
        login_callback = args[-1]
        select_roles_interactively.assert_not_called()
        selected_roles = login_callback(["Role1", "Role2", "MCS-Role3"])
        select_roles_interactively.assert_called_once()
        assert selected_roles == ["Role1", "MCS-Role3"]
        return returned_token

    with mock.patch(f"accwidgets.rbac._model.AuthenticationClient.{pyrbac_mocked_method}", side_effect=side_effect):
        with qtbot.wait_signals([model.login_started, model.login_finished, model.login_succeeded]) as blocker:
            getattr(model, login_method)(**kwargs, interactively_select_roles=True)
        for sig_args in blocker.all_signals_and_args:
            if sig_args.signal_name.startswith("login_succeeded"):
                assert sig_args.args == (returned_token,)
            elif sig_args.signal_name.startswith("login_started"):
                assert sig_args.args == (expected_login_method.value,)


@pytest.mark.parametrize("login_method,kwargs,pyrbac_mocked_method,expected_login_method", [
    ("login_by_location", {}, "login_location", RbaToken.LoginMethod.LOCATION),
    ("login_explicitly", {"username": "test_user", "password": "test_password"}, "login_explicit", RbaToken.LoginMethod.EXPLICIT),
])
@mock.patch("accwidgets.rbac._model.select_roles_interactively", return_value=["Role1", "MCS-Role3"])
def test_model_interactive_login_fails(select_roles_interactively, qtbot: QtBot, login_method, kwargs,
                                       expected_login_method, pyrbac_mocked_method):
    model = RbaButtonModel()

    def side_effect(*args):
        login_callback = args[-1]
        select_roles_interactively.assert_not_called()
        selected_roles = login_callback(["Role1", "Role2", "MCS-Role3"])
        select_roles_interactively.assert_called_once()
        assert selected_roles == ["Role1", "MCS-Role3"]
        raise AuthenticationError("Test error")

    with mock.patch(f"accwidgets.rbac._model.AuthenticationClient.{pyrbac_mocked_method}", side_effect=side_effect):
        with qtbot.wait_signals([model.login_started, model.login_finished, model.login_failed]) as blocker:
            getattr(model, login_method)(**kwargs, interactively_select_roles=True)
        for sig_args in blocker.all_signals_and_args:
            if sig_args.signal_name.startswith("login_failed"):
                assert sig_args.args == ("Test error", expected_login_method.value)
            elif sig_args.signal_name.startswith("login_started"):
                assert sig_args.args == (expected_login_method.value,)


@pytest.mark.parametrize("login_method,kwargs,pyrbac_mocked_method,expected_login_method", [
    ("login_by_location_with_roles", {}, "login_location", RbaToken.LoginMethod.LOCATION),
    ("login_explicitly_with_roles", {"username": "test_user", "password": "test_password"}, "login_explicit", RbaToken.LoginMethod.EXPLICIT),
])
@mock.patch("accwidgets.rbac._model.select_roles_interactively")
def test_model_preselected_login_succeeds(select_roles_interactively, qtbot: QtBot, login_method, kwargs,
                                          pyrbac_mocked_method, expected_login_method):
    returned_token = Token.create_empty_token()
    model = RbaButtonModel()

    def side_effect(*args):
        login_callback = args[-1]
        select_roles_interactively.assert_not_called()
        selected_roles = login_callback(["Role1", "Role2", "MCS-Role3"])
        select_roles_interactively.assert_not_called()
        assert selected_roles == ["Role1", "MCS-Role3"]
        return returned_token

    with mock.patch(f"accwidgets.rbac._model.AuthenticationClient.{pyrbac_mocked_method}", side_effect=side_effect):
        with qtbot.wait_signals([model.login_started, model.login_finished, model.login_succeeded]) as blocker:
            getattr(model, login_method)(**kwargs, preselected_roles=["Role1", "MCS-Role3"])
        for sig_args in blocker.all_signals_and_args:
            if sig_args.signal_name.startswith("login_succeeded"):
                assert sig_args.args == (returned_token,)
            elif sig_args.signal_name.startswith("login_started"):
                assert sig_args.args == (expected_login_method.value,)


@pytest.mark.parametrize("login_method,kwargs,pyrbac_mocked_method,expected_login_method", [
    ("login_by_location_with_roles", {}, "login_location", RbaToken.LoginMethod.LOCATION),
    ("login_explicitly_with_roles", {"username": "test_user", "password": "test_password"}, "login_explicit", RbaToken.LoginMethod.EXPLICIT),
])
@mock.patch("accwidgets.rbac._model.select_roles_interactively")
def test_model_preselected_login_fails(select_roles_interactively, qtbot: QtBot, login_method, kwargs,
                                       expected_login_method, pyrbac_mocked_method):
    model = RbaButtonModel()

    def side_effect(*args):
        login_callback = args[-1]
        select_roles_interactively.assert_not_called()
        selected_roles = login_callback(["Role1", "Role2", "MCS-Role3"])
        select_roles_interactively.assert_not_called()
        assert selected_roles == ["Role1", "MCS-Role3"]
        raise AuthenticationError("Test error")

    with mock.patch(f"accwidgets.rbac._model.AuthenticationClient.{pyrbac_mocked_method}", side_effect=side_effect):
        with qtbot.wait_signals([model.login_started, model.login_finished, model.login_failed]) as blocker:
            getattr(model, login_method)(**kwargs, preselected_roles=["Role1", "MCS-Role3"])
        for sig_args in blocker.all_signals_and_args:
            if sig_args.signal_name.startswith("login_failed"):
                assert sig_args.args == ("Test error", expected_login_method.value)
            elif sig_args.signal_name.startswith("login_started"):
                assert sig_args.args == (expected_login_method.value,)


def test_model_several_logins_allowed(qtbot: QtBot):
    returned_token = Token.create_empty_token()
    model = RbaButtonModel()

    def side_effect(*args):
        login_callback = args[-1]
        login_callback(["Role1", "Role2", "MCS-Role3"])
        return returned_token

    with mock.patch(f"accwidgets.rbac._model.AuthenticationClient.login_location", side_effect=side_effect):
        assert model.token is None
        with qtbot.wait_signals([model.login_started, model.login_finished, model.login_succeeded]):
            model.login_by_location_with_roles(preselected_roles=[])
        assert model.token is not None
        for _ in range(3):
            with qtbot.wait_signals([model.login_started, model.login_finished, model.login_succeeded]):
                model.login_by_location_with_roles(preselected_roles=[])
            assert model.token is not None


@pytest.mark.parametrize("method,kwargs,pyrbac_mocked_method,expected_login_method", [
    ("login_by_location_with_roles", {"preselected_roles": []}, "login_location", RbaToken.LoginMethod.LOCATION),
    ("login_explicitly_with_roles", {"username": "test_username", "password": "test_password", "preselected_roles": []}, "login_explicit", RbaToken.LoginMethod.EXPLICIT),
    ("login_by_location", {"interactively_select_roles": True}, "login_location", RbaToken.LoginMethod.LOCATION),
    ("login_explicitly", {"username": "test_username", "password": "test_password", "interactively_select_roles": True}, "login_explicit", RbaToken.LoginMethod.EXPLICIT),
])
def test_model_login_fails_when_no_role_callback_is_given(qtbot: QtBot, pyrbac_mocked_method, method, kwargs,
                                                          expected_login_method):
    returned_token = Token.create_empty_token()
    model = RbaButtonModel()

    # Should fail because mocked method returns a token, but does not call the login_callback, which saves the
    # available roles
    with mock.patch(f"accwidgets.rbac._model.AuthenticationClient.{pyrbac_mocked_method}", return_value=returned_token):
        assert model.token is None
        with qtbot.wait_signals([model.login_started, model.login_finished, model.login_failed]) as blocker:
            getattr(model, method)(**kwargs)
        assert model.token is None
        for sig_args in blocker.all_signals_and_args:
            if sig_args.signal_name.startswith("login_failed"):
                assert sig_args.args == ("Failed to obtain RBAC token", expected_login_method.value)


static_token = Token.create_empty_token()


@pytest.mark.parametrize("input,expected_encoded,expected_login_method,expected_auto_renewable", [
    (static_token, static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (static_token.get_encoded(), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (base64.b64encode(static_token.get_encoded()).decode("utf-8"), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.UNKNOWN), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.UNKNOWN), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, True),
    (RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.EXPLICIT), static_token.get_encoded(), RbaToken.LoginMethod.EXPLICIT, False),
    (RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.EXPLICIT), static_token.get_encoded(), RbaToken.LoginMethod.EXPLICIT, True),
    (RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.LOCATION), static_token.get_encoded(), RbaToken.LoginMethod.LOCATION, False),
    (RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.LOCATION), static_token.get_encoded(), RbaToken.LoginMethod.LOCATION, True),
])
def test_model_update_token_succeeds(qtbot: QtBot, input, expected_encoded, expected_auto_renewable, expected_login_method):
    model = RbaButtonModel()
    with qtbot.wait_signals([model.login_succeeded, model.login_finished]) as blocker:
        model.update_token(input)
    for sig_args in blocker.all_signals_and_args:
        if sig_args.signal_name.startswith("login_succeeded"):
            assert len(sig_args.args) == 1
            assert sig_args.args[0].get_encoded() == expected_encoded

    assert model.token is not None
    assert model.token.get_encoded() == expected_encoded
    assert model.token.login_method == expected_login_method
    assert model.token.auto_renewable == expected_auto_renewable


@pytest.mark.parametrize("input,expected_error", [
    ("abc", "Failed to decode base64-encoded token: Incorrect padding"),
    (2354, "Unsupported Token type: int"),
    (object(), "Unsupported Token type: object"),
    # (b"testtesttest", "sdgf")  # FIXME: Uncomment when fixed in pyrbac (now it dies with SEGFAULT instead of throwing exception), then we need to catch it
])
def test_model_update_token_fails(input, expected_error):
    model = RbaButtonModel()
    with pytest.raises(ValueError, match=expected_error):
        model.update_token(input)


@pytest.mark.parametrize("login_service_exists,input,expect_logout", [
    (True, static_token, True),
    (False, static_token, False),
    (True, static_token.get_encoded(), True),
    (False, static_token.get_encoded(), False),
    (True, base64.b64encode(static_token.get_encoded()).decode("utf-8"), True),
    (False, base64.b64encode(static_token.get_encoded()).decode("utf-8"), False),
    (True, RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.UNKNOWN), True),
    (False, RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.UNKNOWN), False),
    (True, RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.UNKNOWN), False),
    (False, RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.UNKNOWN), False),
    (True, RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.EXPLICIT), True),
    (False, RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.EXPLICIT), False),
    (True, RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.EXPLICIT), False),
    (False, RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.EXPLICIT), False),
    (True, RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.LOCATION), True),
    (False, RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.LOCATION), False),
    (True, RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.LOCATION), False),
    (False, RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.LOCATION), False),
])
def test_model_removes_login_service(qtbot: QtBot, login_service_exists, input, expect_logout):
    model = RbaButtonModel()
    if login_service_exists:
        model._login_service = mock.MagicMock()
    else:
        assert model._login_service is None
    with qtbot.wait_signal(model.logout_finished, raising=False, timeout=100) as blocker:
        model.update_token(input)
    blocker.signal_triggered == expect_logout
    if not login_service_exists or (expect_logout and login_service_exists):
        assert model._login_service is None
    else:
        assert model._login_service is not None


@pytest.mark.parametrize("input,expected_encoded,expected_login_method,expected_auto_renewable", [
    (static_token, static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (static_token.get_encoded(), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (base64.b64encode(static_token.get_encoded()).decode("utf-8"), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.UNKNOWN), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, False),
    (RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.UNKNOWN), static_token.get_encoded(), RbaToken.LoginMethod.UNKNOWN, True),
    (RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.EXPLICIT), static_token.get_encoded(), RbaToken.LoginMethod.EXPLICIT, False),
    (RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.EXPLICIT), static_token.get_encoded(), RbaToken.LoginMethod.EXPLICIT, True),
    (RbaToken(original_token=static_token, auto_renewable=False, login_method=RbaToken.LoginMethod.LOCATION), static_token.get_encoded(), RbaToken.LoginMethod.LOCATION, False),
    (RbaToken(original_token=static_token, auto_renewable=True, login_method=RbaToken.LoginMethod.LOCATION), static_token.get_encoded(), RbaToken.LoginMethod.LOCATION, True),
])
def test_model_update_slot(qtbot: QtBot, input, expected_encoded, expected_auto_renewable, expected_login_method):

    class Supplier(QObject):
        send_token = Signal("PyQt_PyObject")

    supplier = Supplier()
    model = RbaButtonModel()
    supplier.send_token.connect(model.update_token, Qt.QueuedConnection)

    with qtbot.wait_signals([model.login_succeeded, model.login_finished]) as blocker:
        supplier.send_token.emit(input)
    for sig_args in blocker.all_signals_and_args:
        if sig_args.signal_name.startswith("login_succeeded"):
            assert len(sig_args.args) == 1
            assert sig_args.args[0].get_encoded() == expected_encoded

    assert model.token is not None
    assert model.token.get_encoded() == expected_encoded
    assert model.token.login_method == expected_login_method
    assert model.token.auto_renewable == expected_auto_renewable


@pytest.mark.parametrize("login_method,kwargs", [
    ("login_by_location", {}),
    ("login_explicitly", {"username": "test_user", "password": "test_password"}),
])
@mock.patch("accwidgets.rbac._model.RbaAuthService.login", autospec=True)
def test_model_token_expiration(login, qtbot: QtBot, login_method, kwargs):

    returned_token = Token.create_empty_token()

    def side_effect(obj: RbaAuthService, *_, login_method: RbaToken.LoginMethod):
        obj.login_succeeded.emit(returned_token, login_method.value)

    login.side_effect = side_effect
    model = RbaButtonModel()
    getattr(model, login_method)(**kwargs, interactively_select_roles=False)
    with qtbot.wait_signal(model.token_expired) as blocker:
        assert model._login_service is not None
        model._login_service.token_expired.emit(returned_token)
    assert blocker.args == [returned_token]


@pytest.mark.parametrize("login_method,called_method,called_args,expected_signal,expected_args", [
    (RbaToken.LoginMethod.LOCATION, "authenticationDone", [static_token], "on_done", [static_token, RbaToken.LoginMethod.LOCATION.value]),
    (RbaToken.LoginMethod.EXPLICIT, "authenticationDone", [static_token], "on_done", [static_token, RbaToken.LoginMethod.EXPLICIT.value]),
    (RbaToken.LoginMethod.LOCATION, "authenticationError", [AuthenticationError("Test error")], "on_error", ["Test error", RbaToken.LoginMethod.LOCATION.value]),
    (RbaToken.LoginMethod.EXPLICIT, "authenticationError", [AuthenticationError("Test error")], "on_error", ["Test error", RbaToken.LoginMethod.EXPLICIT.value]),
    (RbaToken.LoginMethod.LOCATION, "tokenExpired", [static_token], "on_expired", [static_token]),
    (RbaToken.LoginMethod.EXPLICIT, "tokenExpired", [static_token], "on_expired", [static_token]),
])
def test_listener_forwards_callbacks(login_method, called_args, called_method, expected_args, expected_signal):

    callbacks = {
        "on_done": mock.Mock(),
        "on_error": mock.Mock(),
        "on_expired": mock.Mock(),
    }
    listener = RbaAuthListener(login_method=login_method, **callbacks)
    for cb in callbacks.values():
        cb.assert_not_called()
    getattr(listener, called_method)(*called_args)
    for name, cb in callbacks.items():
        if name == expected_signal:
            cb.assert_called_once_with(*expected_args)
        else:
            cb.assert_not_called()


@pytest.mark.parametrize("login_method,login_args,expected_builder_method", [
    (RbaToken.LoginMethod.EXPLICIT, ["test_username", "test_password"], "build_explicit"),
    (RbaToken.LoginMethod.LOCATION, [], "build_location"),
])
@mock.patch("accwidgets.rbac._model.LoginServiceBuilder")
def test_auth_service_succeeds(LoginServiceBuilder, login_method, login_args, expected_builder_method):
    known_methods = ["build_explicit", "build_location"]
    known_methods.remove(expected_builder_method)
    uncalled_method = known_methods[0]

    returned_service = mock.MagicMock()

    srv = RbaAuthService()
    LoginServiceBuilder.create.assert_not_called()
    getattr(LoginServiceBuilder.create.return_value, expected_builder_method).return_value = returned_service
    assert not hasattr(srv, "listener")
    assert not hasattr(srv, "service")
    srv.login(*login_args, login_method=login_method)
    LoginServiceBuilder.create.assert_called_once()
    LoginServiceBuilder.create.return_value.listener.assert_called_once()
    getattr(LoginServiceBuilder.create.return_value, expected_builder_method).assert_called_once_with(*login_args)
    getattr(LoginServiceBuilder.create.return_value, uncalled_method).assert_not_called()
    assert srv.service is returned_service
    assert isinstance(srv.listener, RbaAuthListener)


@pytest.mark.parametrize("login_args", [
    [],
    ["test_username", "test_password"],
])
@pytest.mark.parametrize("login_method,expected_error", [
    (RbaToken.LoginMethod.UNKNOWN, "Unsupported login type: 1"),
    ("abc", "Unsupported login type: abc"),
])
@mock.patch("accwidgets.rbac._model.LoginServiceBuilder")
def test_auth_service_fails(LoginServiceBuilder, login_method, login_args, expected_error):
    known_methods = ["build_explicit", "build_location"]

    srv = RbaAuthService()
    LoginServiceBuilder.create.assert_not_called()
    assert not hasattr(srv, "listener")
    assert not hasattr(srv, "service")
    with pytest.raises(TypeError, match=expected_error):
        srv.login(*login_args, login_method=login_method)
    LoginServiceBuilder.create.assert_called_once()
    LoginServiceBuilder.create.return_value.listener.assert_called_once()
    for name in known_methods:
        getattr(LoginServiceBuilder.create.return_value, name).assert_not_called()
    assert not hasattr(srv, "listener")
    assert not hasattr(srv, "service")

# pkey resolution is not tested here, because it gets imported once, and public key gets cached when creating
# AuthenticationClient instances (and even with importlib.reload(pyrbac) does not allow to break it later), presumably
# because it gets cached in C++ part and *.so is not reloaded by the system, when doing importlib.reload(). As a result,
# it is not possible to reliably trigger the error, when running tests in the random order (or having random order
# of pyrbac imports and instantiations).
