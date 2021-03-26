"""
This is the example of how the TimingBar can be "frozen" by stopping active subscriptions to the
timing devices. "Toggle" button will switch between "frozen" and normal states.
For the sake of example, we are using custom model that does not require connection to real devices.
"""

import sys
import json
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from accwidgets.timing_bar import TimingBar
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleTimingBarModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("TimingBar toggle example")

        timing_bar = TimingBar(model=SampleTimingBarModel())
        self.timing_bar = timing_bar

        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        layout.addWidget(timing_bar)
        self.label = QLabel()
        layout.addWidget(self.label)
        btn = QPushButton("Toggle")
        btn.clicked.connect(self.toggle)
        layout.addWidget(btn)
        self.centralWidget().setLayout(layout)
        self.update_label()
        timing_bar.model.monitoringChanged.connect(self.update_label)

    def toggle(self):
        self.timing_bar.model.monitoring = not self.timing_bar.model.monitoring

    def update_label(self):
        self.label.setText(f"Monitoring: {json.dumps(self.timing_bar.model.monitoring)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
