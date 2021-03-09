import socket
import signal
from typing import Optional
from qtpy.QtCore import QObject
from qtpy.QtWidgets import QApplication
from qtpy.QtNetwork import QAbstractSocket


class SignalWakeUpHandler(QAbstractSocket):

    def __init__(self, parent: Optional[QObject] = None):
        """
        Handler to propagate OS signals and avoid blocking of the handling by Qt event loop.

        The Qt event loop is implemented in C++, hence, while it runs and no Python code is called (eg. by a Qt
        signal connected to a Python slot), the signals are noted, but the Python signal handlers aren't called.

        Since Python 2.6 and in Python 3 it is possible to make Qt run a Python function when a signal with a handler
        is received using signal.set_wakeup_fd(). This is possible, because, contrary to the documentation,
        the low-level signal handler doesn't only set a flag for the virtual machine, but it may also write a byte
        into the file descriptor set by set_wakeup_fd(). Python 2 writes a NUL byte, Python 3 writes the signal
        number.

        Subclassing a Qt class that takes a file descriptor and provides a readReady() signal, like e.g.
        QAbstractSocket, the event loop will execute a Python function every time a signal (with a handler)
        is received causing the signal handler to execute nearly instantaneous.

        This implementation is highly inspired by https://stackoverflow.com/a/37229299
        """
        super().__init__(QAbstractSocket.UdpSocket, parent)
        self._write_socket, self._read_socket = socket.socketpair(type=socket.SOCK_DGRAM)
        self._write_socket.setblocking(False)
        self.setSocketDescriptor(self._read_socket.fileno())  # Let Qt listen on the one end
        self._prev_fd = signal.set_wakeup_fd(self._write_socket.fileno())  # Let Python write on the other end
        # First Python code executed gets any exception from the signal handler, so add a dummy handler first
        self.readyRead.connect(lambda: None)
        # Second handler does the real handling
        self.readyRead.connect(self._on_ready_read)

    def __del__(self):
        # Restore any old handler on deletion
        if self._prev_fd:
            signal.set_wakeup_fd(self._prev_fd)

    def _on_ready_read(self):
        # readyRead is blocked from occurring again until readData() was called, so call it,
        # even if you don't need the value.
        _ = self.readData(1)


def attach_sigint(app: QApplication):
    """
    Attach SIGINT interrupt handler, so that PyQt application can be gracefully exited on Ctrl+C shortcut from the
    terminal.

    Args:
        app: Application that is to be run.
    """
    SignalWakeUpHandler(app)  # Pass app, so that object gets preserved by parent-child relationship
    signal.signal(signal.SIGINT, lambda sig, _: app.quit())
