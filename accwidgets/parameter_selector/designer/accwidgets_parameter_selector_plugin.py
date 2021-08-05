"""
Module containing QtDesigner plugin for ParameterLineEdit widget.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


skip_plugin = False
try:
    with disable_assert_cache():
        from accwidgets.parameter_selector import ParameterLineEdit
except ImportError:
    skip_plugin = True


if not skip_plugin:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    ParameterLineEditPlugin = create_plugin(widget_class=ParameterLineEdit,
                                            group=WidgetBoxGroup.INPUTS,
                                            icon_base_path=_ICON_BASE_PATH)
