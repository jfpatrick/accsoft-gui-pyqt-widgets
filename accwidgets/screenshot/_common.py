import operator
from typing import Union, Iterable
from qtpy.QtWidgets import QWidget
from ._model import LogbookModel


def make_activities_summary(model: LogbookModel) -> str:
    return "/".join(map(operator.attrgetter("name"), model.logbook_activities))


def make_new_entry_tooltip(model: LogbookModel) -> str:
    activities_summary = make_activities_summary(model)
    return f"Capture screenshot to a new entry in <i>{activities_summary}</i> e-logbook"


ScreenshotSource = Union[QWidget, Iterable[QWidget]]
"""Alias for the possible types of the widgets that can be captured in a screenshot."""
