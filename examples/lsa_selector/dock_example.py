"""
This example shows the way of integrating LsaSelector widget into a dock. Here, the widget is accommodated on the left
side of the window inside a QDockWidget. For the sake of example, we are using custom model that does not require
connection to LSA servers.
"""

import sys
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QDockWidget, QLabel
from accwidgets.lsa_selector import LsaSelector, AbstractLsaSelectorContext
from sample_model import SampleLsaSelectorModel

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LsaSelector Dock example")

        lsa_selector = LsaSelector(parent=self, model=SampleLsaSelectorModel())
        lsa_selector.contextSelectionChanged.connect(self._on_select)
        dock = QDockWidget()
        dock.setWidget(lsa_selector)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        # Main contents
        main_widget = QLabel("My custom application contents")
        main_widget.setStyleSheet("background-color: yellow; color: black")
        main_widget.setAlignment(Qt.AlignCenter)
        font = main_widget.font()
        font.setPointSize(22)
        main_widget.setFont(font)
        self.main_widget = main_widget
        self.setCentralWidget(main_widget)

        self.resize(900, 300)

    def _on_select(self, ctx: AbstractLsaSelectorContext):
        self.main_widget.setText(ctx.name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
