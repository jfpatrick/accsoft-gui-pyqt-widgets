import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QColorDialog, QPushButton, QComboBox
from qtpy.uic import loadUi
from accwidgets.led import Led


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        """
        UI loaded from the Designer file (app.ui). Color picker allows setting custom color, while combobox
        sets the color to the predefined status color..
        """
        super().__init__(*args, **kwargs)

        self.pick_btn: QPushButton = None
        self.status_led: Led = None
        self.color_led: Led = None
        self.status_combo: QComboBox = None

        loadUi(Path(__file__).absolute().parent / "app.ui", self)

        self.pick_btn.clicked.connect(self.pick_color)
        self.status_combo.setCurrentIndex(3)
        self.status_combo.activated.emit(3)

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
