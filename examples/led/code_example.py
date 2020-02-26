import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QColorDialog, QPushButton, QComboBox, QWidget, QGridLayout
from accwidgets.led import Led


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        """
        Color picker allows setting custom color, while combobox
        sets the color to the predefined status color. This is identical to designer_example.py
        """
        super().__init__(*args, **kwargs)
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
        self.show()

    def pick_color(self):
        new_color = QColorDialog.getColor(self.color_led.color)
        if not new_color.isValid():
            # User cancelled the selection
            return
        self.color_led.color = new_color


def run():
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
