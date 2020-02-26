import json
import sys
import warnings
import weakref
import numpy as np
from typing import Optional, List, Dict, Tuple, cast, Any, Union, TypeVar, Generic, Callable
from abc import ABCMeta, abstractmethod
from enum import IntEnum, IntFlag, auto
from qtpy.QtWidgets import (QWidget, QDoubleSpinBox, QCheckBox, QLineEdit, QComboBox, QSpinBox, QFormLayout, QLabel,
                            QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGroupBox, QLayout, QSizePolicy, QSpacerItem)
from qtpy.QtCore import Property, Q_ENUMS, QObjectCleanupHandler, Qt, Signal, Slot
from dataclasses import dataclass
from accwidgets.generics import GenericMeta
from accwidgets.designer_check import is_designer


@dataclass
class PropertyEditField:
    """
    Data structure for the field configuration of :class:`PropertyEdit`.
    """

    field: str
    """Name of the field in the property."""

    type: "PropertyEdit.ValueType"
    """Type of the field."""

    editable: bool
    """If this field can be edited or should be read-only."""

    label: Optional[str] = None
    """Optional label for the field. If undefined, `field` will be placed as a label."""

    user_data: Optional[Dict[str, Any]] = None
    """Optional additional data for specific fields. For example, ENUM configuration needs `options`."""


# For Qt Designer purposes
class _QtDesignerButtons:
    Neither = 0
    Set = 1
    Get = 2
    Both = 3


class _QtDesignerButtonPosition:
    Bottom = 0
    Right = 1


class _QtDesignerDecoration:
    Empty = 0
    Frame = 1
    GroupBox = 2


EnumItemConfig = Tuple[str, int]
"""One entry of the configuration for ENUM options. It's a tuple of user-readable label and code as seen in the control system."""


_ENUM_OPTIONS_KEY = "options"


