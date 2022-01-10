from typing_extensions import Protocol, runtime_checkable
from qtpy.QtCore import Signal


@runtime_checkable
class RbaButtonProtocol(Protocol):
    loginFinished: Signal
    loginSucceeded: Signal
    loginFailed: Signal
    logoutFinished: Signal
    tokenExpired: Signal
