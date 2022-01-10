"""
:class:`ScreenshotButton` widget (or its related :class:`ScreenshotAction` action ) allow uploading an
application screenshot to the e-logbook.
"""
# flake8: noqa: F401
from accwidgets._api import assert_dependencies as _assert_dependencies
_assert_dependencies(__file__)


from ._widget import ScreenshotButton
from ._action import ScreenshotAction
from ._common import ScreenshotSource
from ._model import LogbookModel


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(ScreenshotButton, __name__)
_mark_public_api(ScreenshotAction, __name__)
_mark_public_api(LogbookModel, __name__)
