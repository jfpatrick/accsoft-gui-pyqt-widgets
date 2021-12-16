from typing import Optional, List
from pathlib import Path
from enum import IntEnum, auto
from qtpy import uic
from qtpy.QtGui import QHideEvent, QKeyEvent, QShowEvent
from qtpy.QtCore import QEvent, QSignalBlocker, Qt, Signal
from qtpy.QtWidgets import (QWidget, QPushButton, QLineEdit, QLabel, QTabWidget, QCheckBox, QVBoxLayout,
                            QDialogButtonBox, QDialog, QStackedWidget)
from accwidgets.qt import ActivityIndicator
from ._token import RbaToken


class RbaAuthDialogWidget(QWidget):

    class DefaultLoginTab(IntEnum):
        """Position where Get/Set buttons are placed, relative to the fields form."""

        LOCATION = auto()
        """Login by location tab will be focused when opening the dialog."""

        EXPLICIT = auto()
        """Login with credentials tab will be focused when opening the dialog."""

        # TODO: Uncomment when adding kerberos support
        # KERBEROS = auto()
        # """Login with Kerberos tab will be focused when opening the dialog."""

    location_login = Signal([bool], [list])
    """
    Signal to attempt the login by location.

    This signal has 2 overloads:

    * bool argument: Login with boolean indicating whether interactive roles selection is needed
    * list argument: Login with pre-selected roles, which are a list of strings. No interactive roles selection should be done.
    """

    explicit_login = Signal([str, str, bool], [str, str, list])
    """
    Signal to attempt the login with user credentials.

    This signal has 2 overloads (the first 2 arguments always correspond to entered username and password):

    * bool as the last argument: Login with boolean indicating whether interactive roles selection is needed
    * list as the last argument: Login with pre-selected roles, which are a list of strings. No interactive roles selection should be done.
    """

    # TODO: Uncomment when adding kerberos support
    # kerberos_login = Signal([bool], [list])
    # """
    # Signal to attempt the login with Kerberos token.
    #
    # This signal has 2 overloads:
    #
    # * bool argument: Login with boolean indicating whether interactive roles selection is needed
    # * list argument: Login with pre-selected roles, which are a list of strings. No interactive roles selection should be done.
    # """

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 initial_username: Optional[str] = None,
                 focused_tab: "RbaAuthDialogWidget.DefaultLoginTab" = DefaultLoginTab.LOCATION,
                 roles: Optional[List[str]] = None):
        """
        Dialog seen when user presses the RBAC button.

        Args:
            parent: Parent widget to own this object.
            initial_username: If for some reason, the used username was known, prefill it for convenience.
            focused_tab: Tab to be initially open.
            roles: Roles that should be used during the login.
        """
        super().__init__(parent)

        # For IDE support, assign types to dynamically created items from the *.ui file
        self.loc_btn: QPushButton = None
        self.user_btn: QPushButton = None
        self.username: QLineEdit = None
        self.password: QLineEdit = None
        self.user_error: QLabel = None
        self.loc_error: QLabel = None
        self.user_auto_info: QLabel = None
        self.loc_auto_info: QLabel = None
        self.tabs: QTabWidget = None
        self.roles_explicit: QCheckBox = None
        self.roles_loc: QCheckBox = None
        self.activity_stack: QStackedWidget = None
        self.activity_indicator: ActivityIndicator = None  # type: ignore

        uic.loadUi(Path(__file__).parent / "rbac_dialog.ui", self)

        self.user_error.hide()
        self.loc_error.hide()
        self.user_error.setProperty("qss-role", "error")
        self.loc_error.setProperty("qss-role", "error")
        self.user_auto_info.hide()
        self.loc_auto_info.hide()
        self.user_auto_info.setProperty("qss-role", "info")
        self.loc_auto_info.setProperty("qss-role", "info")
        self.activity_stack.setCurrentIndex(self._STACK_NORMAL)
        self.activity_indicator.hint = "Logging in..."

        if initial_username:
            self.username.setText(initial_username)
            self.username.setEnabled(False)
            self.username.setClearButtonEnabled(False)
            self.password.setFocus()
        if focused_tab == RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT:
            self.tabs.setCurrentIndex(self._TAB_EXPLICIT_LOGIN)
        elif focused_tab == RbaAuthDialogWidget.DefaultLoginTab.LOCATION:
            self.tabs.setCurrentIndex(self._TAB_LOCATION_LOGIN)
        # TODO: Uncomment when adding kerberos support
        # elif focused_tab == RbaAuthDialogWidget.DefaultLoginTab.KERBEROS:
        #     self.tabs.setCurrentIndex(self._TAB_KERBEROS_LOGIN)

        self._immediate_roles: bool = False

        self.loc_btn.clicked.connect(self._login_loc)
        self.user_btn.clicked.connect(self._login_user)

        if roles is None:
            self.roles_explicit.stateChanged.connect(self._roles_change)
            self.roles_explicit.stateChanged.connect(self.user_auto_info.show)
            self.roles_explicit.stateChanged.connect(self.loc_auto_info.show)
            self.roles_loc.stateChanged.connect(self._roles_change)
            self.roles_loc.stateChanged.connect(self.user_auto_info.show)
            self.roles_loc.stateChanged.connect(self.loc_auto_info.show)
        else:
            # Roles already have been preselected, so we don't give user an opportunity to pick them here
            self.roles_explicit.hide()
            self.roles_loc.hide()

        self._roles = roles

    def on_login_status_changed(self, token: Optional[RbaToken]):
        """
        Slot to get notified when login status has changed.

        This method cleans up the entered password in the explicit login tab.

        Args:
            token: Token of the connected user or :obj:`None` for the disconnected state.
        """
        if token is not None or not self.isVisible():
            self.password.setText(None)
        self.user_error.setText(None)
        self.loc_error.setText(None)

    def on_login_failed(self, msg: str, login_method: int):
        """
        Slot to get notified about the error when attempting login.

        Args:
            message: Error message.
        """
        if not self.isVisible():
            # Do not react to events that may be coming from the model triggered by another auth widget,
            # e.g. when logging in to apply new roles
            return
        self.user_error.setVisible(login_method == RbaToken.LoginMethod.EXPLICIT)
        self.loc_error.setVisible(login_method == RbaToken.LoginMethod.LOCATION)
        if login_method == RbaToken.LoginMethod.EXPLICIT:
            self.user_error.setText(msg)
            self.tabs.setCurrentIndex(self._TAB_EXPLICIT_LOGIN)
        elif login_method == RbaToken.LoginMethod.LOCATION:
            self.loc_error.setText(msg)
            self.tabs.setCurrentIndex(self._TAB_LOCATION_LOGIN)
        # TODO: Uncomment when adding kerberos support
        # elif login_method == RbaToken.LoginMethod.KERBEROS:
        #     self._main_widget.on_kerberos_login_error(msg)

    def on_login_started(self, *_):
        if not self.isVisible():
            # Do not react to events that may be coming from the model triggered by another auth widget,
            # e.g. when logging in to apply new roles
            return
        self.activity_indicator.startAnimation()
        self.activity_stack.setCurrentIndex(self._STACK_ACTIVITY)

    def on_login_finished(self):
        self.activity_indicator.stopAnimation()
        self.activity_stack.setCurrentIndex(self._STACK_NORMAL)

    def hideEvent(self, event: QHideEvent):
        super().hideEvent(event)
        self.password.setText(None)
        self.user_error.setText(None)
        self.loc_error.setText(None)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.username.hasFocus():
                self.focusNextChild()
            elif self.password.hasFocus():
                self.user_btn.click()
        super().keyPressEvent(event)

    _TAB_LOCATION_LOGIN = 0
    _TAB_EXPLICIT_LOGIN = 1
    # TODO: Uncomment when adding kerberos support
    # _TAB_KERBEROS_LOGIN = 2

    _STACK_NORMAL = 0
    _STACK_ACTIVITY = 1

    def _roles_change(self, state: Qt.CheckState):
        blocker1 = QSignalBlocker(self.roles_explicit)
        blocker2 = QSignalBlocker(self.roles_loc)
        self._immediate_roles = state == Qt.Checked
        self.roles_explicit.setChecked(self._immediate_roles)
        self.roles_loc.setChecked(self._immediate_roles)
        blocker1.unblock()
        blocker2.unblock()

    def _login_loc(self):
        self.loc_error.hide()
        self.user_error.hide()

        if self._immediate_roles:
            self.location_login[bool].emit(True)
        elif self._roles is None:
            self.location_login[bool].emit(False)
        else:
            self.location_login[list].emit(self._roles)

    def _login_user(self):
        user = self.username.text()
        passwd = self.password.text()
        if not user and not passwd:
            self.user_error.setText("You must type in username and password")
        elif not user:
            self.user_error.setText("You must type in username")
        elif not passwd:
            self.user_error.setText("You must type in password")
        else:
            self.user_error.hide()
            self.loc_error.hide()

            if self._immediate_roles:
                self.explicit_login[str, str, bool].emit(user, passwd, True)
            elif self._roles is None:
                self.explicit_login[str, str, bool].emit(user, passwd, False)
            else:
                self.explicit_login[str, str, list].emit(user, passwd, self._roles)
            return
        self.user_error.show()


