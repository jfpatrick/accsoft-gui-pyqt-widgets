"""
Module containing QtDesigner plugin for LED widget.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


skip_plugin = False
try:
    with disable_assert_cache():
        from accwidgets.led import Led
except ImportError:
    skip_plugin = True


if not skip_plugin:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    LedPlugin = create_plugin(widget_class=Led,
                              group=WidgetBoxGroup.INDICATORS,
                              icon_base_path=_ICON_BASE_PATH)
