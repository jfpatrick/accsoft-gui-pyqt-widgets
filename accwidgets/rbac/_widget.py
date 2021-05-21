import warnings
from typing import Optional, List, cast, Union
from pathlib import Path
from qtpy.QtGui import QColor, QResizeEvent, QKeyEvent
from qtpy.QtWidgets import (QWidget, QToolButton, QMenu, QDialog, QVBoxLayout, QToolBar,
                            QWidgetAction, QSizePolicy, QHBoxLayout, QMessageBox)
from qtpy.QtCore import Qt, Slot, Signal, Property, QObjectCleanupHandler, QEvent, QSize
from pyrbac import Token
from accwidgets.qt import make_icon, OrientedToolButton
from ._palette import Color, ColorRole, Palette
from ._token import RbaToken
from ._role_picker import RbaRolePicker
from ._token_dialog import RbaTokenDialog
from ._rbac_dialog import RbaAuthDialog, RbaAuthPopupWidget
from ._model import RbaButtonModel


class RbaButton(QWidget):

    loginSucceeded = Signal(Token)
    """
    Fires when the login is successful, sending a newly obtained token.
    """

    loginFailed = Signal(str, int)
    """
    Signal emitted when login fails. The first argument is error message, the second argument is login method value,
    that corresponds to the :class:`~accwidgets.rbac.RbaToken.LoginMethod` enum.
    """

    logoutFinished = Signal()
    """Fires when the logout has been finished."""

    loginFinished = Signal()
    """Fires when the login has been finished, no matter the outcome."""

    tokenExpired = Signal(Token)
    """
    Notifies that a token has been expired, providing old raw :mod:`pyrbac` token.

    .. note:: This signal fires only when the auto-renewable token expires. It will not fire if the expiring token
              is a one-time token (produced when selecting custom roles) or a token that was received from the
              outside via :meth:`~accwidgets.rbac.RbaButtonModel.update_token` call.
    """

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 model: Optional[RbaButtonModel] = None):
        """
        Set of buttons that assist with authentication & authorization via RBAC.

        Args:
            parent: Parent widget to hold this object.
            model: Existing RBAC model.
        """
        self._color_palette = Palette()
        super().__init__(parent)
        self._auth_btn = RbaAuthButton(self)
        self._user_btn = RbaUserButton(self)

        # Create a layout, even if not added so far to anything. This can be handy when loading Qt Designer widgets,
        # since they do not initially react to ParentChange event.
        self._on_orientation_changed(Qt.Horizontal)

        self._model = model or RbaButtonModel(parent=self)
        self._connect_model(self._model)  # This will also decorate the widget according to the model state

    def _get_model(self) -> RbaButtonModel:
        return self._model

    def _set_model(self, new_val: RbaButtonModel):
        if new_val == self._model:
            return
        self._disconnect_model(self._model)
        self._model = new_val
        self._connect_model(new_val)

    model = property(fget=_get_model, fset=_set_model)
    """
    Model that handles interaction with :mod:`pyrbac` library.

    When assigning a new model, its ownership is transferred to the widget.
    """

    def _get_color_fg_mcs(self) -> QColor:
        return self._color_palette.color(ColorRole.MCS)

    def _set_color_fg_mcs(self, new_val: Color):
        self._color_palette.set_color(ColorRole.MCS, new_val)

    # Even though it's a single color property currently, it cannot be removed, because unlike other
    # places that have QLabels, which can be configured with dynamic properties, this color is given to the
    # table model, which does not have access to QLabels and cannot propagate any dynamic property information.
    mcsColor: Color = Property(QColor, fget=_get_color_fg_mcs, fset=_set_color_fg_mcs)
    """
    Font color for MSC roles in role picker. This property enables ability to restyle the widget with QSS.
    """

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.ParentAboutToChange:
            if isinstance(self.parent(), QToolBar):
                self._disconnect_toolbar(self.parent())
        res = super().event(event)
        if event.type() == QEvent.ParentChange:
            if isinstance(self.parent(), QToolBar):
                self._connect_toolbar(self.parent())
            else:
                # When not inside toolbar, always assume horizontal layout
                self._on_orientation_changed(Qt.Horizontal)
                self._auth_btn.set_margin_icon_size(self.size())
        return res

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if not isinstance(self.parent(), QToolBar):
            # Is supposed to have dynamic icon size
            # In contrast, when in toolbar, icon size is driven by QToolBar's iconSize
            self._auth_btn.set_margin_icon_size(event.size())

    def _connect_toolbar(self, toolbar: QToolBar):
        self._auth_btn.setIconSize(toolbar.iconSize())
        self._on_orientation_changed(toolbar.orientation())
        toolbar.iconSizeChanged.connect(self._auth_btn.setIconSize)
        toolbar.orientationChanged.connect(self._on_orientation_changed)

    def _disconnect_toolbar(self, toolbar: QToolBar):
        try:
            toolbar.iconSizeChanged.disconnect(self._auth_btn.setIconSize)
        except TypeError:
            pass
        try:
            toolbar.orientationChanged.disconnect(self._on_orientation_changed)
        except TypeError:
            pass

    def _connect_model(self, model: RbaButtonModel):
        model.logout_finished.connect(self._on_logout_finished)
        model.logout_finished.connect(self.logoutFinished)
        model.login_finished.connect(self.loginFinished)
        model.login_finished.connect(self._auth_btn.forward_login_finished)
        model.login_started.connect(self._auth_btn.forward_login_started)
        model.login_succeeded.connect(self._on_login_succeeded)
        model.login_succeeded.connect(self.loginSucceeded)
        model.login_succeeded.connect(self._auth_btn.forward_login_succeeded)
        model.login_failed.connect(self._auth_btn.forward_login_error)
        model.login_failed.connect(self.loginFailed)
        model.token_expired.connect(self.tokenExpired)
        model.setParent(self)
        if model.token is None:
            self._on_logout_finished()
        else:
            self._on_login_succeeded()

    def _disconnect_model(self, model: RbaButtonModel):
        model.logout_finished.disconnect(self._on_logout_finished)
        model.logout_finished.disconnect(self.logoutFinished)
        model.login_finished.disconnect(self.loginFinished)
        model.login_finished.disconnect(self._auth_btn.forward_login_finished)
        model.login_started.disconnect(self._auth_btn.forward_login_started)
        model.login_succeeded.disconnect(self._on_login_succeeded)
        model.login_succeeded.disconnect(self.loginSucceeded)
        model.login_succeeded.disconnect(self._auth_btn.forward_login_succeeded)
        model.login_failed.disconnect(self._auth_btn.forward_login_error)
        model.login_failed.disconnect(self.loginFailed)
        model.token_expired.disconnect(self.tokenExpired)
        if model.parent() is self:
            model.setParent(None)
            model.deleteLater()

    def _on_orientation_changed(self, new_val: Qt.Orientation):
        new_layout_type = QHBoxLayout if new_val == Qt.Horizontal else QVBoxLayout
        prev_layout = self.layout()
        if type(prev_layout) == new_layout_type:
            return
        if prev_layout is not None:
            for child in prev_layout.children():  # children of a layout are always items
                prev_layout.removeItem(child)

        new_layout = new_layout_type()
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(0)
        new_layout.addWidget(self._auth_btn)
        new_layout.addWidget(self._user_btn)

        if prev_layout is not None:
            # You can't directly delete a layout and you can't
            # replace a layout on a widget which already has one
            # Found here: https://stackoverflow.com/a/10439207
            QObjectCleanupHandler().add(prev_layout)
            prev_layout = None

        self.setLayout(new_layout)
        self._auth_btn.setOrientation(new_val)
        self._user_btn.setOrientation(new_val)

    def _on_logout_finished(self):
        self._auth_btn.decorate(connected=False)
        self._user_btn.hide()

    def _on_login_succeeded(self):
        self._auth_btn.decorate(connected=True)
        self._user_btn.show()
        # We are using token from the model and not from the arguments to work on the wrapped object and not
        # touch pyrbac API
        self._user_btn.setText(self.model.token.username)