class RbaAuthDialog(QDialog):

    location_login = Signal([bool], [list])
    explicit_login = Signal([str, str, bool], [str, str, list])
    # TODO: Uncomment when adding kerberos support
    # kerberos_login = Signal([bool], [list])

    def __init__(self,
                 new_roles: List[str],
                 display_location_tab: bool,
                 username: str,
                 parent: Optional[QWidget] = None):
        """
        Wrapper for the :class:`RbaAuthDialogWidget`. Currently, we cannot re-login
        with new roles automatically, as :mod:`pyrbac` does not provide such capability.
        Instead, we are bound to ask the user to login again with a new login dialog.

        Args:
            new_roles: Roles to use when signing in again.
            display_location_tab: Display tab for location login. It should not be provided when explicit login
                                  was used originally. Location tab will be displayed as a fallback for unknown
                                  login method, such that comes with external tokens.
            username: Username to prefill for convenience.
            parent: Owning object.
        """
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.setLayout(layout)
        focused_tab = (RbaAuthDialogWidget.DefaultLoginTab.LOCATION if display_location_tab
                       else RbaAuthDialogWidget.DefaultLoginTab.EXPLICIT)
        # TODO: Need something here when Kerberos is supported
        self._main_widget = RbaAuthDialogWidget(parent=self,
                                                initial_username=username,
                                                focused_tab=focused_tab,
                                                roles=new_roles)
        self._main_widget.location_login[bool].connect(self.location_login[bool])
        self._main_widget.location_login[list].connect(self.location_login[list])
        self._main_widget.explicit_login[str, str, bool].connect(self.explicit_login[str, str, bool])
        self._main_widget.explicit_login[str, str, list].connect(self.explicit_login[str, str, list])
        self._main_widget.layout().setContentsMargins(0, 0, 0, 0)
        if not display_location_tab:
            self._main_widget.tabs.removeTab(RbaAuthDialogWidget._TAB_LOCATION_LOGIN)
        self._btn_box = QDialogButtonBox(QDialogButtonBox.Cancel, self)
        layout.addWidget(self._main_widget)
        layout.addWidget(self._btn_box)
        self._btn_box.rejected.connect(self.close)

    def on_login_status_changed(self, token: Optional[RbaToken] = None):
        """
        Slot to get notified when login status has changed.

        Closes the dialog when login has been successful.

        Args:
            token: Retrieved token for the logged in user, otherwise :obj:`None`.
        """
        if token is not None:
            self.accept()
        else:
            self._main_widget.on_login_status_changed(token)

    def on_login_failed(self, msg: str, login_method: int):
        self._main_widget.on_login_failed(msg, login_method)

    def on_login_started(self, login_method: int):
        self._main_widget.on_login_started(login_method)

    def on_login_finished(self):
        self._main_widget.on_login_finished()


class RbaAuthPopupWidget(RbaAuthDialogWidget):

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonPress or event.type() == QEvent.MouseButtonRelease:
            # Prevent widget being hidden on a click inside the popup area
            return True
        return super().event(event)

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)

        # Highlights "Login by location" button in Location tab
        # + "Username" field in credentials tab
        if self.tabs.currentIndex() == self._TAB_LOCATION_LOGIN:
            self.focusPreviousChild()
        elif not self.password.hasFocus():
            self.username.setFocus()
