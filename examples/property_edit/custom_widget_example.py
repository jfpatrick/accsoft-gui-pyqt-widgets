"""
This example embeds a single PropertyEdit widget, which contains 2 fields of different types.
The purpose is to show how to create a custom inner widget, as opposed to default form field
widget.
"""

import sys
import json
from typing import Dict, Any, Optional, cast
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLCDNumber
from accwidgets.property_edit import PropertyEdit, PropertyEditField, AbstractPropertyEditWidgetDelegate

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class CustomWidgetDelegate(AbstractPropertyEditWidgetDelegate):
    """
    Custom delegate that creates LCD widgets for numerical fields.
    """

    def create_widget(self,
                      field_id: str,
                      item_type: PropertyEdit.ValueType,
                      editable: bool,
                      user_data: Optional[Dict[str, Any]],
                      parent: Optional[QWidget] = None) -> QWidget:
        widget = QLCDNumber(parent)
        widget.setFrameShape(QLCDNumber.NoFrame)
        widget.setSegmentStyle(QLCDNumber.Flat)
        return widget

    def display_data(self, field_id: str, value: Any, user_data: Optional[Dict[str, Any]], item_type: PropertyEdit.ValueType, widget: QWidget):
        cast(QLCDNumber, widget).display(value)

    def send_data(self, field_id: str, user_data: Optional[Dict[str, Any]], item_type: PropertyEdit.ValueType, widget: QWidget) -> Any:
        if item_type == PropertyEdit.ValueType.INTEGER:
            return cast(QLCDNumber, widget).intValue()
        else:
            return cast(QLCDNumber, widget).value()


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PropertyEdit custom widget delegate example")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setLayout(QVBoxLayout())
        property_edit = PropertyEdit()
        property_edit.buttons = PropertyEdit.Buttons.GET
        property_edit.fields = [
            PropertyEditField(field="amplitude", label="Amplitude (mA)", editable=True, type=PropertyEdit.ValueType.REAL),
            PropertyEditField(field="frequency", label="Frequency (Hz)", editable=True, type=PropertyEdit.ValueType.INTEGER),
        ]
        property_edit.widget_delegate = CustomWidgetDelegate()
        property_edit.valueUpdated.connect(self.format_data)
        property_edit.valueRequested.connect(self.create_data_sample)
        self.property_edit = property_edit
        main_widget.layout().addWidget(property_edit)

    def format_data(self, incoming: Dict[str, Any]):
        formatted_text = json.dumps(incoming, indent=4)
        self.label.setText(formatted_text)

    def create_data_sample(self):
        self.property_edit.setValue({
            "amplitude": 0.5,
            "frequency": 30,
        })


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
