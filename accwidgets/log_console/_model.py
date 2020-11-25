import logging
import functools
import operator
from typing import Optional, Dict, Set, Deque, Union, Iterator, Iterable, List, Tuple
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from collections import deque, OrderedDict
from qtpy.QtCore import QObject, Signal
from accwidgets.qt import AbstractQObjectMeta
from ._config import LogLevel


@dataclass(frozen=True)
class LogConsoleRecord:
    """
    Record representing a single logging event. It is abstracted from Python :mod:`logging` (to allow
    alternative implementations of models that are not tied to Python :mod:`logging`) but has all
    essential fields required by :class:`logging.LogRecord`.
    """
    logger_name: str
    """Name of the logger that produced the record."""

    message: str
    """Contents of the log message."""

    level: LogLevel
    """Severity level."""

    timestamp: float
    """Unix epoch timestamp of the message creation."""

    millis: int = 0
    """Milliseconds of the timestamp, complimentary to :attr:`timestamp`."""


class AbstractLogConsoleModel(QObject, metaclass=AbstractQObjectMeta):
    """Base class for the models used with :class:`LogConsole` widget."""

    freeze_changed = Signal(bool)
    """Signal emitted when :attr:`frozen` value changes. The argument is the new value of the attribute."""

    new_log_record_received = Signal(LogConsoleRecord, bool)
    """
    Signal emitted when a new record is available in the model's buffer.

    - First argument is a new record
    - Second argument if the buffer was full, so that earliest records should be popped from the view.
    """

    @property
    @abstractmethod
    def all_records(self) -> Iterator[LogConsoleRecord]:
        """Property allowing to iterate through all the log records in the buffer lazily."""
        pass

    @abstractmethod
    def clear(self):
        """Clear the internal buffers of any log records."""
        pass

    @abstractmethod
    def freeze(self):
        """
        Freeze the model. Frozen model should not emit a :attr:`new_log_record_received` signal, while
        still accumulating incoming log records, so that they can be displayed after :meth:`unfreeze`
        is called.

        This call should influence the return value of :attr:`frozen` and emit :attr:`freeze_changed` if the
        value has changed.
        """
        pass

    @abstractmethod
    def unfreeze(self):
        """
        Undo the effects produced in :meth:`freeze`.

        This call should influence the return value of :attr:`frozen` and emit :attr:`freeze_changed` if the
        value has changed.
        """
        pass

    @property
    @abstractmethod
    def frozen(self) -> bool:
        """Represents the current state of a "frozen" model. Frozen model should not emit a
        :attr:`new_log_record_received` signal, while still accumulating incoming log records, so that they
        can be displayed after :meth:`unfreeze` is called."""
        pass

    @property  # type: ignore
    @abstractmethod
    def buffer_size(self) -> int:
        """
        Amount of log records that can be stored by the internal buffer.

        This number can be configured by the user from the "Preferences" dialog, thus the model should allow
        dynamic size change. Depending on the buffer type, buffer can behave differently when it gets full.
        E.g., for queue (FIFO) buffers, new log records cause removal of the oldest log records."""
        pass

    @buffer_size.setter  # type: ignore
    @abstractmethod
    def buffer_size(self, new_val: int):
        pass

    @property  # type: ignore
    @abstractmethod
    def visible_levels(self) -> Set[LogLevel]:
        """
        Subset of real severity levels (as provided by :meth:`LogLevel.real_levels`), that should be displayed
        in the console.

        This setting can be configured by the user from the "Preferences" dialog, thus the model should allow
        dynamic change. Log records that have currently invisible levels should still be stored in the buffer,
        as the setting can be changed, and they should appear in the console.
        """
        pass

    @visible_levels.setter  # type: ignore
    @abstractmethod
    def visible_levels(self, new_val: Set[LogLevel]):
        pass

    @property  # type: ignore
    @abstractmethod
    def selected_logger_levels(self) -> Dict[str, LogLevel]:
        """
        Dictionary mapping the logger name and the severity level that is currently selected for it.

        This setting can be configured by the user from the "Preferences" dialog, thus the model should allow
        dynamic change. In contrast to :attr:`visible_levels`, which only hide the log records, but do not remove
        them from the buffer, the logger levels actually influence what is captured in the first place. Thus,
        the log records that have lower severity than that of the selected level, should not be stored in the
        model's buffer.
        """
        pass

    @selected_logger_levels.setter  # type: ignore
    @abstractmethod
    def selected_logger_levels(self, new_val: Dict[str, LogLevel]):
        pass

    @property
    def available_logger_levels(self) -> Dict[str, Set[LogLevel]]:
        """
        Dictionary mapping the logger name and the levels available for user selection in "Preferences" dialog.

        Sometimes, it does not make sense to show all levels. For example, Python's :class:`~logging.Logger`
        can be configured to display only from a certain level. In this case, the handler that is created by the
        model will not receive any other messages, even if it has lower severity configured. To avoid the user
        confusion, model can choose to hide such levels altogether.

        The default implementation allows all levels to be selected.
        """
        return {logger_name: set(LogLevel) for logger_name in self.selected_logger_levels.keys()}

    @property
    def level_notice(self) -> Optional[Tuple[str, bool]]:
        """
        If relevant, return a message that will be placed in the bottom of logger level configuration, just
        for user information.

        Returns:
            Tuple of the message contents and boolean flag indicating if the message should be warning
            (will have a highlighted color), otherwise :obj:`False` for regular information.
        """
        return None


