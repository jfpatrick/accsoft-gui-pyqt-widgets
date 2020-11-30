import pytest
import logging
from freezegun import freeze_time
from datetime import datetime
from dateutil.tz import UTC
from typing import cast
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QEvent
from accwidgets.log_console import LogLevel, LogConsoleModel, LogConsoleRecord
from accwidgets.log_console._model import PythonLoggingHandler, _record_from_python_logging_record, _get_logger
from .fixtures import *  # noqa: F401,F403


# We have to make the freeze time utc, otherwise freeze-gun seems to
# take the current timezone which lets tests fail
STATIC_TIME = datetime(year=2020, day=1, month=1, hour=4, minute=43, second=5, microsecond=214923, tzinfo=UTC)


@pytest.fixture(scope="function", autouse=True)
def test_fn_wrapper():
    # Reset logger cache
    logging.root = logging.RootLogger(logging.WARNING)
    logging.Logger.root = logging.root
    logging.Logger.manager = logging.Manager(logging.Logger.root)
    yield


def test_abc_model_available_logger_levels(custom_model_class):
    model = custom_model_class()
    assert model.available_logger_levels == {}
    model.selected_logger_levels = {
        "logger1": {LogLevel.ERROR},
        "logger2": {LogLevel.WARNING},
    }

    assert model.available_logger_levels == {
        "logger1": {LogLevel.NOTSET, LogLevel.DEBUG, LogLevel.WARNING, LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
        "logger2": {LogLevel.NOTSET, LogLevel.DEBUG, LogLevel.WARNING, LogLevel.INFO, LogLevel.ERROR, LogLevel.CRITICAL},
    }


def test_custom_model_level_notice_defaults_to_none(custom_model_class):
    model = custom_model_class()
    assert model.level_notice is None


def test_model_cleans_up_on_destroy(qtbot):
    _ = qtbot
    logger = logging.getLogger("test_logger")
    logger2 = logging.getLogger("test_logger2")
    assert len(logger.handlers) == 0
    assert len(logger2.handlers) == 0
    model = LogConsoleModel(loggers={logger, logger2})
    assert len(logger.handlers) == 1
    assert len(logger2.handlers) == 1
    QApplication.instance().sendEvent(model, QEvent(QEvent.DeferredDelete))  # The only working way of triggering "destroyed" signal
    assert len(logger.handlers) == 0
    assert len(logger2.handlers) == 0


def test_model_attaches_handlers_to_passed_loggers():
    logger = logging.getLogger("test_logger")
    logger2 = logging.getLogger("test_logger2")
    assert len(logger.handlers) == 0
    assert len(logger2.handlers) == 0
    model = LogConsoleModel(loggers={logger})
    assert len(logger.handlers) == 1
    assert len(logger2.handlers) == 0
    assert isinstance(logger.handlers[0], PythonLoggingHandler)
    _ = model


@pytest.mark.parametrize("modify_loggers,selected_level,root_level,expected_available_levels", [
    (False, LogLevel.CRITICAL, None, {LogLevel.NOTSET, LogLevel.CRITICAL}),
    (False, LogLevel.ERROR, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR}),
    (False, LogLevel.WARNING, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING}),
    (False, LogLevel.INFO, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO}),
    (False, LogLevel.DEBUG, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (False, LogLevel.NOTSET, LogLevel.CRITICAL, {LogLevel.NOTSET, LogLevel.CRITICAL}),
    (False, LogLevel.NOTSET, LogLevel.ERROR, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR}),
    (False, LogLevel.NOTSET, LogLevel.WARNING, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING}),
    (False, LogLevel.NOTSET, LogLevel.INFO, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO}),
    (False, LogLevel.NOTSET, LogLevel.DEBUG, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.CRITICAL, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.ERROR, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.WARNING, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.INFO, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.DEBUG, None, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.NOTSET, LogLevel.CRITICAL, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.NOTSET, LogLevel.ERROR, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.NOTSET, LogLevel.WARNING, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.NOTSET, LogLevel.INFO, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
    (True, LogLevel.NOTSET, LogLevel.DEBUG, {LogLevel.NOTSET, LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.DEBUG}),
])
def test_model_available_logger_levels_limited_by_logger(modify_loggers, root_level, selected_level, expected_available_levels):
    if root_level is not None:
        logging.getLogger().setLevel(root_level.value)
    logger = logging.getLogger("test_logger")
    logger.setLevel(selected_level.value)
    model = LogConsoleModel(loggers={logger}, level_changes_modify_loggers=modify_loggers)
    assert model.available_logger_levels == {"test_logger": expected_available_levels}


