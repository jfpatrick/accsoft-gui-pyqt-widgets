try:
    from unittest.mock import AsyncMock  # type: ignore  # this is py3.8+ code, fails in 3.7 mypy
except ImportError:
    from unittest.mock import Mock

    class AsyncMock(Mock):  # type: ignore  # mypy thinks it's already defined above

        async def __call__(self, *args, **kwargs):
            return super().__call__(*args, **kwargs)
