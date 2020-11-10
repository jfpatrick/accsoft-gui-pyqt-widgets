# flake8: noqa: F401

from .led import Led


from accwidgets._api import mark_public_api as _mark_public_api
_mark_public_api(Led, __name__)
