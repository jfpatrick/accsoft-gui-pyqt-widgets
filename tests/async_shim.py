# flake8: noqa: F401
try:
    from unittest.mock import AsyncMock  # type: ignore  # mypy fails this in Python 3.7
except ImportError:
    from mock import AsyncMock  # type: ignore  # mypy fails this in Python 3.7
