import sys
import json
from typing import Dict, Any
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGroupBox, QLabel
from accwidgets.property_edit import PropertyEdit, PropertyEditField


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        """
        This example embeds a single PropertyEdit widget, which contains 4 fields of different types.
        Both "Get" and "Set" buttons are available. Whenever user presses "Set", the assumed propagation of the value
        to the control system is reflected by JSON representation in the bottom of the window.
        "Get" will reset the field values to the predefined setting.
        """

        super().__init__(*args, **kwargs)
        self.setWindowTitle("Proton-Ion Property Editor")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setLayout(QVBoxLayout())
        property_edit = PropertyEdit(title="Proton-Ion Config")
        property_edit.decoration = PropertyEdit.Decoration.FRAME
        property_edit.buttons = PropertyEdit.Buttons.SET | PropertyEdit.Buttons.GET
        property_edit.fields = [
            PropertyEditField(field="amplitude", label="Amplitude (mA)", editable=True, type=PropertyEdit.ValueType.REAL),
            PropertyEditField(field="frequency", label="Frequency (Hz)", editable=True, type=PropertyEdit.ValueType.INTEGER),
            PropertyEditField(field="enabled", label="Enabled", editable=True, type=PropertyEdit.ValueType.BOOLEAN),
            PropertyEditField(field="particles",
                              label="Particle Type",
                              editable=True,
                              type=PropertyEdit.ValueType.ENUM,
                              user_data=PropertyEdit.ValueType.enum_user_data([
                                  ("Protons", 1),
                                  ("Ions", 2),
                                  ("Electrons", 4),
                              ])),
        ]
        property_edit.valueUpdated.connect(self.format_data)
        property_edit.valueRequested.connect(self.create_data_sample)
        self.property_edit = property_edit
        main_widget.layout().addWidget(property_edit)
        main_widget.layout().addStretch()
        res_box = QGroupBox("Sent data sample")
        label = QLabel()
        res_box.setLayout(QVBoxLayout())
        res_box.layout().addWidget(label)
        main_widget.layout().addWidget(res_box)
        self.label = label
        self.show()

    def format_data(self, incoming: Dict[str, Any]):
        formatted_text = json.dumps(incoming, indent=4)
        self.label.setText(formatted_text)

    def create_data_sample(self):
        self.property_edit.setValue({
            "amplitude": 0.5,
            "frequency": 30,
            "enabled": True,
            "particles": 2,
        })


def run():
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
