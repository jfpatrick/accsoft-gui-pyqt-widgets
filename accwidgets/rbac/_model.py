import copy
import functools
from base64 import b64decode
from typing import List, Union, Optional, Callable
from qtpy.QtCore import QObject, Signal, Slot, QTimer
from pyrbac import AuthenticationClient, AuthenticationError, AuthenticationListener, LoginServiceBuilder, Token
from ._token import RbaToken, RbaRole, is_rbac_role_critical
from ._role_picker import select_roles_interactively


class RbaButtonModel(QObject):

    login_succeeded = Signal(Token)
    """
    Fires when the login is successful, sending a newly obtained token.
    """

    login_failed = Signal(str, int)
    """
    Signal emitted when login fails. The first argument is error message, the second argument is login method value,
    that corresponds to the :class:`~accwidgets.rbac.RbaToken.LoginMethod` enum.
    """

    login_started = Signal(int)
    """
    Fires when the login has started, argument being the login method value, that corresponds to the
    :class:`~accwidgets.rbac.RbaToken.LoginMethod` enum.
    """

    login_finished = Signal()
    """Fires when the login has been finished, no matter the outcome."""

    logout_finished = Signal()
    """Fires when the logout has been finished."""

    token_expired = Signal(Token)
    """
    Notifies that a token has been expired, providing old raw :mod:`pyrbac` token.

    .. note:: This signal fires only when the auto-renewable token expires. It will not fire if the expiring token
              is a one-time token (produced when selecting custom roles) or a token that was received from the
              outside via :meth:`update_token` call.
    """

    def __init__(self, parent: Optional[QObject] = None):
        """
        Model handles RBAC login and supporting operations via :mod:`pyrbac` implementation.

        Args:
            parent: Owning object.
        """

        super().__init__(parent)
        self._pyrbac_client = None
        self._token: Optional[RbaToken] = None
        self._login_service: Optional[RbaAuthService] = None
        # pyrbac does not present a nice way to receive roles list,
        # therefore we must store it in an instance var temporarily
        self._callback_role_storage: Optional[List[str]] = None

    def logout(self):
        """
        Perform logout.

        This method emits a :attr:`logout_finished` signal in the end.
        """
        if self._login_service is not None:
            self._login_service.login_failed.disconnect(self.login_failed)
            self._login_service.login_failed.disconnect(self.login_finished)
            self._login_service.login_succeeded.disconnect(self._token_obtained)
            self._login_service.login_succeeded.disconnect(self.login_finished)
            self._login_service.token_expired.disconnect(self.token_expired)
            self._login_service.deleteLater()
            self._login_service = None
        elif self._token is None:
            return  # Was logged out before, no need to fire a signal again
        self._token = None
        self.logout_finished.emit()

    def login_by_location(self, interactively_select_roles: bool):
        """
        Slot to perform login by location when no roles have been previously selected (normally when doing regular
        login and not repeated one after picking roles in the dialog).

        Args:
            interactively_select_roles: :obj:`True` if roles should be selected by the user via interactive Role
                                        Picker dialog. Otherwise default roles will be provided.
        """
        if interactively_select_roles:
            self._single_shot_login(login_method=RbaToken.LoginMethod.LOCATION,
                                    login_func=self._client.login_location,
                                    login_callback=functools.partial(self._login_callback,
                                                                     select_roles=True))
        else:
            self._renewable_login(login_method=RbaToken.LoginMethod.LOCATION)

    def login_by_location_with_roles(self, preselected_roles: List[str]):
        """
        Slot to perform login by location with roles received previously (presumably from the roles picker dialog).

        Args:
            preselected_roles: Roles that have been previously selected in the role picker.
        """
        self._single_shot_login(login_method=RbaToken.LoginMethod.LOCATION,
                                login_func=self._client.login_location,
                                login_callback=functools.partial(self._login_callback,
                                                                 select_roles=preselected_roles))

    def login_explicitly(self, username: str, password: str, interactively_select_roles: bool):
        """
        Slot to perform explicit login when no roles have been previously selected (normally when doing regular
        login and not repeated one after picking roles in the dialog).

        Args:
            username: Supplied username.
            password: Entered password.
            interactively_select_roles: :obj:`True` if roles should be selected by the user via interactive Role
                                        Picker dialog. Otherwise default roles will be provided.
        """
        if interactively_select_roles:
            self._single_shot_login(username, password,
                                    login_method=RbaToken.LoginMethod.EXPLICIT,
                                    login_func=self._client.login_explicit,
                                    login_callback=functools.partial(self._login_callback,
                                                                     select_roles=True))
        else:
            self._renewable_login(username, password,
                                  login_method=RbaToken.LoginMethod.EXPLICIT)

    def login_explicitly_with_roles(self, username: str, password: str, preselected_roles: List[str]):
        """
        Slot to perform explicit login with roles received previously (presumably from the roles picker dialog).

        Args:
            username: Supplied username.
            password: Entered password.
            preselected_roles: Roles that have been previously selected in the role picker.
        """
        self._single_shot_login(username, password,
                                login_method=RbaToken.LoginMethod.EXPLICIT,
                                login_func=self._client.login_explicit,
                                login_callback=functools.partial(self._login_callback,
                                                                 select_roles=preselected_roles))

    # TODO: Uncomment when adding kerberos support
    # def login_by_kerberos(self, interactively_select_roles: bool):
    #     """
    #     Slot to perform Kerberos login when no roles have been previously selected (normally when doing regular
    #     login and not repeated one after picking roles in the dialog).
    #
    #     Args:
    #         interactively_select_roles: ``True`` if roles should be selected by the user via interactive Role
    #                                     Picker dialog. Otherwise default roles will be provided.
    #     """
    #     if interactively_select_roles:
    #         self._single_shot_login(username, password,
    #                                 login_approach=RbaToken.LoginMethod.KERBEROS,
    #                                 login_func=self._client.login_kerberos,
    #                                 login_callback=functools.partial(self._login_callback,
    #                                                                  select_roles=True))
    #     else:
    #         self._renewable_login(login_method=RbaToken.LoginMethod.KERBEROS)
    #
    # def login_by_kerberos_with_roles(self, preselected_roles: List[str]):
    #     """
    #     Slot to perform Kerberos login with roles received previously (presumably from the roles picker dialog).
    #
    #     Args:
    #         preselected_roles: Roles that have been previously selected in the role picker.
    #     """
    #     self._single_shot_login(username, password,
    #                             login_approach=RbaToken.LoginMethod.KERBEROS,
    #                             login_func=self._client.login_kerberos,
    #                             login_callback=functools.partial(self._login_callback,
    #                                                              select_roles=preselected_roles))

    @property
    def token(self) -> Optional[RbaToken]:
        """
        Token that has been obtained either by authenticating using this model object, or by injecting an external
        token via :meth:`update_token` method. The returned object is a wrapper over raw :class:`pyrbac.Token`. To
        access the raw token, use :meth:`~accwidgets.rbac.RbaToken.get_encoded`.
        """
        return self._token

    @Slot(Token)
    @Slot(RbaToken)
    @Slot(bytes)
    @Slot(str)
    def update_token(self, new_token: Union[Token, RbaToken, bytes, str]):
        """
        Slot to update token, if authentication was handled by the user code, outside of this model.

        This can be very useful to synchronize widget state, when the login is done in Java RBAC, e.g. when using
        Java-based libraries, such as :mod:`pyjapc` or :mod:`pjlsa`.

        This can also be used to copy a token from one model to another (with type :class:`RbaToken` returned by
        :attr:`token`).

        This method emits :attr:`login_succeeded` signal.

        .. note:: When injecting external token (unless it is :class:`RbaToken`), you will lose certain features,
                  such as proper roles display. Available roles are usually only provided temporarily during login
                  process, when specifically requested, and it is not possible to derive a complete set of roles
                  from the existing token.

        Args:
            new_token: New token, as object or in serialized form.

                       * When type is :class:`RbaToken`, presumably generated by another :class:`RbaButtonModel`
                         instance, its copy is stored by this model.
                       * When type is :class:`~pyrbac.Token`, this is the direct object, presumably generated by
                         :mod:`pyrbac` in another part of the application.
                       * :obj:`bytes` is an array of bytes of the encoded token, similar to what
                         :meth:`~pyrbac.Token.get_encoded` returns, or similar routine in the Java library.
                       * :obj:`str`, is expected to be base64-encoded serialized array of bytes, for instance,
                         produced by :meth:`pyjapc.PyJapc.rbacGetSerializedToken`.
        """
        if isinstance(new_token, RbaToken):
            if not new_token.auto_renewable and self._login_service is not None:
                self.logout()
            self._token = copy.copy(new_token)
            self.login_succeeded.emit(new_token._token)
        else:
            if isinstance(new_token, str):
                try:
                    new_token = b64decode(new_token)
                except Exception as e:  # noqa: B902
                    raise ValueError(f"Failed to decode base64-encoded token: {e!s}") from e
            if isinstance(new_token, bytes):
                try:
                    new_token = Token(new_token)  # FIXME: This needs a more precices try-catch when pyrbac implements proper exceptions https://issues.cern.ch/browse/RBAC-958
                except Exception as e:  # noqa: B902
                    raise ValueError(f"Failed to instantiate RBAC token: {e!s}") from e
            if not isinstance(new_token, Token):
                raise ValueError(f"Unsupported Token type: {type(new_token).__name__}")

            if self._login_service is not None:
                self.logout()

            self._token = RbaToken(login_method=RbaToken.LoginMethod.UNKNOWN,
                                   original_token=new_token,
                                   auto_renewable=False,
                                   available_roles=new_token.get_roles())  # FIXME: This is not good for "Select roles", need pyrbac API to access all available roles
            self.login_succeeded.emit(new_token)
        self.login_finished.emit()

    def _login_callback(self,
                        roles_available: List[str],
                        select_roles: Union[bool, List[str], None]) -> List[str]:
        self._callback_role_storage = roles_available
        if select_roles is True:
            # Default login without explicit roles. Select all non-critical roles.
            role_objects = [RbaRole(name=r, active=not is_rbac_role_critical(r)) for r in roles_available]
            roles_selected = select_roles_interactively(roles=role_objects, parent=self.parent())
        elif isinstance(select_roles, list):
            roles_selected = select_roles
        else:
            # Default login without explicit roles. Select all non-critical roles.
            roles_selected = [r for r in roles_available if not is_rbac_role_critical(r)]
        return roles_selected

    def _single_shot_login(self,
                           *login_args,
                           login_method: RbaToken.LoginMethod,
                           login_func: Callable,
                           login_callback: Callable[[List[str]], List[str]]):
        self.login_started.emit(login_method.value)

        # Move execution to the end of the event loop, to allow login_started have effect on the UI (and display activity indicators)
        callback = functools.partial(self._deferred_single_shot_login,
                                     *login_args,
                                     login_method=login_method,
                                     login_func=login_func,
                                     login_callback=login_callback)
        QTimer.singleShot(0, callback)

    def _deferred_single_shot_login(self,
                                    *login_args,
                                    login_method: RbaToken.LoginMethod,
                                    login_func: Callable,
                                    login_callback: Callable[[List[str]], List[str]]):
        # This will be populated in pyrbac callback. We store it only for the duration of this call,
        # and then clean it.
        self._callback_role_storage = None
        try:
            pyrbac_token: Token = login_func(*login_args, login_callback)
        except AuthenticationError as e:
            self.login_failed.emit(str(e), login_method.value)
        else:
            retrieved_available_roles = self._callback_role_storage
            if pyrbac_token and retrieved_available_roles is not None:
                self._token_obtained(token=pyrbac_token,
                                     login_method=login_method,
                                     auto_renewable=False,
                                     available_roles=retrieved_available_roles)
            else:
                self.login_failed.emit("Failed to obtain RBAC token", login_method.value)
        finally:
            self._callback_role_storage = None
            self.login_finished.emit()

    def _renewable_login(self, *login_args, login_method: RbaToken.LoginMethod):
        if self._login_service is not None:
            self.logout()
        self.login_started.emit(login_method.value)
        login_service = RbaAuthService(self)
        login_service.login_failed.connect(self.login_failed)
        login_service.login_failed.connect(self.login_finished)
        login_service.login_succeeded.connect(self._token_obtained)
        login_service.login_succeeded.connect(self.login_finished)
        login_service.token_expired.connect(self.token_expired)
        self._login_service = login_service
        login_service.login(*login_args, login_method=login_method)

    def _token_obtained(self,
                        token: Token,
                        login_method: RbaToken.LoginMethod,
                        auto_renewable: bool = True,  # Default for slot from LoginService, which is auto-renewable by definition
                        available_roles: Optional[List[str]] = None):
        final_token = RbaToken(login_method=login_method,
                               original_token=token,
                               auto_renewable=auto_renewable,
                               available_roles=available_roles)
        # TODO: This is a workaround until pyrbac implements proper roles retrieval
        final_token._roles_can_be_trusted = available_roles is not None
        self._token = final_token
        self.login_succeeded.emit(token)

    @property
    def _client(self):
        """Lazy creation of the client (used to be delayed to delay public key intialization."""
        if self._pyrbac_client is None:
            self._pyrbac_client = AuthenticationClient.create()
        return self._pyrbac_client