class LogConsoleModel(AbstractLogConsoleModel):

    def __init__(self,
                 buffer_size: int = 1000,
                 visible_levels: Optional[Set[LogLevel]] = None,
                 loggers: Optional[Iterable[logging.Logger]] = None,
                 parent: Optional[QObject] = None,
                 level_changes_modify_loggers: bool = False):
        """
        Default model implementation that is used by :class:`LogConsole`.

        This model works with Python loggers (:class:`logging.Logger`) to collect log records.
        By default it is non-invasive, meaning that any severity level change that is configured by
        the user in the "Preferences" dialog, is not affecting actual loggers, but changes the
        level of the related handlers that are created by the logger. This behavior can be changed by
        setting ``level_changes_modify_loggers`` argument to :obj:`True`.

        This implementation maintains 2 queues:

            - Real-time queue, that accumulates incoming messages (even when model is "frozen").
            - Frozen queue, that gets populated when the user "freezes" the console. It exists separately,
              so that any changes in the "Preferences" dialog do not re-render the new messages, but keep
              displaying frozen messages. This queue gets purged when the user "unfreezes" the console.

        Args:
            buffer_size: Default buffer size of the real-time message queue.
            visible_levels: Default visible severity levels. If omitted, :attr:`~LogLevel.INFO` and above will
                            be configured for display.
            loggers: Python loggers that should be captured (and thus configurable) by the console. If omitted,
                     the root Python logger is attached to, which should cover all messages from the Python code.
            parent: Owning object.
            level_changes_modify_loggers: Whenever user configures the severity levels in the "Preferences" dialog,
                                          change the levels on the actual :class:`~logging.Logger` objects (when
                                          set to :obj:`True`), which affects the logging behavior of the entire
                                          application. This flag is disabled by default to have non-invasive behavior.
        """
        super().__init__(parent)
        self._rt_queue: Deque[logging.LogRecord] = deque(maxlen=buffer_size)
        self._frozen_queue: List[logging.LogRecord] = []
        self._frozen: bool = False
        loggers_list = list(set(loggers)) if loggers is not None else [_get_logger()]
        self._handlers: OrderedDict[str, PythonLoggingHandler] = OrderedDict()
        self._level_changes_modify_loggers = level_changes_modify_loggers
        self._visible_levels = visible_levels if visible_levels is not None else {LogLevel.INFO,
                                                                                  LogLevel.WARNING,
                                                                                  LogLevel.ERROR,
                                                                                  LogLevel.CRITICAL}

        # Order here is important to keep longer names in the front, so that when we iterate through handlers
        # in all_records, more specific sub-handlers get a match before the parent handlers.
        loggers_list = sorted(loggers_list, key=operator.attrgetter("name"), reverse=True)
        all_handler_names = [logger.name for logger in loggers_list]

        for logger in loggers_list:
            handler = PythonLoggingHandler(parent=self,
                                           name=logger.name,
                                           frozen=self._frozen,
                                           level=logger.level,
                                           all_handler_names=all_handler_names,
                                           visible_levels=self._visible_levels)
            handler.new_message_received.connect(self.__on_new_record_received)
            logger.addHandler(handler)
            self._handlers[logger.name] = handler

        self.destroyed.connect(functools.partial(_clean_up_model_before_delete, handlers=self._handlers))

    @property
    def all_records(self) -> Iterator[LogConsoleRecord]:
        active_queue = self._frozen_queue if self.frozen else self._rt_queue

        for record in active_queue:
            handler = self._handler_for_record(record)
            if handler and handler.filter_ignore_frozen(record):
                yield _record_from_python_logging_record(record)

    def clear(self):
        self._rt_queue.clear()
        self._frozen_queue.clear()

    @property
    def buffer_size(self) -> int:
        return self._rt_queue.maxlen or 0

    @buffer_size.setter
    def buffer_size(self, new_val: int):
        if new_val == self.buffer_size:
            return
        new_queue: Deque[logging.LogRecord] = deque(iterable=self._rt_queue, maxlen=new_val)
        self._rt_queue = new_queue

    def freeze(self):
        if self.frozen:
            return
        self._frozen = True
        for handler in self._handlers.values():
            handler.frozen = True
        self._frozen_queue.clear()
        self._frozen_queue.extend(self._rt_queue)
        self.freeze_changed.emit(self._frozen)

    def unfreeze(self):
        if not self.frozen:
            return
        self._frozen = False
        for handler in self._handlers.values():
            handler.frozen = False
        self._frozen_queue.clear()
        self.freeze_changed.emit(self._frozen)

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def selected_logger_levels(self) -> Dict[str, LogLevel]:
        return {logger_name: LogLevel(_get_logger(logger_name).level if self._level_changes_modify_loggers
                                      else self._handlers[logger_name].level)
                for logger_name in self._handlers.keys()}

    @selected_logger_levels.setter
    def selected_logger_levels(self, new_val: Dict[str, LogLevel]):
        for logger_name, logger_level in new_val.items():
            try:
                self._handlers[logger_name].setLevel(logger_level.value)
            except KeyError:
                continue
            if self._level_changes_modify_loggers:
                _get_logger(logger_name).setLevel(logger_level.value)

    @property
    def available_logger_levels(self) -> Dict[str, Set[LogLevel]]:
        if self._level_changes_modify_loggers:
            # When we act directly on loggers, give everything, because loggers can be adapted
            return super().available_logger_levels

        # Otherwise, offer levels, only that can be displayed, given the parent logger limitations
        res = {}
        for logger_name in self.selected_logger_levels.keys():
            lower_limit = _get_logger(logger_name).getEffectiveLevel()
            res[logger_name] = {level for level in LogLevel.real_levels() if level.value >= lower_limit}
            res[logger_name].add(LogLevel.NOTSET)  # Always allow NOTSET
        return res

    @property
    def visible_levels(self) -> Set[LogLevel]:
        return self._visible_levels

    @visible_levels.setter  # type: ignore
    def visible_levels(self, new_val: Set[LogLevel]):
        self._visible_levels = new_val
        for handler in self._handlers.values():
            handler.set_visible_levels(new_val)

    @property
    def level_notice(self) -> Optional[Tuple[str, bool]]:
        if self._level_changes_modify_loggers:
            return "Attention! This modifies application-wide logging, which has effect beyond the log console.", True
        return "Note: These levels control the records captured by the log console and do not affect " \
               "application-wide logging.", False

    @property
    def level_changes_modify_loggers(self) -> bool:
        return self._level_changes_modify_loggers

    def _handler_for_record(self, record: logging.LogRecord) -> Optional["PythonLoggingHandler"]:
        for handler_name, handler in self._handlers.items():
            if _record_name_can_be_handled(record_name=record.name, handler_name=handler_name):
                return handler

        # If no specific parent handler is found, try using the root handler (if was added to the model)
        # Otherwise, bail out.
        try:
            return self._handlers[_ROOT_LOGGER_NAME]
        except KeyError:
            return None

    def __on_new_record_received(self, record: logging.LogRecord, should_display: bool):
        # Queue was already full
        buffer_overflown = len(self._rt_queue) >= self.buffer_size
        self._rt_queue.append(record)
        if should_display and not self.frozen:
            self.new_log_record_received.emit(_record_from_python_logging_record(record), buffer_overflown)


