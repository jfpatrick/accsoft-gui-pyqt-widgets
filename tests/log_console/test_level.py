import pytest
import logging
from accwidgets.log_console import LogLevel


@pytest.mark.parametrize("level,expected_name", [
    (LogLevel.DEBUG, "DEBUG"),
    (LogLevel.INFO, "INFO"),
    (LogLevel.CRITICAL, "CRITICAL"),
    (LogLevel.WARNING, "WARNING"),
    (LogLevel.ERROR, "ERROR"),
    (LogLevel.NOTSET, "NOTSET"),
    (logging.DEBUG, "DEBUG"),
    (logging.INFO, "INFO"),
    (logging.CRITICAL, "CRITICAL"),
    (logging.WARNING, "WARNING"),
    (logging.ERROR, "ERROR"),
    (logging.NOTSET, "NOTSET"),
])
def test_level_name(level, expected_name):
    assert LogLevel.level_name(level) == expected_name


def test_real_levels():
    assert set(LogLevel.real_levels()) == {LogLevel.DEBUG,
                                           LogLevel.INFO,
                                           LogLevel.WARNING,
                                           LogLevel.ERROR,
                                           LogLevel.CRITICAL}
    assert LogLevel.NOTSET not in LogLevel.real_levels()
