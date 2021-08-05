import pytest
from accwidgets.parameter_selector._model import get_ccda


def test_get_ccda_is_singleton():
    obj1 = get_ccda()
    obj2 = get_ccda()
    assert obj1 is obj2
