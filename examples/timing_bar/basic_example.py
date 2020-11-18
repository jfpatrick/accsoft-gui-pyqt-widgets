"""
This is the most basic example of using the timing bar widget.
By default, the widget is initialized with the predefined timing domain.
For the sake of example, we are using custom model that does not require connection to real devices.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from accwidgets.timing_bar import TimingBar
from sample_model import SampleTimingBarModel

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("TimingBar simple example")

        timing_bar = TimingBar(model=SampleTimingBarModel())
        timing_bar.highlightedUser = "USER2"

        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        layout.addWidget(timing_bar)
        self.centralWidget().setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
