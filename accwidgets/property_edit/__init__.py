"""
:class:`PropertyEdit` allows interacting with multiple fields of the same property
(as a concept of CERN's device properties), similar to the "Knob" of a "WorkingSet".
"""
# flake8: noqa: F401

from .propedit import (PropertyEdit, PropertyEditField, EnumItemConfig,
                       AbstractPropertyEditLayoutDelegate, AbstractPropertyEditWidgetDelegate)


from accwidgets._api import mark_public_api
mark_public_api(PropertyEdit, __name__)
mark_public_api(PropertyEditField, __name__)
mark_public_api(AbstractPropertyEditLayoutDelegate, __name__)
mark_public_api(AbstractPropertyEditWidgetDelegate, __name__)
