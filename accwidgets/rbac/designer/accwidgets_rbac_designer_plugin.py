"""
Module containing QtDesigner plugin for RBAC widget.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


skip_plugin = False
try:
    with disable_assert_cache():
        from accwidgets.rbac import RbaButton
except ImportError:
    skip_plugin = True


if not skip_plugin:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    RbaButtonPlugin = create_plugin(widget_class=RbaButton,
                                    group=WidgetBoxGroup.BUTTONS,
                                    icon_base_path=_ICON_BASE_PATH)
