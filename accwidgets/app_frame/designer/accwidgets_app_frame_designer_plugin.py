"""
Module containing QtDesigner plugin for Application frame widget.
"""

from pathlib import Path


skip_plugin = False
try:
    from accwidgets.app_frame import ApplicationFrame
except ImportError:
    skip_plugin = True


if not skip_plugin:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _ICON_BASE_PATH = Path(__file__).parent.parent.absolute()

    ApplicationFramePlugin = create_plugin(widget_class=ApplicationFrame,
                                           group=WidgetBoxGroup.HIDDEN,
                                           icon_base_path=_ICON_BASE_PATH)
