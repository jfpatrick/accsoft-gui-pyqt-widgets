import pytest
from typing import Union
from enum import Enum
from pylogbook import NamedActivity
from pylogbook.models import Activity
from accwidgets.screenshot import LogbookModel
from accwidgets.screenshot._common import make_activities_summary
from .fixtures import *  # noqa: F401,F403


@pytest.mark.parametrize("activities,expected_result", [
    ((), ""),
    (("TEST1",), "TEST1"),
    (("TEST1", "TEST2"), "TEST1/TEST2"),
    ((NamedActivity.LHC,), "LHC"),
    ((NamedActivity.LHC, NamedActivity.LINAC4, "TEST1"), "LHC/LINAC 4/TEST1"),
])
def test_make_activities_summary(activities, expected_result, logbook):

    def convert(val: Union[str, Enum]):
        return Activity(activity_id=0, name=val if isinstance(val, str) else val.value)

    _, activities_client = logbook
    activities_client.activities = tuple(map(convert, activities))
    model = LogbookModel(logbook=logbook)
    res = make_activities_summary(model)
    assert res == expected_result
