"""
This example shows the simple integration of Led widget into a window. 2 Leds are placed side by side, one of
which is controlled via "Status" combobox, that modifies Led color based on the predefined status, while another
Led accepts an arbitrary RBG color from the color picker.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QColorDialog, QPushButton, QComboBox, QWidget, QGridLayout
from accwidgets.led import Led

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Led simple example")
        self.setCentralWidget(QWidget())
        layout = QGridLayout()
        self.centralWidget().setLayout(layout)
        layout.setContentsMargins(15, 15, 15, 15)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Unknown", "On", "Off", "Warning", "Error"])
        layout.addWidget(self.status_combo, 0, 0)

        self.pick_btn = QPushButton("Pick color")
        self.pick_btn.clicked.connect(self.pick_color)
        layout.addWidget(self.pick_btn, 0, 1)

        self.status_led = Led()
        layout.addWidget(self.status_led, 1, 0)

        self.color_led = Led()
        layout.addWidget(self.color_led, 1, 1)

        self.status_combo.activated.connect(self.status_led.setStatus)

        self.status_combo.setCurrentIndex(3)
        self.status_combo.activated.emit(3)

        self.resize(360, 223)

    def pick_color(self):
        new_color = QColorDialog.getColor(self.color_led.color)
        if not new_color.isValid():  # User cancelled the selection
            return
        self.color_led.color = new_color


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