def _clean_up_model_before_delete(handlers: Dict[str, "PythonLoggingHandler"]):
    # This has to be an independent method, not belonging to the model itself, because apparently
    # it's not getting called, when belonging to the model. We just preserve the list of handlers here
    # that can be cleaned up independently.

    try:
        # This avoids Python logger notifying handlers that have been deleted in deleted model
        for name, handler in handlers.items():
            logger = _get_logger(name)
            logger.removeHandler(handler)
    except Exception:
        # Avoid crashing at the clean-up phase for any reason
        pass


def _record_from_python_logging_record(input: logging.LogRecord) -> LogConsoleRecord:
    return LogConsoleRecord(logger_name=input.name,
                            message=input.getMessage(),
                            level=LogLevel[input.levelname],
                            timestamp=float(input.created),
                            millis=input.msecs)


class AbstractLoggerFilter(logging.Filter, metaclass=ABCMeta):

    def __init__(self, name: str, ignored_ids: List[str], can_handle_arbitrary_names: bool):
        super().__init__(name=name)
        self._ignored_ids = ignored_ids
        self._can_handle_arbitrary_names = can_handle_arbitrary_names

    def filter(self, record: logging.LogRecord) -> bool:
        for handler_name in self._ignored_ids:
            if _record_name_can_be_handled(record_name=record.name, handler_name=handler_name):
                return False
        return True if self._can_handle_arbitrary_names else bool(super().filter(record))


