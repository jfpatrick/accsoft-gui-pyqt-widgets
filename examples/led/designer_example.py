"""
This example shows the integration of Led widget using Qt Designer. 2 Leds are placed side by side, one of
which is controlled via "Status" combobox, that modifies Led color based on the predefined status, while another
Led accepts an arbitrary RBG color from the color picker.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QColorDialog, QPushButton, QComboBox
from qtpy.uic import loadUi
from accwidgets.led import Led
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pick_btn: QPushButton = None
        self.status_led: Led = None
        self.color_led: Led = None
        self.status_combo: QComboBox = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)
        self.pick_btn.clicked.connect(self.pick_color)
        self.status_combo.setCurrentIndex(3)
        self.status_combo.activated.emit(3)

    def pick_color(self):
        new_color = QColorDialog.getColor(self.color_led.color)
        if not new_color.isValid():
            # User cancelled the selection
            return
        self.color_led.color = new_color


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
