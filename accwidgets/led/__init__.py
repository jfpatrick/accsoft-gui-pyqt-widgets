# flake8: noqa: F401

from .led import Led


from accwidgets._api import mark_public_api
mark_public_api(Led, __name__)
