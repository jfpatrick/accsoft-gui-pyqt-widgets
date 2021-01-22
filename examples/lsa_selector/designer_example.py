"""
This is the the same example as basic_example.py, but integrating with Qt Designer widget, instead of the
programmatically created one. For the sake of example, we are using custom model that does not require
connection to LSA servers.
"""

import sys
from pathlib import Path
from unittest import mock
from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy.uic import loadUi
from accwidgets.designer_check import set_designer
from accwidgets.lsa_selector import LsaSelector
from sample_model import SampleLsaSelectorModel

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lsa_selector: LsaSelector = None

        set_designer()  # This prevents widget from trying to contact LSA servers in the next call

        # Redefine model before shown, so that it does not try to connect to devices
        with mock.patch("accwidgets.lsa_selector._view.LsaSelectorModel.__new__", side_effect=SampleLsaSelectorModel.__new__):
            loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)

        self.lsa_selector.contextSelectionChanged.connect(lambda ctx: print(f"New LSA context: {ctx}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
