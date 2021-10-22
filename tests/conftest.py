import os
import time
import pytest
import asyncio
from accwidgets._async_utils import make_qt_compatible_loop


# Reset timezone to UTC for time-sensitive tests, e.g. those using freezegun.
# While setting freezegun to a date with explicit timezone may work, it also
# may fail on systems, where $TZ environment variable is undefined. Here, we
# define it explicitly to avoid those problems.
os.environ["TZ"] = "Etc/UTC"
time.tzset()


# Override default pytest-asyncio's event_loop fixture so that QEventLoop is used in tests by default
# This will help avoid creating 2 event loops:
# 1. From pytest-asyncio (when used with @pytest.mark.asyncio)
# 2. QEventLoop Inside the widget, when it calls install_asyncio_event_loop()
@pytest.fixture(scope="function")
def event_loop(request, qtbot):
    _ = request
    try:
        # This may fail, if QApplication was not instantiated, e.g. in the tests, where qtbot is not used
        # But in that case, we don't really care about Qt-compatible event loop and can use standard asyncio
        # even loop
        loop = make_qt_compatible_loop()
    except Exception:  # noqa: B902
        # Standard implementation of pytest-asyncio
        loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
