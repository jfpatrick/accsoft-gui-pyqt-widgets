import pytest
import signal
from unittest import mock
from accwidgets._signal import SignalWakeUpHandler, attach_sigint


@mock.patch("accwidgets._signal.SignalWakeUpHandler")
@mock.patch("signal.signal")
def test_attach_sigint(signal_mock, SignalWakeUpHandler):
    app = mock.MagicMock()
    attach_sigint(app)
    SignalWakeUpHandler.assert_called_once_with(app)
    signal_mock.assert_called_once_with(signal.SIGINT, mock.ANY)
    passed_lambda = signal_mock.call_args[0][1]
    app.quit.assert_not_called()
    passed_lambda(mock.ANY, mock.ANY)
    app.quit.assert_called_once()


@mock.patch("accwidgets._signal.SignalWakeUpHandler.readData", autospec=True)
def test_signal_wakeup_handler_ready_read_unblocks_read(readData):
    handler = SignalWakeUpHandler()
    readData.assert_not_called()
    handler.readyRead.emit()
    readData.assert_called_once_with(1)


@pytest.mark.parametrize("fileno", [0, 1, 999])
@mock.patch("accwidgets._signal.socket.socketpair")
@mock.patch("accwidgets._signal.SignalWakeUpHandler.setSocketDescriptor", autospec=True)
@mock.patch("signal.set_wakeup_fd", autospec=True)
def test_signal_wakeup_handler_sets_signal_fd_to_write_end(set_wakeup_fd, _, socketpair, fileno):
    write_sock = mock.MagicMock()
    write_sock.fileno.return_value = fileno
    read_sock = mock.MagicMock()
    read_sock.fileno.return_value = 3
    socketpair.return_value = write_sock, read_sock
    _ = SignalWakeUpHandler()
    set_wakeup_fd.assert_called_once_with(fileno)


@pytest.mark.parametrize("fileno", [0, 1, 999])
@mock.patch("accwidgets._signal.socket.socketpair")
@mock.patch("accwidgets._signal.SignalWakeUpHandler.setSocketDescriptor", autospec=True)
@mock.patch("signal.set_wakeup_fd", autospec=True)
def test_signal_wakeup_handler_sets_own_fd_to_read_end(_, setSocketDescriptor, socketpair, fileno):
    write_sock = mock.MagicMock()
    write_sock.fileno.return_value = 3
    read_sock = mock.MagicMock()
    read_sock.fileno.return_value = fileno
    socketpair.return_value = write_sock, read_sock
    _ = SignalWakeUpHandler()
    setSocketDescriptor.assert_called_once_with(fileno)


@pytest.mark.parametrize("fileno", [0, 1, 999])
@pytest.mark.parametrize("prev_id", [-1, 1, 2])
@mock.patch("accwidgets._signal.socket.socketpair")
@mock.patch("accwidgets._signal.SignalWakeUpHandler.setSocketDescriptor", autospec=True)
@mock.patch("signal.set_wakeup_fd", autospec=True)
def test_signal_wakeup_handler_restores_original_fd_on_delete(set_wakeup_fd, _, socketpair, fileno, prev_id):
    write_sock = mock.MagicMock()
    write_sock.fileno.return_value = fileno
    read_sock = mock.MagicMock()
    read_sock.fileno.return_value = 3
    set_wakeup_fd.return_value = prev_id
    socketpair.return_value = write_sock, read_sock

    def scope():
        _ = SignalWakeUpHandler()
        set_wakeup_fd.assert_called_once_with(fileno)
        set_wakeup_fd.reset_mock()

    set_wakeup_fd.assert_not_called()
    scope()
    set_wakeup_fd.assert_called_once_with(prev_id)
