import pytest
from typing import Dict
from accwidgets.log_console import AbstractLogConsoleFormatter, AbstractLogConsoleModel, LogConsoleRecord, LogLevel


@pytest.fixture
def custom_fmt_class():

    class TestFormatter(AbstractLogConsoleFormatter):

        def __init__(self, test_attr: bool, test_attr2: bool):
            super().__init__()
            self.test_attr = test_attr
            self.test_attr2 = test_attr2

        def format(self, record) -> str:
            res = "fixed string"
            if self.test_attr:
                res += "+1"
            if self.test_attr2:
                res += "+2"
            return res

        @classmethod
        def configurable_attributes(cls):
            return {
                "test_attr": "Attribute 1",
                "test_attr2": "Attribute 2",
            }

    return TestFormatter


@pytest.fixture
def custom_fmt_class_parametrized():

    def _wrapper(config: Dict[str, str]):

        class TestFormatter(AbstractLogConsoleFormatter):

            def __init__(self, **kwargs):
                super().__init__()
                for k, v in kwargs.items():
                    setattr(self, k, v)

            def format(self, record) -> str:
                return "fixed string"

            @classmethod
            def configurable_attributes(cls):
                return config

        return TestFormatter

    return _wrapper


@pytest.fixture
def custom_model_class():

    class TestModel(AbstractLogConsoleModel):

        def __init__(self, parent=None):
            super().__init__(parent)
            self._selected_levels = {}

        @property
        def all_records(self):
            yield LogConsoleRecord(logger_name="test_logger", message="test message", level=LogLevel.WARNING, timestamp=0)

        def clear(self):
            pass

        def freeze(self):
            pass

        def unfreeze(self):
            pass

        @property
        def frozen(self):
            return False

        @property
        def buffer_size(self):
            return 1

        @buffer_size.setter
        def buffer_size(self, _):
            pass

        @property
        def visible_levels(self):
            return set()

        @visible_levels.setter
        def visible_levels(self, _):
            pass

        @property
        def selected_logger_levels(self):
            return self._selected_levels

        @selected_logger_levels.setter
        def selected_logger_levels(self, new_val):
            self._selected_levels = new_val

    return TestModel