class RootLoggerFilter(AbstractLoggerFilter):

    def __init__(self, name: str, all_handler_names: List[str]):
        super().__init__(name=name,
                         ignored_ids=[handler_name for handler_name in all_handler_names if handler_name != _ROOT_LOGGER_NAME],
                         can_handle_arbitrary_names=True)


class LoggerFilter(AbstractLoggerFilter):

    def __init__(self, name: str, all_handler_names: List[str]):
        super().__init__(name=name,
                         ignored_ids=[handler_name for handler_name in all_handler_names
                                      if _logger_name_is_child_to(parent_name=name, child_name=handler_name)],
                         can_handle_arbitrary_names=False)


class PythonLoggingHandler(QObject, logging.Handler):

    new_message_received = Signal(logging.LogRecord, bool)
    """
    First argument is the actual message, that should be stored in the buffer.
    Second argument indicates whether this message should be displayed. (For the case when console is frozen,
    it must be stored but not display until explicitly fetched).
    """

    def __init__(self,
                 name: str,
                 frozen: bool,
                 visible_levels: Set[LogLevel],
                 all_handler_names: List[str],
                 parent: Optional[QObject] = None,
                 level: Union[LogLevel, int] = logging.NOTSET):
        QObject.__init__(self, parent)
        if isinstance(level, LogLevel):
            level = level.value
        logging.Handler.__init__(self, level=level)
        self.frozen = frozen
        self._filter: AbstractLoggerFilter = (RootLoggerFilter if name == _ROOT_LOGGER_NAME else LoggerFilter)(
            name=name,
            all_handler_names=all_handler_names,
        )
        self.addFilter(self._filter)
        self._visible_levels: Set[str] = set()
        self.set_visible_levels(visible_levels)

    def set_visible_levels(self, new_val: Set[LogLevel]):
        self._visible_levels = {LogLevel.level_name(level) for level in new_val}

    def emit(self, record: logging.LogRecord):
        should_display = not self.frozen and self.filter_ignore_frozen(record)
        self.new_message_received.emit(record, should_display)

    def filter_ignore_frozen(self, record: logging.LogRecord) -> bool:
        return record.levelname in self._visible_levels and self._filter.filter(record)


def _logger_name_is_child_to(parent_name: str, child_name: str) -> bool:
    # This is similar to how logging.Filter.filter works
    if child_name == parent_name:
        return False
    elif child_name.find(parent_name, 0, len(parent_name)) != 0:
        return False
    return child_name[len(parent_name)] == "."


def _record_name_can_be_handled(record_name: str, handler_name: str) -> bool:
    return record_name == handler_name or _logger_name_is_child_to(parent_name=handler_name,
                                                                   child_name=record_name)


def _get_logger(name: Optional[str] = None) -> logging.Logger:
    # This is a wrapper method, because if we request logging.getLogger("root"), we are not getting the
    # RootLogger instance, but rather a new Logger instance. It becomes confusing and out-of-sync.
    # e.g. when we want to access level, we may receive an unexpected value, because not a root logger is
    # actually being queried.
    if name is None or name == _ROOT_LOGGER_NAME:
        return logging.getLogger()
    return logging.getLogger(name)


_ROOT_LOGGER_NAME = "root"
