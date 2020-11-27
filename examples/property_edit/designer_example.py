"""
Example of embedding PropertyEdit widget using Qt Designer. UI loaded from the designer_example.ui file.
2 PropertyEdit widgets work on the same data set. First one, with the "Set" button, lets you define custom values.
Pressing "Set", propagates the value to the assumed control system, reflected by the JSON representation in the
bottom of the window. The second widget, with the "Get" button, lets you fetch updated values from the control
system, so it starts displaying same values as seen in the JSON representation.
"""

import sys
import json
from typing import Dict, Any
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QLabel
from qtpy.uic import loadUi
from accwidgets.property_edit import PropertyEdit

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cs_label: QLabel = None
        self.set_propedit: PropertyEdit = None
        self.get_propedit: PropertyEdit = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)

        self._cs_val: Dict[str, Any] = {
            "amplitude": 0.5,
            "frequency": 30,
            "enabled": True,
            "particles": 2,
        }

        self.set_propedit.setValue(self._cs_val)

        self.set_propedit.valueUpdated.connect(self.send_val)
        self.get_propedit.valueRequested.connect(self.receive_val)

        # Propagate initial values
        self.send_val(self._cs_val)
        self.receive_val()

    def send_val(self, val: Dict[str, Any]):
        self._cs_val = val
        self.cs_label.setText(json.dumps(val, indent=4))

    def receive_val(self):
        self.get_propedit.setValue(self._cs_val)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
