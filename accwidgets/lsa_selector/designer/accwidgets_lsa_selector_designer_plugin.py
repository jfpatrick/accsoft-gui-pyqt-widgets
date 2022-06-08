"""
Module containing QtDesigner plugin for LSA selector widget.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


try:
    with disable_assert_cache():
        from accwidgets.lsa_selector import LsaSelector
except ImportError:
    pass
else:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    LsaSelectorPlugin = create_plugin(widget_class=LsaSelector,
                                      group=WidgetBoxGroup.INPUTS,
                                      icon_base_path=_ICON_BASE_PATH)
