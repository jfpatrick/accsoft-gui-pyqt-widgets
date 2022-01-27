from .fixtures import *  # noqa: F401,F403
import pytest
from typing import Union
from enum import Enum
from pylogbook import NamedActivity
from pylogbook.models import Activity
from accwidgets.screenshot._common import make_activities_summary, make_new_entry_tooltip


def make_activity(val: Union[str, Enum]):
    return Activity(activity_id=0, name=val if isinstance(val, str) else val.value)


@pytest.mark.parametrize("activities,expected_result", [
    ((), ""),
    (("TEST1",), "TEST1"),
    (("TEST1", "TEST2"), "TEST1/TEST2"),
    ((NamedActivity.LHC,), "LHC"),
    ((NamedActivity.LHC, NamedActivity.LINAC4, "TEST1"), "LHC/LINAC 4/TEST1"),
])
def test_make_activities_summary(activities, expected_result, logbook_model):
    logbook_model.logbook_activities = tuple(map(make_activity, activities))
    res = make_activities_summary(logbook_model)
    assert res == expected_result


@pytest.mark.parametrize("activities,expected_result", [
    ((), "Capture screenshot to a new entry in <i></i> e-logbook"),
    (("TEST1",), "Capture screenshot to a new entry in <i>TEST1</i> e-logbook"),
    (("TEST1", "TEST2"), "Capture screenshot to a new entry in <i>TEST1/TEST2</i> e-logbook"),
    ((NamedActivity.LHC,), "Capture screenshot to a new entry in <i>LHC</i> e-logbook"),
    ((NamedActivity.LHC, NamedActivity.LINAC4, "TEST1"), "Capture screenshot to a new entry in <i>LHC/LINAC 4/TEST1</i> e-logbook"),
])
def test_make_new_entry_tooltip(activities, expected_result, logbook_model):
    logbook_model.logbook_activities = tuple(map(make_activity, activities))
    res = make_new_entry_tooltip(logbook_model)
    assert res == expected_result
