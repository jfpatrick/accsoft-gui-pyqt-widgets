"""
This is the example of how communication error is displayed to the user.
The widget will overlay a label with error occurred during processing LSA information.
For the sake of example, we are using custom model that does not require connection to LSA servers. Error is simulated
by emitting an error signal from the custom model.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from accwidgets.lsa_selector import LsaSelector
from sample_model import SampleLsaSelectorModel

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LsaSelector error example")

        model = SampleLsaSelectorModel()
        lsa_selector = LsaSelector(model=model)
        self.lsa = lsa_selector

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().addWidget(lsa_selector)

        model.simulate_error("Test error message")

        self.resize(400, 200)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
