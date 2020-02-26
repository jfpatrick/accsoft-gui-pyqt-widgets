"""
Module containing QtDesigner plugin for LED widget.
"""

from pathlib import Path
from accwidgets.led import Led
from accwidgets.designer_base import create_plugin


_ICON_BASE_PATH = Path(__file__).parent.absolute()


PropertyEditPlugin = create_plugin(
    widget_class=Led,
    group="Display Widgets",
    icon_base_path=_ICON_BASE_PATH,
)
