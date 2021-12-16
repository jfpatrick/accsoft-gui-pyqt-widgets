import logging
from abc import abstractmethod, ABC
from typing import Optional, List, TypeVar, Dict
from ._model import LogConsoleRecord


_T = TypeVar("_T", bound="AbstractLogConsoleFormatter")


class AbstractLogConsoleFormatter(ABC):
    """
    Formatter is responsible for pre-formatting the log message and adding arbitrary auxiliary information to it,
    e.g. timestamps or logger names.

    This abstract class defines the skeleton for implementing custom formatters.

    Custom implementations must define arguments in the initializer that correspond to the list provided by
    :meth:`configurable_attributes` and their type must always be :obj:`bool`. Same attributes should be also
    public and accessible for reading, e.g.:

    1. Custom subclass' :meth:`configurable_attributes` returns ``{'custom_attr': 'Show custom attr'}``
    2. Custom subclass' ``__init__`` must have a signature ``def __init__(self, custom_attr: bool):``
    3. Custom subclass` must have either and attribute or a property with name ``custom_attr``
    """

    @abstractmethod
    def format(self, record: LogConsoleRecord) -> str:
        """
        Format the log record into the final string visible in the :class:`LogConsole` widget.

        Args:
            record: Log record.

        Returns:
            Human-readable log string.
        """
        pass

    @classmethod
    def create(cls, **kwargs) -> _T:
        """
        Factory method to create the formatter instance.

        The default implementation simply instantiates a new object, but it can be overridden for custom behaviors,
        e.g. if you decide to have a formatter singleton.

        Formatters are re-created many times at runtime (mainly because Python formatters of the default implementation
        cannot be reconfigured after the fact and their configuration is done in the initializer):

        - When user changes formatter settings in the "Preferences" dialog, to render a sample message
        - When user saves changes from the "Preferences" dialog, to re-render shown contents of the log console.

        Args:
            **kwargs: Arbitrary arguments that are passed to the initializer. Argument names must correspond to the
                      ones provided by :meth:`configurable_attributes` and their type must always be :obj:`bool`.
        """
        return cls(**kwargs)  # type: ignore

    @classmethod
    @abstractmethod
    def configurable_attributes(cls) -> Dict[str, str]:
        """
        Class method that returns attributes that can be configured in the "Preferences" dialog by the user.

        All of the attributes are assumed to be of the :obj:`bool` type, because user configuration is done via
        checkboxes.

        Returns:
            Dictionary, where keys are attribute names (that can be accessed for reading, and also passed as the
            initializer arguments). The corresponding values are human-readable strings that are displayed next to
            checkboxes in the "Preferences" dialog.
        """
        pass


class LogConsoleFormatter(AbstractLogConsoleFormatter):

    def __init__(self, show_date: bool = True, show_time: bool = True, show_logger_name: bool = True):
        """
        Implementation of the default formatter that makes use of standard Python
        :class:`logging.Formatter` instances.

        It is able to prefix log messages with the optional date, time and logger names.

        Args:
            show_date: Add date to the log message prefix.
            show_time: Add time to the log message prefix.
            show_logger_name: Add logger name to the log message prefix.
        """
        super().__init__()

        self.show_date = show_date
        self.show_time = show_time
        self.show_logger_name = show_logger_name

        components: List[str] = []
        date_format: Optional[str] = None
        if show_date and show_time:
            components.append("%(asctime)s")
        elif show_date and not show_time:
            components.append("%(asctime)s")
            date_format = "%Y-%m-%d"
        elif show_time and not show_date:
            components.append("%(asctime)s,%(msecs)03d")
            date_format = "%H:%M:%S"
        if show_logger_name:
            components.append("%(name)s")
        components.append("%(levelname)s")
        components.append("%(message)s")

        self._fmt = logging.Formatter(fmt=" - ".join(components), datefmt=date_format, style="%")

    def format(self, record: LogConsoleRecord) -> str:
        rec = logging.LogRecord(name=record.logger_name,
                                msg=record.message,
                                level=record.level.value,
                                pathname=getattr(record, "pathname", ""),
                                lineno=getattr(record, "lineno", 0),
                                args=getattr(record, "args", ()),
                                exc_info=getattr(record, "exc_info", None),
                                func=getattr(record, "funcName", None),
                                sinfo=getattr(record, "stack_info", None))
        rec.created = record.timestamp  # type: ignore  # mypy erroneusly thinks that 'created' is int
        rec.msecs = record.millis  # type: ignore  # mypy erroneusly thinks that 'msecs' is int

        return self._fmt.format(rec)

    @classmethod
    def configurable_attributes(cls) -> Dict[str, str]:
        return {
            "show_date": "Show date",
            "show_time": "Show time",
            "show_logger_name": "Show Logger name",
        }
