# Note! This code assumes that you have "qasync" installed as a dependency, but it's not enforced anywhere,
# and it's user's responsibility to ensure the presence of the library, when using these APIs.
# for instance, when having "from accwidgets._async_utils import ...", make sure to specify "qasync" in the
# __deps__.py of your widget.

import asyncio
from typing import Optional
from qtpy.QtGui import QGuiApplication
from qasync import QEventLoop


def install_asyncio_event_loop(app: Optional[QGuiApplication] = None):
    """
    Interleaves asyncio loop with Qt event loop, enabling asyncio-code inside GUI applications.

    Args:
        app: Application instance. If :obj:`None` is given, the singleton instance will be fetched.
    """
    if isinstance(asyncio.get_event_loop(), QEventLoop):
        return

    asyncio.set_event_loop(make_qt_compatible_loop(app))


def make_qt_compatible_loop(app: Optional[QGuiApplication] = None) -> asyncio.BaseEventLoop:
    """
    Creates a Qt-compatible :mod:`asyncio` event loop.

    Args:
        app: Application instance. If :obj:`None` is given, the singleton instance will be fetched.

    Returns:
        New event loop instance.
    """
    if app is None:
        app = QGuiApplication.instance()

    return QEventLoop(app)
