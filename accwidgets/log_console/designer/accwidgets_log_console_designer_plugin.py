"""
Module containing QtDesigner plugin for Log console widget.
"""

from pathlib import Path


skip_plugin = False
try:
    from accwidgets.log_console import LogConsole
except ImportError:
    skip_plugin = True


if not skip_plugin:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup, HidePrivateSignalsExtension

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    LogConsolePlugin = create_plugin(widget_class=LogConsole,
                                     extensions=[HidePrivateSignalsExtension],
                                     group=WidgetBoxGroup.INDICATORS,
                                     icon_base_path=_ICON_BASE_PATH)
