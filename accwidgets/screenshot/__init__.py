"""
:class:`ScreenshotButton` allows uploading an application screenshot to the e-logbook.
"""
# flake8: noqa: F401
from accwidgets._api import assert_dependencies as _assert_dependencies
_assert_dependencies(__file__)

from ._widget import LogbookButton


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(LogbookButton, __name__)
