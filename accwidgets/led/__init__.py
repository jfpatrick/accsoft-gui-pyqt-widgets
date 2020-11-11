# flake8: noqa: F401

from accwidgets._api import assert_dependencies as _assert_dependencies
_assert_dependencies(__file__)


from .led import Led


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(Led, __name__)
