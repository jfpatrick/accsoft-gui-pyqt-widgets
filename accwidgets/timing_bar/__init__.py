"""
:class:`TimingBar` displays the currently played cycle in the supercycle view.
"""
# flake8: noqa: F401
from ._model import TimingBarModel, TimingBarDomain
from ._widget import TimingBar, TimingBarPalette


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(TimingBarModel, __name__)
_mark_public_api(TimingBarDomain, __name__)
_mark_public_api(TimingBar, __name__)
_mark_public_api(TimingBarPalette, __name__)