class PropertyEdit(QWidget, _QtDesignerButtons, _QtDesignerButtonPosition, _QtDesignerDecoration):

    Q_ENUMS(
        _QtDesignerButtons,
        _QtDesignerButtonPosition,
        _QtDesignerDecoration,
    )

    class ValueType(IntEnum):
        """Possible types of the property fields."""

        INTEGER = auto()
        REAL = auto()
        BOOLEAN = auto()
        STRING = auto()
        ENUM = auto()

        @staticmethod
        def enum_user_data(options: List[EnumItemConfig]):
            """
            Factory method to create user_data dictionary for Enum types.

            Args:
                options: List of pairs (combobox item label -> associated int value)

            Returns:
                User data dictionary.
            """
            return {_ENUM_OPTIONS_KEY: options}

    class Buttons(IntFlag):
        """Bit mask for Get & Set buttons that have to be displayed in the widget."""
        GET = _QtDesignerButtons.Get
        SET = _QtDesignerButtons.Set

    class ButtonPosition(IntEnum):
        """Position where Get/Set buttons are placed, relative to the fields form."""
        BOTTOM = _QtDesignerButtonPosition.Bottom
        RIGHT = _QtDesignerButtonPosition.Right

    class Decoration(IntEnum):
        """Decoration of the widget to visually group fields together."""
        NONE = _QtDesignerDecoration.Empty
        FRAME = _QtDesignerDecoration.Frame
        GROUP_BOX = _QtDesignerDecoration.GroupBox

    valueUpdated = Signal(dict)
    """Signal issued when the user updates field values and presses 'Set' button."""

    valueRequested = Signal()
    """Signal issued when the user requests new values by pressing 'Get' button."""

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 # property_name: Optional[str] = None,
                 title: Optional[str] = None,
                 ):
        """
        Widget that allows receiving / sending a property with one or multiple fields at once.

        It is a container that can hold one or multiple child widgets for viewing/modifying the fields.
        These inner field widgets are organized in the form layout.

        Args:
            parent: Parent widget of this one.
            title: Optional title to be displayed, when selected :attr:`decoration` is GroupBox
        """
        QWidget.__init__(self, parent)
        # self._property_name: Optional[str] = property_name
        self._title: Optional[str] = title
        self._send_only_updated: bool = True
        self._buttons: PropertyEdit.Buttons = PropertyEdit.Buttons(_QtDesignerButtons.Neither)
        self._button_position = PropertyEdit.ButtonPosition.BOTTOM
        self._widget_config: List[PropertyEditField] = []
        self._widget_delegate: AbstractPropertyEditWidgetDelegate = PropertyEditWidgetDelegate()
        self._layout_delegate: AbstractPropertyEditLayoutDelegate = PropertyEditFormLayoutDelegate()

        # Assuming None frame in the beginning
        self._decoration_type: PropertyEdit.Decoration = PropertyEdit.Decoration.NONE
        self._widget_layout = self._layout_delegate.create_layout()
        self._widget_layout.setObjectName("widget_layout")
        self._decoration: Union[QFrame, QGroupBox, None] = None
        self._layout = QVBoxLayout(self)
        self._layout.setObjectName("main_layout")
        self._button_box = QHBoxLayout()
        self._button_box.setObjectName("button_box_layout")
        self._get_btn = QPushButton("Get")
        self._get_btn.setObjectName("get_btn")
        self._set_btn = QPushButton("Set")
        self._set_btn.setObjectName("set_btn")
        self._get_btn.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        self._set_btn.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        self._get_btn.clicked.connect(self.valueRequested.emit)
        self._set_btn.clicked.connect(self._do_set)
        self._button_box.setContentsMargins(0, 0, 0, 0)
        self._left_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._right_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._button_box.addWidget(self._get_btn)
        self._button_box.addWidget(self._set_btn)
        self._layout.addLayout(self._widget_layout)
        self._layout.addLayout(self._button_box)
        self._add_button_stretch()  # This goes along with the default position = bottom

        self._recalculate_button_box()
        self._recalculate_layout()
        self._recalculate_container()

    @Slot(dict)
    def setValue(self, new_val: Dict[str, Any]):
        """
        Slot to receive new value of the property.

        Args:
            new_val: Dictionary with field value map.
        """
        self._widget_delegate.value_updated(new_val)

    # @Property(str)
    # def propertyName(self) -> str:
    #     return self._property_name
    #
    # @propertyName.setter  # type: ignore
    # def propertyName(self, new_val: str):
    #     self._property_name = new_val
    #     # TODO: PropertyName will become useful when we use auto-configuration form pyccda

    def _get_buttons(self) -> "PropertyEdit.Buttons":
        return self._buttons

    def _set_buttons(self, new_val: "PropertyEdit.Buttons"):
        self._buttons = new_val
        self._recalculate_button_box()

    buttons: "PropertyEdit.Buttons" = Property(_QtDesignerButtons, _get_buttons, _set_buttons)
    """Bit mask of what buttons should be displayed in the widget."""

    def _get_button_position(self) -> "PropertyEdit.ButtonPosition":
        return self._button_position

    def _set_button_position(self, new_val: "PropertyEdit.ButtonPosition"):
        self._button_position = new_val
        self._recalculate_layout()

    buttonPosition: "PropertyEdit.ButtonPosition" = Property(_QtDesignerButtonPosition, _get_button_position, _set_button_position)
    """Position where Get/Set buttons are placed, relative to the fields form."""

    def _get_title(self) -> str:
        """Title that is displayed when decoration type is 'GroupBox'."""
        return self._title or ""

    def _set_title(self, new_val: str):
        self._title = new_val
        if isinstance(self._decoration, QGroupBox):
            cast(QGroupBox, self._decoration).setTitle(new_val)

    title: str = Property(str, _get_title, _set_title)
    """Title that is displayed when decoration type is 'GroupBox'."""

    def _get_decoration(self) -> "PropertyEdit.Decoration":
        return self._decoration_type

    def _set_decoration(self, new_val: "PropertyEdit.Decoration"):
        self._decoration_type = new_val
        self._recalculate_container()

    decoration: "PropertyEdit.Decoration" = Property(_QtDesignerDecoration, _get_decoration, _set_decoration)
    """Decoration of the widget to visually group fields together."""

    def _get_send_only_updated_values(self) -> bool:
        return self._send_only_updated

    def _set_send_only_updated_values(self, new_val: bool):
        self._send_only_updated = new_val

    sendOnlyUpdatedValues: bool = Property(bool, _get_send_only_updated_values, _set_send_only_updated_values)
    """If ``True``, only values from editable fields will be sent on pressing 'Set' button. Otherwise, all values will be sent."""

    def _get_fields(self) -> List[PropertyEditField]:
        if is_designer():
            return _pack_designer_fields(self._widget_config)  # type: ignore  # we want string here for Designer
        return self._widget_config

    def _set_fields(self, new_val: List[PropertyEditField]):
        if isinstance(new_val, str):  # Can happen inside the Designer or when initializing from *.ui file
            new_val = _unpack_designer_fields(cast(str, new_val))
        self._widget_config = new_val
        self._layout_widgets()

    fields: List[PropertyEditField] = Property(str, _get_fields, _set_fields, designable=False)
    """Configuration for the fields that construct the form of widgets inside this container."""

    @property
    def widget_delegate(self) -> "AbstractPropertyEditWidgetDelegate":
        """Delegate that controls the inner widget appearance."""
        return self._widget_delegate

    @widget_delegate.setter
    def widget_delegate(self, new_val: "AbstractPropertyEditWidgetDelegate"):
        """Delegate that controls the inner widget appearance."""
        if new_val == self._widget_delegate:
            return
        self._widget_delegate = new_val
        self._layout_widgets()

    @property
    def layout_delegate(self) -> "AbstractPropertyEditLayoutDelegate":
        """Delegate that controls the layout of the inner widgets."""
        return self._layout_delegate

    @layout_delegate.setter
    def layout_delegate(self, new_val: "AbstractPropertyEditLayoutDelegate"):
        """Delegate that controls the layout of the inner widgets."""
        if new_val == self._layout_delegate:
            return
        self._layout_delegate = new_val
        new_widget_layout = new_val.create_layout()
        new_widget_layout.setObjectName("widget_layout")
        old_widget_layout = self._widget_layout
        _clean_layout(old_widget_layout)
        self._layout.removeItem(old_widget_layout)
        old_widget_layout.deleteLater()
        self._widget_layout = new_widget_layout
        self._layout.addLayout(new_widget_layout)

        # InsertLayout does not prepend the layout, so we instead remove all of them and re-add
        self._layout.removeItem(self._button_box)
        self._layout.addLayout(self._button_box)
        self._layout_widgets()

    def _layout_widgets(self):
        _clean_layout(self._widget_layout)
        self._layout_delegate.layout_widgets(layout=self._widget_layout,
                                             widget_config=self._widget_config,
                                             create_widget=self._widget_delegate.widget_for_item,
                                             parent=self)

    def _recalculate_layout(self):
        if self._button_position == PropertyEdit.ButtonPosition.BOTTOM:
            desired_type = QVBoxLayout
        elif self._button_position == PropertyEdit.ButtonPosition.RIGHT:
            desired_type = QHBoxLayout
        else:
            warnings.warn(f"Unsupported button position value {self._button_position}")
            return

        if isinstance(self._layout, desired_type):
            return
        new_layout = desired_type()
        for child in self._layout.children():  # children of a layout are always layouts
            self._layout.removeItem(child)
            new_layout.addLayout(child)

        if self._button_position == PropertyEdit.ButtonPosition.BOTTOM:
            self._add_button_stretch()
        else:
            self._remove_button_stretch()

        layout_container = self._layout.parentWidget()

        # You can't directly delete a layout and you can't
        # replace a layout on a widget which already has one
        # Found here: https://stackoverflow.com/a/10439207
        QObjectCleanupHandler().add(self._layout)

        layout_container.setLayout(new_layout)
        new_layout.setObjectName("main_layout")
        self._layout = new_layout

    def _add_button_stretch(self):
        self._button_box.insertStretch(0)
        self._button_box.addStretch()

    def _remove_button_stretch(self):
        self._button_box.takeAt(0)
        self._button_box.takeAt(self._button_box.count() - 1)

    def _recalculate_container(self):
        if self._decoration_type == PropertyEdit.Decoration.NONE:
            desired_container = None
        elif self._decoration_type == PropertyEdit.Decoration.FRAME:
            desired_container = QFrame
        elif self._decoration_type == PropertyEdit.Decoration.GROUP_BOX:
            desired_container = QGroupBox
        else:
            warnings.warn(f"Unsupported decoration value {self._decoration_type}")
            return

        if ((desired_container is None and self._decoration is None)
                or (desired_container is not None and isinstance(self._decoration, desired_container))):
            return

        if self._decoration is not None:
            self.layout().removeWidget(self._decoration)
            self._decoration.deleteLater()  # Call needed in order to visually remove leftover widget from UI
            self._decoration = None

        if desired_container is None:
            self._update_layout(self._layout)  # Assign main layout directly to the widget
            return

        new_container = desired_container()
        new_container.setObjectName("decoration_container")
        self._decoration = new_container
        if desired_container == QFrame:
            frame = cast(QFrame, new_container)
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setFrameShadow(QFrame.Raised)
            frame.setLineWidth(1)
        elif desired_container == QGroupBox:
            box = cast(QGroupBox, new_container)
            box.setTitle(self.title)

        new_container.setLayout(self._layout)  # Assign main layout into decoration proxy

        # Embed the decoration container in the main widget with a regular layout
        layout = QHBoxLayout()
        layout.addWidget(new_container)
        self._update_layout(layout)

    def _recalculate_button_box(self):
        self._get_btn.setVisible(self.buttons & PropertyEdit.Buttons.GET)
        self._set_btn.setVisible(self.buttons & PropertyEdit.Buttons.SET)

    def _do_set(self):
        new_val = self._widget_delegate.read_value(self._send_only_updated)
        self.valueUpdated.emit(new_val)

    def _update_layout(self, new_layout: QLayout):
        if self.layout() == new_layout:
            return

        # You can't directly delete a layout and you can't
        # replace a layout on a widget which already has one
        # Found here: https://stackoverflow.com/a/10439207
        QObjectCleanupHandler().add(self.layout())

        self.setLayout(new_layout)


