"""
This component provides a dialog to select a parameter name ("device/property" or "device/property#field")
from CCDB. This dialog is accessible via multiple ways and helper widgets.
"""
# flake8: noqa: F401
from accwidgets._api import assert_dependencies as _assert_dependencies
_assert_dependencies(__file__)


from ._line_edit import ParameterLineEdit, ParameterLineEditColumnDelegate
from ._dialog import ParameterSelectorDialog


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(ParameterSelectorDialog, __name__)
_mark_public_api(ParameterLineEdit, __name__)
_mark_public_api(ParameterLineEditColumnDelegate, __name__)
