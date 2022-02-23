"""
This is the same example as basic_example.py, but integrating with Qt Designer widget, instead of the
programmatically created one. For the sake of example, we are using custom model that does not require connection
to real devices.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy.uic import loadUi
from accwidgets.timing_bar import TimingBar
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleTimingBarModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.timing_bar: TimingBar = None

        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)

        # Redefine model before shown, so that it does not try to connect to devices
        self.timing_bar.model = SampleTimingBarModel(domain=self.timing_bar.model.domain)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