class RbaAuthListener(AuthenticationListener):
    # Cannot join this with RbaAuthService, because of the metaclass conflict with Qt

    def __init__(self,
                 login_method: RbaToken.LoginMethod,
                 on_done: Callable[[Token, int], None],
                 on_error: Callable[[str, int], None],
                 on_expired: Callable[[Token], None]):
        super().__init__()
        self._login_method = login_method
        self._on_done = on_done
        self._on_error = on_error
        self._on_expired = on_expired

    def authenticationDone(self, new_token: Token):
        self._on_done(new_token, self._login_method.value)

    def authenticationError(self, authentication_error: AuthenticationError):
        self._on_error(str(authentication_error), self._login_method.value)

    def tokenExpired(self, old_token: Token):
        self._on_expired(old_token)


class RbaAuthService(QObject):

    login_succeeded = Signal(Token, int)
    login_failed = Signal(str, int)
    token_expired = Signal(Token)

    def login(self, *login_args, login_method: RbaToken.LoginMethod):
        # This is specifically a separate method to allow to connect signals before performing the login
        login_builder: LoginServiceBuilder = LoginServiceBuilder.create()

        listener = RbaAuthListener(login_method=login_method,
                                   on_done=self.login_succeeded.emit,
                                   on_error=self.login_failed.emit,
                                   on_expired=self.token_expired.emit)
        login_builder.listener(listener)

        if login_method == RbaToken.LoginMethod.EXPLICIT:
            service = login_builder.build_explicit(*login_args)
        elif login_method == RbaToken.LoginMethod.LOCATION:
            service = login_builder.build_location()
        # TODO: Uncomment when adding kerberos support
        # elif login_method == RbaToken.LoginMethod.KERBEROS:
        #     service = login_builder.build_kerberos()
        else:
            raise TypeError(f"Unsupported login type: {login_method}")
        self.listener = listener
        self.service = service
