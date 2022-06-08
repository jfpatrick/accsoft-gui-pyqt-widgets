"""
Module containing QtDesigner plugin for screenshotting widgets.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


try:
    with disable_assert_cache():
        from accwidgets.screenshot import ScreenshotButton
except ImportError:
    pass
else:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    ScreenshotButtonPlugin = create_plugin(widget_class=ScreenshotButton,
                                           group=WidgetBoxGroup.BUTTONS,
                                           icon_base_path=_ICON_BASE_PATH)