L = TypeVar("L", bound=QLayout)


class AbstractPropertyEditLayoutDelegate(Generic[L], metaclass=GenericMeta):
    """
    Class for defining delegates that handle the layout inside the :class:`PropertyEdit` widget.
    """

    @abstractmethod
    def create_layout(self) -> L:
        """
        Creates layout for to place the widgets and labels inside.

        Returns:
            New layout instance.
        """
        pass

    @abstractmethod
    def layout_widgets(self, layout: L, widget_config: List[PropertyEditField], create_widget: Callable[[PropertyEditField, Optional[QWidget]], QWidget], parent: Optional[QWidget] = None):
        """
        Adds widgets to the layout created via :meth:`create_layout`.

        Delegate does not need to clean the layout from existing widgets, it is done for him.
        It also should not cached layout, but act on the one given via this method arguments.

        Args:
            layout: Existing layout instance that should be updated with new widgets.
            widget_config: Configuration of the fields inside :class:`PropertyEdit`.
            create_widget: Factory method that will construct a :class:`QWidget` instance to be added to the layout.
            parent: Owner of the constructed widgets to be passed into "create_widget" function.
        """
        pass


class PropertyEditFormLayoutDelegate(AbstractPropertyEditLayoutDelegate[QFormLayout]):
    """
    Default implementation for delegate that can handle the creation of the layout for :class:`PropertyEdit`.
    """

    def create_layout(self) -> QFormLayout:
        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignLeft)
        layout.setFormAlignment(Qt.AlignVCenter)
        return layout

    def layout_widgets(self, layout: QFormLayout, widget_config: List[PropertyEditField], create_widget: Callable[[PropertyEditField, Optional[QWidget]], QWidget], parent: Optional[QWidget] = None):
        for conf in widget_config:
            label = conf.label or conf.field
            widget = create_widget(conf, parent)
            layout.addRow(label, widget)


