import pytest
from accwidgets.cycle_selector import CycleSelectorValue


@pytest.mark.parametrize("val,expected_str", [
    (CycleSelectorValue(domain="LHC", group="USER", line="ALL"), "LHC.USER.ALL"),
    (CycleSelectorValue(domain="SPS", group="PARTY", line="ION"), "SPS.PARTY.ION"),
    (CycleSelectorValue(domain="LHC", group="", line="LHC"), "LHC..LHC"),  # This is not valid
])
def test_str(val, expected_str):
    assert str(val) == expected_str
