"""
Module containing QtDesigner plugin for PropertyEdit widget.
"""

from pathlib import Path
from accwidgets.property_edit import PropertyEdit
from accwidgets.property_edit.designer.designer_extensions import PropertyFieldExtension
from accwidgets._designer_base import create_plugin


_ICON_BASE_PATH = Path(__file__).parent.absolute()


PropertyEditPlugin = create_plugin(widget_class=PropertyEdit,
                                   extensions=[PropertyFieldExtension],
                                   group="Inputs",
                                   icon_base_path=_ICON_BASE_PATH)