class RbaButtonBase(OrientedToolButton):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent=parent,
                         primary=QSizePolicy.Preferred,
                         secondary=QSizePolicy.Expanding)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setAutoRaise(True)

    @property
    def _model(self) -> RbaButtonModel:
        return cast(RbaButton, self.parent()).model

    @Slot(bool)
    @Slot(list)
    def _request_location_login(self, roles: Union[List[str], bool]):
        if isinstance(roles, list):
            self._model.login_by_location_with_roles(preselected_roles=roles)
        else:
            self._model.login_by_location(interactively_select_roles=roles)

    @Slot(str, str, bool)
    @Slot(str, str, list)
    def _request_explicit_login(self, username: str, password: str, roles: Union[List[str], bool]):
        if isinstance(roles, list):
            self._model.login_explicitly_with_roles(username=username,
                                                    password=password,
                                                    preselected_roles=roles)
        else:
            self._model.login_explicitly(username=username,
                                         password=password,
                                         interactively_select_roles=roles)

    # TODO: Uncomment when adding kerberos support
    # @Slot(bool)
    # @Slot(list)
    # def _request_kerberos_login(self, roles: Union[List[str], bool]):
    #     if isinstance(roles, list):
    #         self._model.login_by_kerberos_with_roles(username=username,
    #                                                 password=password,
    #                                                 preselected_roles=roles)
    #     else:
    #         self._model.login_by_kerberos(username=username,
    #                                      password=password,
    #                                      interactively_select_roles=roles)


