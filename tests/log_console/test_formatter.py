import pytest
from dateutil.parser import isoparse
from accwidgets.log_console import LogConsoleFormatter, LogConsoleRecord, LogLevel
from .fixtures import *  # noqa: F401,F403


@pytest.mark.parametrize("test_attr", [True, False])
@pytest.mark.parametrize("test_attr2", [True, False])
def test_custom_fmt_create_calls_init(custom_fmt_class, test_attr, test_attr2):
    obj = custom_fmt_class.create(test_attr=test_attr, test_attr2=test_attr2)
    assert type(obj) == custom_fmt_class
    assert obj.test_attr == test_attr
    assert obj.test_attr2 == test_attr2


def test_std_fmt_configurable_items():
    assert LogConsoleFormatter.configurable_attributes() == {
        "show_date": "Show date",
        "show_time": "Show time",
        "show_logger_name": "Show Logger name",
    }


@pytest.mark.parametrize("show_date,show_time,show_logger_name,record_logger,record_message,record_level,record_timestamp,record_millis,expected_string", [
    (False, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "DEBUG - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "logger.name - DEBUG - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - DEBUG - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - logger.name - DEBUG - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "2020-01-02 - DEBUG - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "2020-01-02 - logger.name - DEBUG - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - DEBUG - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - logger.name - DEBUG - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "INFO - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "logger.name - INFO - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - INFO - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - logger.name - INFO - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "2020-01-02 - INFO - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "2020-01-02 - logger.name - INFO - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - INFO - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - logger.name - INFO - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "WARNING - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "logger.name - WARNING - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - WARNING - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - logger.name - WARNING - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "2020-01-02 - WARNING - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "2020-01-02 - logger.name - WARNING - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - WARNING - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - logger.name - WARNING - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "ERROR - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "logger.name - ERROR - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - ERROR - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - logger.name - ERROR - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "2020-01-02 - ERROR - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "2020-01-02 - logger.name - ERROR - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - ERROR - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - logger.name - ERROR - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "CRITICAL - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "logger.name - CRITICAL - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - CRITICAL - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "23:43:11,959354 - logger.name - CRITICAL - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "2020-01-02 - CRITICAL - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "2020-01-02 - logger.name - CRITICAL - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - CRITICAL - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, "2020-01-02 23:43:11,959354 - logger.name - CRITICAL - Message body"),
])
def test_std_fmt_format(show_time, show_date, show_logger_name, record_level, record_logger, record_message, record_millis,
                        record_timestamp, expected_string):
    obj = LogConsoleFormatter(show_time=show_time,
                              show_date=show_date,
                              show_logger_name=show_logger_name)
    record = LogConsoleRecord(logger_name=record_logger,
                              level=record_level,
                              message=record_message,
                              millis=record_millis,
                              timestamp=isoparse(record_timestamp).timestamp())
    assert obj.format(record) == expected_string