class AbstractPropertyEditWidgetDelegate(metaclass=ABCMeta):

    def __init__(self):
        """
        Class for defining delegates that can handle the creation and data marshalling
        to inner widgets of the :class:`PropertyEdit`.
        """
        super().__init__()
        self.widget_map: Dict[str, Tuple[weakref.ReferenceType, PropertyEditField]] = {}
        """Map between field IDs and widget instances / expected data type"""

        self.last_value: Dict[str, Any] = {}
        """Last known data sample arriving from the control system"""

    @abstractmethod
    def create_widget(self,
                      field_id: str,
                      item_type: PropertyEdit.ValueType,
                      editable: bool,
                      user_data: Optional[Dict[str, Any]],
                      parent: Optional[QWidget] = None) -> QWidget:
        """
        Creates widget for the given type to be rendered inside PropertyEdit widget.

        You must never call this method directly, but rather use :meth:`widget_for_item`.

        Args:
            field_id: Field associated with the given widget.
            item_type: Type of the value that is expected on that field.
            editable: Whether the given field is read-only or writable.
            user_data: Arbitrary data relevant for specific item types.
            parent: Parent widget for the newly instantiated widgets.

        Returns:
            New widget instance.
        """
        pass

    @abstractmethod
    def display_data(self, field_id: str, value: Any, user_data: Optional[Dict[str, Any]], item_type: PropertyEdit.ValueType, widget: QWidget):
        """
        Method that is called when a new value arrives to PropertyEdit and it starts
        distributing the data to individual widgets. Here you can display incoming data in the widget.
        This will be called on GET or SUBSCRIBE operations to display data.

        Args:
            field_id: Field associated with the given widget.
            value: Incoming value of the field.
            user_data: Optional data associated with the field.
            item_type: Type of the value that is expected on that field.
            widget: Associated widget that needs to display the data.
        """
        pass

    @abstractmethod
    def send_data(self, field_id: str, user_data: Optional[Dict[str, Any]], item_type: PropertyEdit.ValueType, widget: QWidget) -> Any:
        """
        Method that is called when a value update is about to be sent to the control system.
        :class:`PropertyEdit` will collect the update values for each of the fields to construct them into
        shared map object. Thereby, this method will be called for each individual widget on SET operation.

        Args:
            field_id: Field associated with the given widget.
            user_data: Optional data associated with the field.
            item_type: Type of the value that is expected on that field.
            widget: Associated widget that needs to display the data.
        """
        pass

    def widget_for_item(self, config: PropertyEditField, parent: Optional[QWidget] = None) -> QWidget:
        """
        Retrieves a widget for the given item. Do not override this method, but rather :meth:`create_widget`.

        Args:
            config: Configuration object for the field
            parent: Parent widget for the newly instantiated widgets.

        Returns:
            New or cached widget instance.
        """
        def make_new():
            new_widget = self.create_widget(field_id=config.field,
                                            item_type=config.type,
                                            editable=config.editable,
                                            user_data=config.user_data,
                                            parent=parent)
            self.widget_map[config.field] = weakref.ref(new_widget), config
            return new_widget

        try:
            weak_widget = self.widget_map[config.field][0]
            widget = weak_widget()
            if widget is None:
                return make_new()
            return widget
        except KeyError:
            return make_new()

    def value_updated(self, value: Dict[str, Any]):
        """
        Slot to propagate property dictionary from the control system into individual widgets.

        Args:
            value: Actual value from the control system in form of dictionary, where keys are field names
                   and values are values of those fields.
        """
        self.last_value = value
        for field_id, field_value in value.items():
            try:
                weak_widget, config = self.widget_map[field_id]  # This will fail on the unseen field or if this field was not configured before
            except KeyError:
                continue
            widget = weak_widget()
            if widget is not None:
                self.display_data(field_id=field_id, value=field_value, item_type=config.type, user_data=config.user_data, widget=widget)
            else:
                warnings.warn("Won't be displaying data on deleted weak reference")

    def read_value(self, send_only_updated: bool) -> Dict[str, Any]:
        """
        Called by :class:`PropertyEdit` to collect the property value to be sent to the control system.

        Args:
            send_only_updated: When ``True``, only changed fields will be composed into the dictionary.

        Returns:
            Dictionary representing device property value.
        """
        res = {}
        for field_id, refs in self.widget_map.items():
            weak_widget, config = refs

            if send_only_updated and not config.editable:
                continue

            widget = weak_widget()
            if widget is not None:
                new_val = self.send_data(field_id=field_id, user_data=config.user_data, widget=widget, item_type=config.type)
                if send_only_updated:
                    last_val = self.last_value.get(field_id)
                    if isinstance(new_val, np.ndarray) and isinstance(last_val, np.ndarray):
                        # We need all() call, otherwise it results in array of bools
                        vals_equal = new_val.shape == last_val.shape and (new_val == last_val).all()
                    else:
                        vals_equal = new_val == last_val
                    if vals_equal:
                        continue
                res[field_id] = new_val
            else:
                warnings.warn("Won't be sending data from deleted weak reference")
        return res


