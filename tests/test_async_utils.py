import pytest
import asyncio
from unittest import mock
from qasync import QEventLoop
from qtpy.QtWidgets import QApplication
from accwidgets._async_utils import install_asyncio_event_loop


@pytest.fixture(scope="function")
def reset_event_loop():
    # This fixture attempts to isolate all event loops that are placed inside asyncio system.
    # It also tries to protect from automatic QEventLoop initialization that is created
    # inside conftest.py in order to allow testing of asyncronous Qt interfaces in other parts of the library
    asyncio.get_event_loop_policy().set_event_loop(asyncio.get_event_loop_policy().new_event_loop())

    def simple_get_event_loop():
        return asyncio.get_event_loop_policy().get_event_loop()

    def simple_set_event_loop(loop):
        asyncio.get_event_loop_policy().set_event_loop(loop)

    with mock.patch("asyncio.get_event_loop", side_effect=simple_get_event_loop):
        with mock.patch("asyncio.set_event_loop", side_effect=simple_set_event_loop):
            yield
    last_loop = asyncio.get_event_loop_policy().get_event_loop()
    last_loop.close()


@pytest.mark.parametrize("use_app", [True, False])
def test_install_asyncio_event_loop_noop_already_installed(qapp: QApplication, use_app, reset_event_loop):
    _ = reset_event_loop
    app = qapp if use_app else None
    orig_event_loop = asyncio.get_event_loop()
    assert orig_event_loop is not None
    assert not isinstance(orig_event_loop, QEventLoop)
    install_asyncio_event_loop(app)
    orig_event_loop = asyncio.get_event_loop()
    assert orig_event_loop is not None
    assert isinstance(orig_event_loop, QEventLoop)
    install_asyncio_event_loop(app)
    assert asyncio.get_event_loop() is orig_event_loop


@pytest.mark.parametrize("passed_app_default", [
    None,
    True,
    False,
])
def test_install_asyncio_event_installs(passed_app_default, reset_event_loop, qapp: QApplication):
    _ = reset_event_loop
    orig_event_loop = asyncio.get_event_loop()
    assert orig_event_loop is not None
    assert not isinstance(orig_event_loop, QEventLoop)
    if passed_app_default is None:
        app = None
        expected_instance = qapp
    elif passed_app_default is True:
        app = qapp
        expected_instance = qapp
    else:
        old_instance = qapp
        new_instance = mock.MagicMock()
        assert new_instance is not old_instance
        app = new_instance
        expected_instance = new_instance
    with mock.patch("asyncio.set_event_loop") as set_event_loop:

        used_args = None
        mocked_loop = mock.MagicMock(spec=QEventLoop)

        class MockedEventLoop(QEventLoop):

            def __new__(cls, *args, **kwargs):
                nonlocal used_args
                used_args = args
                return mocked_loop

        with mock.patch("accwidgets._async_utils.QEventLoop", new=MockedEventLoop):
            install_asyncio_event_loop(app)
            assert used_args == (expected_instance,)
            set_event_loop.assert_called_once_with(mocked_loop)
