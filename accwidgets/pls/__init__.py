"""
This component allows discovering available selectors (i.e. timing users) from CCDB. It is possible to embed the
widget directly or use an auxiliary :class:`QDialog` or :class:`QAction` that render the widget in a respective manner.
"""
# flake8: noqa: F401
from accwidgets._api import assert_dependencies as _assert_dependencies
_assert_dependencies(__file__)


from ._model import PlsSelectorModel, PlsSelectorConnectionError


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(PlsSelectorConnectionError, __name__)
_mark_public_api(PlsSelectorModel, __name__)