class PropertyEditWidgetDelegate(AbstractPropertyEditWidgetDelegate):
    """
    Default implementation for delegate that can handle the creation and data marshalling
    to inner widgets of the :class:`PropertyEdit`.
    """

    def create_widget(self,
                      field_id: str,
                      item_type: PropertyEdit.ValueType,
                      editable: bool,
                      user_data: Optional[Dict[str, Any]],
                      parent: Optional[QWidget] = None) -> QWidget:
        _ = field_id
        # TODO: This needs to be updated with smarter widgets when they are available (e.g. combobox that can work with EnumSets or LED for booleans). Currently this will be overridden in ComRAD which has LEDs
        if not editable:
            widget = QLabel(parent)
            if is_designer():
                widget.setText("<Runtime value>")
            return widget
        if item_type == PropertyEdit.ValueType.INTEGER:
            widget = QSpinBox(parent)
            max_val = 2**sys.int_info.bits_per_digit  # can't use sys.maxsize here, as it supplies "long" size overflowing Qt
            widget.setMaximum(max_val - 1)
            widget.setMinimum(-max_val + 1)
            return widget
        if item_type == PropertyEdit.ValueType.REAL:
            widget = QDoubleSpinBox(parent)
            max_val = sys.float_info.max
            widget.setMaximum(max_val)
            widget.setMinimum(-max_val)
            return widget
        if item_type == PropertyEdit.ValueType.BOOLEAN:
            return QCheckBox(parent)
        if item_type == PropertyEdit.ValueType.STRING:
            return QLineEdit(parent)
        if item_type == PropertyEdit.ValueType.ENUM:
            widget = QComboBox(parent)
            for label, code in (user_data or {}).get(_ENUM_OPTIONS_KEY, []):
                widget.addItem(label, code)
            return widget

    def display_data(self, field_id: str, value: Any, user_data: Optional[Dict[str, Any]], item_type: PropertyEdit.ValueType, widget: QWidget):
        _ = field_id
        if isinstance(widget, QLabel):
            if item_type == PropertyEdit.ValueType.ENUM:
                if isinstance(value, int):
                    ud = user_data or {}
                    options = cast(List[EnumItemConfig], ud.get("options", []))
                    for label, code in options:
                        if code == value:
                            cast(QLabel, widget).setText(label)
                            return
                elif isinstance(value, tuple):  # Expecting (code, label) from PyJapc
                    try:
                        _, label = value
                        cast(QLabel, widget).setText(label)
                        return
                    except ValueError:
                        pass
                warnings.warn(f"Can't set data {value} to QLabel. Unexpected enum value received.")
            elif isinstance(value, str):
                cast(QLabel, widget).setText(value)
            elif isinstance(value, bool):
                cast(QLabel, widget).setText(str(value))
            elif isinstance(value, int) or isinstance(value, float):
                cast(QLabel, widget).setNum(value)
            else:
                warnings.warn(f"Can't set data {value} to QLabel. Unsupported data type.")
        elif isinstance(widget, QSpinBox):
            cast(QSpinBox, widget).setValue(value)  # Assuming data is int here, based on the widget_for_item
        elif isinstance(widget, QDoubleSpinBox):
            cast(QDoubleSpinBox, widget).setValue(value)  # Assuming data is float here, based on the widget_for_item
        elif isinstance(widget, QCheckBox):
            cast(QCheckBox, widget).setChecked(value)  # Assuming data is bool here, based on the widget_for_item
        elif isinstance(widget, QLineEdit):
            cast(QLineEdit, widget).setText(value)  # Assuming data is str here, based on the widget_for_item
        elif isinstance(widget, QComboBox):
            combo = cast(QComboBox, widget)
            if isinstance(value, tuple):  # Expecting (code, label) from PyJapc
                try:
                    value, _ = value
                except ValueError:
                    pass

            if isinstance(value, int):
                idx = combo.findData(value)  # Assuming data is int, value of the related userData of combobox items.
                if idx != -1:
                    combo.setCurrentIndex(idx)
                    return

            warnings.warn(f"Can't set data {value} to QComboBox. Unexpected enum value received.")

    def send_data(self, field_id: str, user_data: Optional[Dict[str, Any]], item_type: PropertyEdit.ValueType, widget: QWidget) -> Any:
        _ = field_id
        if isinstance(widget, QLabel):
            # This is clearly non-editable field. So just read last known value
            return self.last_value.get(field_id)
        elif isinstance(widget, QSpinBox):
            return cast(QSpinBox, widget).value()
        elif isinstance(widget, QDoubleSpinBox):
            return cast(QDoubleSpinBox, widget).value()
        elif isinstance(widget, QCheckBox):
            return cast(QCheckBox, widget).isChecked()
        elif isinstance(widget, QLineEdit):
            return cast(QLineEdit, widget).text()
        elif isinstance(widget, QComboBox):
            return cast(QComboBox, widget).currentData()


