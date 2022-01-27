from .fixtures import *  # noqa: F401,F403
import pytest
from dateutil.parser import isoparse
from accwidgets.log_console import LogConsoleFormatter, LogConsoleRecord, LogLevel


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


class MyExceptionType(Exception):
    __module__ = "my_module"
    __qualname__ = "MyExceptionType"


dummy_exception = MyExceptionType("Test exception")


@pytest.mark.parametrize("show_date,show_time,show_logger_name,record_logger,record_message,record_level,record_timestamp,record_millis,record_extras,expected_string", [
    (False, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "DEBUG - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "logger.name - DEBUG - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - DEBUG - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - logger.name - DEBUG - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - DEBUG - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - logger.name - DEBUG - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - DEBUG - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - logger.name - DEBUG - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "INFO - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "logger.name - INFO - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - INFO - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - logger.name - INFO - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - INFO - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - logger.name - INFO - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - INFO - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - logger.name - INFO - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "WARNING - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "logger.name - WARNING - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - WARNING - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - logger.name - WARNING - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - WARNING - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - logger.name - WARNING - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - WARNING - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - logger.name - WARNING - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "ERROR - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "logger.name - ERROR - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - ERROR - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - logger.name - ERROR - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - ERROR - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - logger.name - ERROR - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - ERROR - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - logger.name - ERROR - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "CRITICAL - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "logger.name - CRITICAL - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - CRITICAL - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "23:43:11,959354 - logger.name - CRITICAL - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - CRITICAL - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "2020-01-02 - logger.name - CRITICAL - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - CRITICAL - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, None, "2020-01-02 23:43:11,959354 - logger.name - CRITICAL - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "DEBUG - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "logger.name - DEBUG - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - DEBUG - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - logger.name - DEBUG - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - DEBUG - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - logger.name - DEBUG - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - DEBUG - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - logger.name - DEBUG - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "INFO - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "logger.name - INFO - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - INFO - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - logger.name - INFO - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - INFO - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - logger.name - INFO - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - INFO - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - logger.name - INFO - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "WARNING - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "logger.name - WARNING - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - WARNING - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - logger.name - WARNING - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - WARNING - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - logger.name - WARNING - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - WARNING - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - logger.name - WARNING - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "ERROR - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "logger.name - ERROR - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - ERROR - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - logger.name - ERROR - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - ERROR - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - logger.name - ERROR - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - ERROR - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - logger.name - ERROR - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "CRITICAL - Message body"),
    (False, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "logger.name - CRITICAL - Message body"),
    (False, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - CRITICAL - Message body"),
    (False, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "23:43:11,959354 - logger.name - CRITICAL - Message body"),
    (True, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - CRITICAL - Message body"),
    (True, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 - logger.name - CRITICAL - Message body"),
    (True, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - CRITICAL - Message body"),
    (True, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"lineno": 200}, "2020-01-02 23:43:11,959354 - logger.name - CRITICAL - Message body"),
    (False, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)}, "DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)}, "logger.name - DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - logger.name - DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - logger.name - DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, False, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, True, "logger.name", "Message body", LogLevel.DEBUG, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - logger.name - DEBUG - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "logger.name - INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - logger.name - INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - logger.name - INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, False, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, True, "logger.name", "Message body", LogLevel.INFO, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - logger.name - INFO - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "logger.name - WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - logger.name - WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - logger.name - WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, False, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, True, "logger.name", "Message body", LogLevel.WARNING, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - logger.name - WARNING - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "logger.name - ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - logger.name - ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - logger.name - ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, False, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, True, "logger.name", "Message body", LogLevel.ERROR, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - logger.name - ERROR - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "logger.name - CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
    (False, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "23:43:11,959354 - logger.name - CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, False, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 - logger.name - CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, False, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
    (True, True, True, "logger.name", "Message body", LogLevel.CRITICAL, "2020-01-02 23:43:11", 959354, {"exc_info": (MyExceptionType, dummy_exception, None)},
     "2020-01-02 23:43:11,959354 - logger.name - CRITICAL - Message body\nmy_module.MyExceptionType: Test exception"),
])
def test_std_fmt_format(show_time, show_date, show_logger_name, record_level, record_logger, record_message, record_millis,
                        record_timestamp, record_extras, expected_string):
    obj = LogConsoleFormatter(show_time=show_time,
                              show_date=show_date,
                              show_logger_name=show_logger_name)
    record = LogConsoleRecord(logger_name=record_logger,
                              level=record_level,
                              message=record_message,
                              millis=record_millis,
                              timestamp=isoparse(record_timestamp).timestamp(),
                              extras=record_extras)
    assert obj.format(record) == expected_string