class RbaUserButton(RbaButtonBase):

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Button that is embedded into the toolbar to open the dialog.

        Args:
            parent: Parent widget to hold this object.
        """
        super().__init__(parent)
        menu = QMenu(self)
        self.setMenu(menu)
        menu.addAction("Select Roles", self._open_role_picker)
        menu.addSeparator()
        menu.addAction("Show Existing RBAC Token", self._open_token_details)

    def _open_role_picker(self):
        # TODO: This is a workaround until pyrbac implements proper roles retrieval. Critical roles are not available for selection when was logged in without roles previously (hence only have active ones)
        if self._token._roles_can_be_trusted:
            picker = RbaRolePicker(roles=self._token.roles,
                                   display_auto_renewable_notice=self._token.auto_renewable,
                                   parent=self)
            picker.roles_selected.connect(self._on_roles_selected)
            picker.exec_()
        else:
            QMessageBox().information(self,
                                      "Action required",
                                      "Available roles cannot be reliably obtained. Please logout and login "
                                      'again, while checking "Select roles at login".',
                                      QMessageBox.Ok)

    def _on_roles_selected(self, selected_roles: List[str], role_picker: QDialog):
        # For some reason self.sender() gives handle to self here, so we have to pass role_picker explicitly in signal
        model = self._model
        token = model.token
        if token is None:
            warnings.warn("Token has been removed in the meantime. Roles will not be updated.")
            role_picker.reject()
            return

        if token.login_method == RbaToken.LoginMethod.LOCATION:
            self._request_location_login(selected_roles)
            # Since we were logged in by location before, assumption is that it will succeed again, not much
            # else we can ask user to do. In corner cases it may fail though.
            # It is better though to avoid ephemeral signal connection to close dialog after successful re-login,
            # as this connection may stay alive.
            role_picker.accept()

        # TODO: Uncomment when adding kerberos support
        # elif token.login_method == RbaToken.LoginMethod.KERBEROS:
        #     pass

        else:
            # Note! This is a workaround (cause we can't re-login again without storing user's credentials),
            # We must ask for login again.

            dialog = RbaAuthDialog(new_roles=selected_roles,
                                   display_location_tab=token.login_method == RbaToken.LoginMethod.UNKNOWN,
                                   username=token.username,
                                   parent=self)
            dialog.setWindowTitle("Authenticate to apply new roles")
            model.login_succeeded.connect(dialog.on_login_status_changed)
            model.login_failed.connect(dialog.on_login_failed)
            model.login_started.connect(dialog.on_login_started)
            model.login_finished.connect(dialog.on_login_finished)
            dialog.location_login[bool].connect(self._request_location_login)
            dialog.location_login[list].connect(self._request_location_login)
            dialog.explicit_login[str, str, bool].connect(self._request_explicit_login)
            dialog.explicit_login[str, str, list].connect(self._request_explicit_login)
            # TODO: Uncomment when adding kerberos support
            # dialog.kerberos_login[bool].connect(self._request_kerberos_login)
            # dialog.kerberos_login[list].connect(self._request_kerberos_login)
            if dialog.exec_() == QDialog.Accepted:
                role_picker.accept()

    def _open_token_details(self):
        dialog = RbaTokenDialog(token=self._token, parent=self)
        dialog.exec_()

    @property
    def _token(self) -> RbaToken:
        if self._model.token is None:
            raise RuntimeError
        return self._model.token


class RbaAuthButton(RbaButtonBase):

    forward_login_error = Signal(str, int)
    forward_login_started = Signal(int)
    forward_login_finished = Signal()
    forward_login_succeeded = Signal(Token)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Button that is embedded into the toolbar to open the dialog.

        Args:
            parent: Parent widget to hold this object.
        """
        super().__init__(parent)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self._menu = TabFocusPreservingMenu(self)
        login_dialog = RbaAuthPopupWidget(parent=self)
        login_dialog.location_login[bool].connect(self._request_location_login)
        login_dialog.location_login[list].connect(self._request_location_login)
        login_dialog.explicit_login[str, str, bool].connect(self._request_explicit_login)
        login_dialog.explicit_login[str, str, list].connect(self._request_explicit_login)
        # TODO: Uncomment when adding kerberos support
        # login_dialog.kerberos_login[bool].connect(self._request_kerberos_login)
        # login_dialog.kerberos_login[list].connect(self._request_kerberos_login)
        self.forward_login_error.connect(login_dialog.on_login_failed)
        self.forward_login_started.connect(login_dialog.on_login_started)
        self.forward_login_finished.connect(login_dialog.on_login_finished)
        self.forward_login_succeeded.connect(login_dialog.on_login_status_changed)
        action = QWidgetAction(self)
        action.setDefaultWidget(login_dialog)
        self._menu.addAction(action)
        self.decorate(connected=False)

    def decorate(self, connected: bool):
        """
        Decorate the button in accordance with the RBAC status.

        Args:
            connected: User is online.
        """
        icon_name: str
        if connected:
            icon_name = "online.ico"
            menu = self.menu()
            if menu:  # Avoid initial error, when menu might not be created
                menu.hide()
            self.setMenu(None)
            self.clicked.connect(self._on_clicked_when_connected)
        else:
            icon_name = "offline.ico"
            self.setMenu(self._menu)
            try:
                self.clicked.disconnect()
            except TypeError:
                # Was not connected (happens during initial setup)
                pass

        self.setIcon(make_icon(Path(__file__).parent.absolute() / "icons" / icon_name))

    def set_margin_icon_size(self, size: QSize):
        return self.setIconSize(size - QSize(_ICON_MARGIN * 2, _ICON_MARGIN * 2))

    def minimumSizeHint(self) -> QSize:
        try:
            is_in_toolbar = isinstance(self.parent().parent(), QToolBar)
        except AttributeError:
            is_in_toolbar = False
        if is_in_toolbar:
            return super().minimumSizeHint()
        return QSize(31, 31)

    def _on_clicked_when_connected(self):
        self._model.logout()


