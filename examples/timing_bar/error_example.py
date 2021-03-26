"""
This is the example of how communication error is displayed to the user.
The widget will draw a label "Communication error", regardless of the contents, just to make sure
that text will nicely fit in the frame. The actual error information can be received by hovering mouse
cursor over the widget.
For the sake of example, we are using custom model that does not require connection to real devices.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from accwidgets.timing_bar import TimingBar
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleTimingBarModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("TimingBar error example")

        model = SampleTimingBarModel()
        timing_bar = TimingBar(model=model)
        timing_bar.highlightedUser = "USER2"

        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        layout.addWidget(timing_bar)
        self.centralWidget().setLayout(layout)

        model.simulate_error("Simulated error. This would be a direct RDA exception from XTIM or CTIM device.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