def _unpack_designer_fields(input: str) -> List[PropertyEditField]:
    try:
        contents = json.loads(input)
    except json.JSONDecodeError as ex:
        warnings.warn(f"Failed to decode json: {str(ex)}")
        return []

    if not isinstance(contents, list):
        warnings.warn(f"Decoded fields is not a list")
        return []

    def map_field(val: Dict[str, Any]) -> PropertyEditField:
        return PropertyEditField(field=val["field"],
                                 type=PropertyEdit.ValueType(val["type"]),
                                 editable=val["rw"],
                                 label=val.get("label"),
                                 user_data=val.get("ud"))

    return list(map(map_field, contents))


def _pack_designer_fields(input: List[PropertyEditField]) -> str:

    def map_field(val: PropertyEditField) -> Dict[str, Any]:
        res = {
            "field": val.field,
            "type": val.type,
            "rw": val.editable,
        }
        if val.label:
            res["label"] = val.label
        if val.user_data:
            res["ud"] = val.user_data
        return res

    json_obj = list(map(map_field, input))
    return json.dumps(json_obj)


def _clean_layout(layout: QLayout):
    for _ in range(layout.count()):
        item = layout.takeAt(0)
        widget = cast(Optional[QWidget], item.widget())
        if widget:
            widget.setParent(None)
            widget.deleteLater()
