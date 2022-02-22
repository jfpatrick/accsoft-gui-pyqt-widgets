"""
Module containing QtDesigner plugin for PLS selector widget.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


try:
    with disable_assert_cache():
        from accwidgets.pls import PlsSelector
except ImportError:
    pass
else:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    PlsSelectorPlugin = create_plugin(widget_class=PlsSelector,
                                      group=WidgetBoxGroup.INPUTS,
                                      icon_base_path=_ICON_BASE_PATH)