class TabFocusPreservingMenu(QMenu):
    """
    Subclass that restores default Tab behavior. It also removes the popup closing on double Return press.

    As explained `here <https://stackoverflow.com/a/20388856>`__, menus have a special treatment
    of Tab keystrokes, mainly to navigate up and down the menu. However, we want to preserve Tab
    navigation within out login widget, otherwise jumping between Username/Password fields is
    inconvenient.
    """

    def focusNextPrevChild(self, next: bool) -> bool:
        """
        Finds a new widget to give the keyboard focus to, as appropriate for ``Tab`` and ``Shift+Tab``,
        and returns ``True`` if it can find a new widget, or ``False`` if it can't.

        If ``next`` is ``True``, this function searches forward, if ``next`` is ``False``, it searches backward.

        Sometimes, you will want to reimplement this function. For example, a web browser might reimplement it to
        move its "current active link" forward or backward, and call :meth:`QWidget.focusNextPrevChild` only when
        it reaches the last or first link on the "page".

        Child widgets call :meth:`QWidget.focusNextPrevChild` on their parent widgets, but only the window that
        contains the child widgets decides where to redirect focus. By reimplementing this function for an object,
        you thus gain control of focus traversal for all child widgets.
        """
        return QWidget.focusNextPrevChild(self, next)

    def keyPressEvent(self, event: QKeyEvent):
        """Prevents menu from closing on double Return press."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            return
        super().keyPressEvent(event)


_ICON_MARGIN = 3
