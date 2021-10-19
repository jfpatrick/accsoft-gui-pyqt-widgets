"""
This example shows how to use LsaSelector widget to drive PyJapc's timing user.
For the sake of example, we are using custom model that does not require connection to LSA servers, and pyjapc is
replaced with papc to remove the requirement of real devices and Technical Network.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from accwidgets.lsa_selector import LsaSelector, LsaSelectorAccelerator
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleLsaSelectorModel  # type: ignore
from simulated_pyjapc import PyJapc


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LsaSelector-PyJapc interaction example")
        self.japc = PyJapc(selector="LEI.USER.ZERO")

        lsa_selector = LsaSelector(parent=self, model=SampleLsaSelectorModel(accelerator=LsaSelectorAccelerator.LEIR))
        lsa_selector.select_user(self.japc.selector)
        lsa_selector.userSelectionChanged.connect(self.on_new_selector)

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout()
        self.centralWidget().setLayout(layout)

        layout.addWidget(lsa_selector)
        layout.addSpacing(5)

        self.label = QLabel("Data here")
        layout.addWidget(self.label)
        layout.addSpacing(5)

        self.resubscribe()

        self.resize(450, 200)

    def on_new_selector(self, sel):
        self.japc.selector = sel
        self.resubscribe()

    def resubscribe(self):
        self.japc.clearSubscriptions()
        try:
            self.japc.subscribeParam("DemoDevice/Acquisition#Demo", onValueReceived=self.on_value_received)
            self.japc.startSubscriptions()
        except ValueError as e:
            self.label.setText(str(e))

    def on_value_received(self, _, val):
        self.label.setText(val)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
