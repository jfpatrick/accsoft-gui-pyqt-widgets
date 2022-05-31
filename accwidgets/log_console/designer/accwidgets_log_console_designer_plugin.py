"""
Module containing QtDesigner plugin for Log console widget.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


try:
    with disable_assert_cache():
        from accwidgets.log_console import LogConsole
except ImportError:
    pass
else:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup, HidePrivateSignalsExtension

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    LogConsolePlugin = create_plugin(widget_class=LogConsole,
                                     extensions=[HidePrivateSignalsExtension],
                                     group=WidgetBoxGroup.INDICATORS,
                                     icon_base_path=_ICON_BASE_PATH)
