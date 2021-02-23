"""
Module containing QtDesigner plugin for PropertyEdit widget.
"""

from pathlib import Path
from accwidgets._api import disable_assert_cache


skip_plugin = False
try:
    with disable_assert_cache():
        from accwidgets.property_edit import PropertyEdit
except ImportError:
    skip_plugin = True


if not skip_plugin:
    from accwidgets._designer_base import create_plugin, WidgetBoxGroup
    from accwidgets.property_edit.designer.designer_extensions import PropertyFieldExtension

    _ICON_BASE_PATH = Path(__file__).parent.absolute()

    PropertyEditPlugin = create_plugin(widget_class=PropertyEdit,
                                       extensions=[PropertyFieldExtension],
                                       group=WidgetBoxGroup.INPUTS,
                                       icon_base_path=_ICON_BASE_PATH)
