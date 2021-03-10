"""
Widget to handle user authentication and display information from RBAC token.
"""

# flake8: noqa: F401
from accwidgets._api import assert_dependencies as _assert_dependencies
_assert_dependencies(__file__)

from ._token import RbaToken, RbaRole
from ._model import RbaButtonModel
from ._widget import RbaButton


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(RbaToken, __name__)
_mark_public_api(RbaRole, __name__)
_mark_public_api(RbaButtonModel, __name__)
_mark_public_api(RbaButton, __name__)