@pytest.mark.parametrize("is_frozen,expected_records", [
    (True, ["before frozen msg"]),
    (False, ["before frozen msg", "at frozen msg"]),
])
def test_model_all_records_taken_from_correct_queue(is_frozen, expected_records):
    model = LogConsoleModel()
    logging.warning("before frozen msg")
    model.freeze()
    logging.warning("at frozen msg")
    if is_frozen:
        model.freeze()
    else:
        model.unfreeze()
    actual_messages = [rec.message for rec in model.all_records]
    assert actual_messages == expected_records


@pytest.mark.parametrize("tracked_loggers,used_loggers,expected_records", [
    ({"root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"root": LogLevel.ERROR}, ["test_logger"], []),
    ({"root": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"root": LogLevel.WARNING}, ["root"], ["root msg"]),
    ({"root": LogLevel.ERROR}, ["root"], []),
    ({"root": LogLevel.INFO}, ["root"], ["root msg"]),
    ({}, ["test_logger"], []),
    ({}, ["root"], []),
    ({"test_logger": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING}, ["test_logger"], []),
    ({"test_logger.sublogger": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger.sublogger": LogLevel.INFO}, ["test_logger"], []),
    ({"test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger.sublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger.sublogger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger"], []),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.INFO}, ["test_logger"], []),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.INFO}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.INFO, "test_logger.sublogger": LogLevel.INFO}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger"], ["test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger"], ["test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.WARNING, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "test_logger.sublogger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger.sublogger.subsublogger"], ["test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING}, ["test_logger_not_quite"], []),
    ({"test_logger": LogLevel.ERROR}, ["test_logger_not_quite"], []),
    ({"test_logger": LogLevel.INFO}, ["test_logger_not_quite"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger_not_quite"], ["test_logger_not_quite msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger_not_quite"], ["test_logger_not_quite msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger_not_quite"], ["test_logger_not_quite msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger_not_quite"], []),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger_not_quite"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger_not_quite"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger_not_quite"], ["test_logger_not_quite msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger_not_quite"], ["test_logger_not_quite msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger_not_quite"], ["test_logger_not_quite msg"]),
    ({"test_logger": LogLevel.WARNING}, ["test_logger_not_quite.sublogger"], []),
    ({"test_logger": LogLevel.ERROR}, ["test_logger_not_quite.sublogger"], []),
    ({"test_logger": LogLevel.INFO}, ["test_logger_not_quite.sublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger_not_quite.sublogger"], ["test_logger_not_quite.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger_not_quite.sublogger"], ["test_logger_not_quite.sublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger_not_quite.sublogger"], ["test_logger_not_quite.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger_not_quite.sublogger"], []),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger_not_quite.sublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger_not_quite.sublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger_not_quite.sublogger"], ["test_logger_not_quite.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger_not_quite.sublogger"], ["test_logger_not_quite.sublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger_not_quite.sublogger"], ["test_logger_not_quite.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING}, ["test_logger_not_quite.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.ERROR}, ["test_logger_not_quite.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO}, ["test_logger_not_quite.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["test_logger_not_quite.sublogger.subsublogger"], ["test_logger_not_quite.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["test_logger_not_quite.sublogger.subsublogger"], ["test_logger_not_quite.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["test_logger_not_quite.sublogger.subsublogger"], ["test_logger_not_quite.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["test_logger_not_quite.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["test_logger_not_quite.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["test_logger_not_quite.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["test_logger_not_quite.sublogger.subsublogger"], ["test_logger_not_quite.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["test_logger_not_quite.sublogger.subsublogger"], ["test_logger_not_quite.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["test_logger_not_quite.sublogger.subsublogger"], ["test_logger_not_quite.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING}, ["not_test_logger"], []),
    ({"test_logger": LogLevel.ERROR}, ["not_test_logger"], []),
    ({"test_logger": LogLevel.INFO}, ["not_test_logger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["not_test_logger"], ["not_test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["not_test_logger"], ["not_test_logger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["not_test_logger"], ["not_test_logger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["not_test_logger"], []),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["not_test_logger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["not_test_logger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["not_test_logger"], ["not_test_logger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["not_test_logger"], ["not_test_logger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["not_test_logger"], ["not_test_logger msg"]),
    ({"test_logger": LogLevel.WARNING}, ["not_test_logger.sublogger"], []),
    ({"test_logger": LogLevel.ERROR}, ["not_test_logger.sublogger"], []),
    ({"test_logger": LogLevel.INFO}, ["not_test_logger.sublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["not_test_logger.sublogger"], ["not_test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["not_test_logger.sublogger"], ["not_test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["not_test_logger.sublogger"], ["not_test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["not_test_logger.sublogger"], []),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["not_test_logger.sublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["not_test_logger.sublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["not_test_logger.sublogger"], ["not_test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["not_test_logger.sublogger"], ["not_test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["not_test_logger.sublogger"], ["not_test_logger.sublogger msg"]),
    ({"test_logger": LogLevel.WARNING}, ["not_test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.ERROR}, ["not_test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO}, ["not_test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.WARNING}, ["not_test_logger.sublogger.subsublogger"], ["not_test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.WARNING}, ["not_test_logger.sublogger.subsublogger"], ["not_test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.WARNING}, ["not_test_logger.sublogger.subsublogger"], ["not_test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.ERROR}, ["not_test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.ERROR}, ["not_test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.ERROR}, ["not_test_logger.sublogger.subsublogger"], []),
    ({"test_logger": LogLevel.WARNING, "root": LogLevel.INFO}, ["not_test_logger.sublogger.subsublogger"], ["not_test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.ERROR, "root": LogLevel.INFO}, ["not_test_logger.sublogger.subsublogger"], ["not_test_logger.sublogger.subsublogger msg"]),
    ({"test_logger": LogLevel.INFO, "root": LogLevel.INFO}, ["not_test_logger.sublogger.subsublogger"], ["not_test_logger.sublogger.subsublogger msg"]),
])
def test_model_all_records_taken_from_correct_handler(tracked_loggers, used_loggers, expected_records):
    loggers = set()
    for logger_name, level in tracked_loggers.items():
        logger = logging.getLogger() if logger_name == "root" else logging.getLogger(logger_name)
        logger.setLevel(level.value)
        loggers.add(logger)

    model = LogConsoleModel(loggers=loggers)
    for logger_name in used_loggers:
        log = logging.getLogger() if logger_name == "root" else logging.getLogger(logger_name)
        log.warning(f"{logger_name} msg")

    actual_messages = [rec.message for rec in model.all_records]
    assert actual_messages == expected_records


@pytest.mark.parametrize("unfrozen_msg_count", [0, 1, 3])
@pytest.mark.parametrize("frozen_msg_count", [0, 1, 3])
@pytest.mark.parametrize("frozen_while_cleaning", [True, False])
@pytest.mark.parametrize("frozen_while_checking", [True, False])
def test_model_clear(unfrozen_msg_count, frozen_msg_count, frozen_while_cleaning, frozen_while_checking):
    model = LogConsoleModel()
    for i in range(unfrozen_msg_count):
        logging.warning(f"Unfrozen msg {i}")
    model.freeze()
    for i in range(frozen_msg_count):
        logging.warning(f"Frozen msg {i}")
    if frozen_while_cleaning:
        model.freeze()
    else:
        model.unfreeze()
    model.clear()
    if frozen_while_checking:
        model.freeze()
    else:
        model.unfreeze()
    assert len(list(model.all_records)) == 0


def test_model_buffer_size_corresponds_to_rt_queue():
    model = LogConsoleModel()
    assert model.buffer_size != 5
    assert model.buffer_size == model._rt_queue.maxlen
    model.buffer_size = 5
    assert model.buffer_size == model._rt_queue.maxlen


def test_model_buffer_size_never_none():
    model = LogConsoleModel(buffer_size=None)
    assert model.buffer_size == 0
    assert model._rt_queue.maxlen is None


@pytest.mark.parametrize("set_at_init", [True, False])
def test_model_set_buffer_size_does_nothing_on_the_same_val(set_at_init):
    if set_at_init:
        model = LogConsoleModel(buffer_size=5)
    else:
        model = LogConsoleModel()
        model.buffer_size = 5

    assert model._rt_queue.maxlen == 5
    orig_addr = id(model._rt_queue)
    model.buffer_size = 5
    assert id(model._rt_queue) == orig_addr
    assert model._rt_queue.maxlen == 5


@pytest.mark.parametrize("initial_size,initial_records,new_size,new_records", [
    (2, [], 1, []),
    (2, [], 3, []),
    (2, ["msg1"], 1, ["msg1"]),
    (2, ["msg1"], 3, ["msg1"]),
    (2, ["msg1", "msg2"], 1, ["msg2"]),
    (2, ["msg1", "msg2"], 3, ["msg1", "msg2"]),
])
@pytest.mark.parametrize("set_at_init", [True, False])
def test_model_set_buffer_size_creates_new_queue(set_at_init, initial_size, initial_records, new_size, new_records):
    if set_at_init:
        model = LogConsoleModel(buffer_size=initial_size)
    else:
        model = LogConsoleModel()
        model.buffer_size = initial_size

    for rec in initial_records:
        logging.warning(rec)

    assert [rec.message for rec in model.all_records] == initial_records
    assert model._rt_queue.maxlen == initial_size
    orig_addr = id(model._rt_queue)
    model.buffer_size = new_size
    assert id(model._rt_queue) != orig_addr
    assert model._rt_queue.maxlen == new_size
    assert [rec.message for rec in model.all_records] == new_records


def test_model_freeze_does_nothing_if_already_frozen(qtbot: QtBot):
    model = LogConsoleModel()
    logging.warning("Frozen msg")
    assert not model.frozen
    with qtbot.wait_signal(model.freeze_changed):
        model.freeze()
    assert model.frozen
    assert [rec.message for rec in model.all_records] == ["Frozen msg"]
    with qtbot.assert_not_emitted(model.freeze_changed):
        model.freeze()
    assert model.frozen

    # Check the frozen queue has not been cleared
    assert [rec.message for rec in model.all_records] == ["Frozen msg"]


def test_model_freeze_freezes_handlers():
    logger = logging.getLogger()
    logger2 = logging.getLogger("test_logger")
    orig_handler_count = len(logger.handlers)
    orig_handler_count2 = len(logger2.handlers)
    model = LogConsoleModel(loggers={logger, logger2})
    assert len(logger.handlers) == orig_handler_count + 1
    assert len(logger2.handlers) == orig_handler_count2 + 1
    assert isinstance(logger.handlers[-1], PythonLoggingHandler)
    assert isinstance(logger2.handlers[-1], PythonLoggingHandler)
    handler1 = cast(PythonLoggingHandler, logger.handlers[-1])
    handler2 = cast(PythonLoggingHandler, logger2.handlers[-1])
    assert not handler1.frozen
    assert not handler2.frozen
    model.freeze()
    assert handler1.frozen
    assert handler2.frozen


@pytest.mark.parametrize("initial_frozen_contents,initial_rt_contents,expected_frozen_contents", [
    (["msg1"], ["msg2", "msg3"], ["msg2", "msg3"]),
    (["msg1", "msg2"], ["msg3"], ["msg3"]),
    (["msg1", "msg2"], ["msg2", "msg3"], ["msg2", "msg3"]),
    ([], ["msg2", "msg3"], ["msg2", "msg3"]),
    ([], ["msg3"], ["msg3"]),
    ([], ["msg2", "msg3"], ["msg2", "msg3"]),
    (["msg1"], [], []),
    (["msg1", "msg2"], [], []),
    (["msg1", "msg2"], [], []),
])
def test_model_freeze_moves_queues(initial_frozen_contents, initial_rt_contents, expected_frozen_contents):

    def msg_to_record(msg: str) -> LogConsoleRecord:
        return LogConsoleRecord(message=msg, logger_name="", level=LogLevel.DEBUG, timestamp=0)

    model = LogConsoleModel()
    model._rt_queue.extend([msg_to_record(msg) for msg in initial_rt_contents])
    model._frozen_queue.extend([msg_to_record(msg) for msg in initial_frozen_contents])
    model.freeze()
    assert [rec.message for rec in model._frozen_queue] == expected_frozen_contents


def test_model_freeze_emits_signal(qtbot: QtBot):
    model = LogConsoleModel()
    with qtbot.wait_signal(model.freeze_changed) as blocker:
        model.freeze()
    assert blocker.args == [True]


def test_model_unfreeze_does_nothing_if_already_unfrozen(qtbot: QtBot):
    model = LogConsoleModel()
    assert not model.frozen
    model.freeze()
    assert model.frozen
    with qtbot.wait_signal(model.freeze_changed):
        model.unfreeze()
    assert not model.frozen
    with qtbot.assert_not_emitted(model.freeze_changed):
        model.unfreeze()
    assert not model.frozen


def test_model_unfreeze_unfreezes_handlers():
    logger = logging.getLogger()
    logger2 = logging.getLogger("test_logger")
    orig_handler_count = len(logger.handlers)
    orig_handler_count2 = len(logger2.handlers)
    model = LogConsoleModel(loggers={logger, logger2})
    assert len(logger.handlers) == orig_handler_count + 1
    assert len(logger2.handlers) == orig_handler_count2 + 1
    assert isinstance(logger.handlers[-1], PythonLoggingHandler)
    assert isinstance(logger2.handlers[-1], PythonLoggingHandler)
    handler1 = cast(PythonLoggingHandler, logger.handlers[-1])
    handler2 = cast(PythonLoggingHandler, logger2.handlers[-1])
    model.freeze()
    assert handler1.frozen
    assert handler2.frozen
    model.unfreeze()
    assert not handler1.frozen
    assert not handler2.frozen


def test_model_unfreeze_emits_signal(qtbot: QtBot):
    model = LogConsoleModel()
    model.freeze()
    with qtbot.wait_signal(model.freeze_changed) as blocker:
        model.unfreeze()
    assert blocker.args == [False]


def test_model_frozen_prop():
    model = LogConsoleModel()
    assert not model.frozen
    model.freeze()
    assert model.frozen
    model.unfreeze()
    assert not model.frozen


@pytest.mark.parametrize("modify_loggers,new_levels,expected_logger1_level,expected_handler1_level,expected_logger2_level,expected_handler2_level", [
    (True, {"logger1": LogLevel.ERROR, "logger2": LogLevel.CRITICAL}, logging.ERROR, logging.ERROR, logging.CRITICAL, logging.CRITICAL),
    (False, {"logger1": LogLevel.ERROR, "logger2": LogLevel.CRITICAL}, logging.INFO, logging.ERROR, logging.ERROR, logging.CRITICAL),
])
def test_model_selected_logger_levels_correspond_to_handler_or_logger_levels(modify_loggers, new_levels, expected_handler1_level,
                                                                             expected_handler2_level, expected_logger1_level,
                                                                             expected_logger2_level):
    logger1 = logging.getLogger("logger1")
    logger1.setLevel(logging.INFO)
    logger2 = logging.getLogger("logger2")
    logger2.setLevel(logging.ERROR)
    model = LogConsoleModel(level_changes_modify_loggers=modify_loggers, loggers={logger1, logger2})
    assert logger1.level == logging.INFO
    assert logger1.handlers[-1].level == logging.INFO
    assert logger2.level == logging.ERROR
    assert logger2.handlers[-1].level == logging.ERROR
    assert model.selected_logger_levels == {
        "logger1": LogLevel.INFO,
        "logger2": LogLevel.ERROR,
    }
    model.selected_logger_levels = new_levels
    assert model.selected_logger_levels == new_levels
    assert logger1.level == expected_logger1_level
    assert logger1.handlers[-1].level == expected_handler1_level
    assert logger2.level == expected_logger2_level
    assert logger2.handlers[-1].level == expected_handler2_level


def test_model_set_visible_levels_updates_handlers():
    model = LogConsoleModel()
    assert isinstance(logging.getLogger().handlers[-1], PythonLoggingHandler)
    handler = cast(PythonLoggingHandler, logging.getLogger().handlers[-1])
    assert handler._visible_levels == {"CRITICAL", "ERROR", "WARNING", "INFO"}
    model.visible_levels = {
        LogLevel.DEBUG,
        LogLevel.ERROR,
    }
    assert handler._visible_levels == {"ERROR", "DEBUG"}


@pytest.mark.parametrize("modify_loggers,expected_message,expect_highlight", [
    (True, "Attention! This modifies application-wide logging, which has effect beyond the log console.", True),
    (False, "Note: These levels control the records captured by the log console and do not affect application-wide logging.", False),
])
def test_model_level_notice(modify_loggers, expected_message, expect_highlight):
    model = LogConsoleModel(level_changes_modify_loggers=modify_loggers)
    actual_message, actual_highlight = model.level_notice
    assert actual_message == expected_message
    assert actual_highlight == expect_highlight


@pytest.mark.parametrize("orig_name,expected_logger_name", [
    ("test_logger", "test_logger"),
    ("root", "root"),
])
@pytest.mark.parametrize("orig_message,expected_message", [
    ("Test message", "Test message"),
    ("", ""),
])
@pytest.mark.parametrize("orig_level,expected_level", [
    (logging.NOTSET, LogLevel.NOTSET),
    (logging.DEBUG, LogLevel.DEBUG),
    (logging.WARNING, LogLevel.WARNING),
    (logging.ERROR, LogLevel.ERROR),
    (logging.CRITICAL, LogLevel.CRITICAL),
    (logging.INFO, LogLevel.INFO),
])
@pytest.mark.parametrize("pathname", [
    "/path/to/file.py",
    "",
])
@pytest.mark.parametrize("lineno", [-1, 0, 1])
@pytest.mark.parametrize("exc_info", [{}, None])
@pytest.mark.parametrize("args", [None, [], [1]])
@pytest.mark.parametrize("func", [None, "", "function_name"])
@freeze_time(STATIC_TIME)
def test_transform_record(orig_level, orig_message, orig_name, expected_level, expected_logger_name, expected_message,
                          pathname, lineno, args, func, exc_info):
    record = logging.LogRecord(name=orig_name,
                               level=orig_level,
                               pathname=pathname,
                               lineno=lineno,
                               msg=orig_message,
                               args=args,
                               exc_info=exc_info,
                               func=func)
    output = _record_from_python_logging_record(record)
    assert output.message == expected_message
    assert output.logger_name == expected_logger_name
    assert output.level == expected_level
    assert output.timestamp == 1577853785.214923
    assert round(output.millis, 3) == 214.923


@pytest.mark.parametrize("frozen,logger_level,should_emit", [
    (True, LogLevel.DEBUG, False),
    (True, LogLevel.WARNING, False),
    (True, LogLevel.ERROR, False),
    (True, LogLevel.INFO, False),
    (True, LogLevel.CRITICAL, False),
    (True, LogLevel.NOTSET, False),
    (False, LogLevel.DEBUG, True),
    (False, LogLevel.WARNING, True),
    (False, LogLevel.ERROR, False),
    (False, LogLevel.INFO, True),
    (False, LogLevel.CRITICAL, False),
    (False, LogLevel.NOTSET, True),
])
def test_model_on_new_record_emits_signal(qtbot: QtBot, frozen, should_emit, logger_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    model = LogConsoleModel(loggers={logger})
    model.selected_logger_levels = {
        "root": logger_level,
    }
    if frozen:
        model.freeze()
    if should_emit:
        with qtbot.wait_signal(model.new_log_record_received) as blocker:
            logging.warning("test message")
        assert len(blocker.args) == 2
        assert blocker.args[0].message == "test message"
        assert blocker.args[0].level == LogLevel.WARNING
    else:
        with qtbot.assert_not_emitted(model.new_log_record_received):
            logging.warning("test message")


@pytest.mark.parametrize("buffer_size,emitted_messages,signal_args", [
    (2, ["msg1"], [("msg1", False)]),
    (1, ["msg1"], [("msg1", False)]),
    (2, ["msg1", "msg2"], [("msg1", False), ("msg2", False)]),
    (1, ["msg1", "msg2"], [("msg1", False), ("msg2", True)]),
])
def test_model_on_new_record_signal_indicates_overflow(qtbot: QtBot, buffer_size, emitted_messages, signal_args):
    model = LogConsoleModel(buffer_size=buffer_size)
    for msg, expected_signal_args in zip(emitted_messages, signal_args):
        expected_msg, expected_overflow = expected_signal_args
        with qtbot.wait_signal(model.new_log_record_received) as blocker:
            logging.warning(msg)
        assert len(blocker.args) == 2
        assert blocker.args[0].message == expected_msg
        assert blocker.args[1] == expected_overflow


def test_model_get_logger_without_args():
    logger = logging.getLogger()
    assert logger.name == "root"
    assert isinstance(logger, logging.RootLogger)


@pytest.mark.parametrize("logger_name,expected_name,expected_type", [
    (None, "root", logging.RootLogger),
    ("", "root", logging.RootLogger),
    ("root", "root", logging.RootLogger),
    ("test_logger", "test_logger", logging.Logger),
])
def test_model_get_logger_with_args(logger_name, expected_name, expected_type):
    logger = _get_logger(logger_name)
    assert logger.name == expected_name
    assert type(logger) == expected_type


def test_log_messages_get_ignored_of_not_tracked_logger(qtbot: QtBot):
    logger1 = logging.getLogger("logger1")
    logger1.setLevel(logging.WARNING)
    logger2 = logging.getLogger("logger2")
    logger2.setLevel(logging.WARNING)
    model = LogConsoleModel(loggers={logger1})
    assert logger1.level == logger2.level
    with qtbot.wait_signal(model.new_log_record_received) as blocker:
        logger1.warning("test1")
    assert blocker.args[0].message == "test1"
    with qtbot.assert_not_emitted(model.new_log_record_received):
        logger2.warning("test2")
