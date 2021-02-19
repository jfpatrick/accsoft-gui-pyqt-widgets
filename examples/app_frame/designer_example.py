"""
This is the the same ApplicationFrame example as programmatic_example.py, but integrating with Qt Designer widget,
instead of the programmatically created one. By default, it will not enable any additional widgets in order to prevent
the implicit need to install additional dependencies for other widgets. It is possible, however, to enable those in
property configuration. The app.ui file was created using "CERN Application Frame"
Qt Designer template. To find out how to install such a template, use the command line utility:

$ accwidgets-cli -h

"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication
from qtpy.uic import loadUi
from accwidgets.app_frame import ApplicationFrame


# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(ApplicationFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loadUi(Path(__file__).absolute().parent / "app.ui", self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
