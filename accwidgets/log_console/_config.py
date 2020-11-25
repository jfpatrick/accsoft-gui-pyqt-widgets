import logging
from typing import Dict, Union, Iterable, Tuple
from enum import IntEnum


class LogLevel(IntEnum):
    """
    Abstraction for the logging severity level that is not tied to Python :mod:`logging` (to allow
    alternative implementations) but resembles it closely, as the majority of user cases still rely
    on Python :mod:`logging`."""

    NOTSET = logging.NOTSET
    """
    Inherit the logger level from the parent logger. This has the same value and effect as
    :obj:`~logging.NOTSET` of Python :mod:`logging`. For custom model implementations that do not
    use Python :mod:`logging` under the hood, it's up to the implementer to recognize this option.
    """

    DEBUG = logging.DEBUG
    """
    Debug messages are meant for application developers and usually are not exposed to end-users
    by default.
    """

    INFO = logging.INFO
    """
    Information messages present output that is not generated because of a problem but rather some
    things to note.
    """

    WARNING = logging.WARNING
    """
    Warnings mark undesirable effects, which still do not impact normal program execution.
    """

    ERROR = logging.ERROR
    """
    Errors are unsupported problems with execution flow or data, which can be handled for the program
    to keep running but are not expected to happen during normal execution.
    """

    CRITICAL = logging.CRITICAL
    """
    Critical errors are events that impact the program in the most severe way, so that it cannot
    keep running reliably.
    """

    @classmethod
    def level_name(cls, level: Union["LogLevel", int]):
        """
        Extract a human-readable logging severity level name from the enum value.

        Args:
            level: Input enum value or its integer equivalent.

        Returns:
            Human-readable string.
        """
        if not isinstance(level, int):
            level = level.value
        return logging.getLevelName(level)

    @classmethod
    def real_levels(cls) -> Iterable["LogLevel"]:
        """
        Real levels represent the subset of enum options that actually depict a message severity level
        (and can thus be related to e.g. output color). Currently, this subset is everything, except for
        :obj:`NOTSET`.

        Returns:
            Iterator of real logging levels.
        """
        for level in cls:
            if level == LogLevel.NOTSET:
                continue
            yield level


ColorMap = Dict[LogLevel, Tuple[str, bool]]
"""Color map maps logging levels to tuples (color name or hash, colors must be inverted)."""
