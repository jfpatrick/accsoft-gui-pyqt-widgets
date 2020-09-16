"""
This example shows the subclassing of the ApplicationFrame class. In this example, subclass forces the usage of
TimingBar widget, that is disabled in ApplicationFrame by default. For the sake of example, we are using
custom model that does not require connection to real devices (same model as used in examples of TimingBar itself).
For the sake of simplicity, default timing domain is used. Menus here are configured to partially recreate the
experience provided by "CERN Application Frame" Qt Designer template.
"""

import sys
from qtpy.QtWidgets import QApplication, QLabel, QMenuBar, QAction
from qtpy.QtCore import Qt
from accwidgets.app_frame import ApplicationFrame
from sample_model import SampleTimingBarModel


# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MyMainWindow(ApplicationFrame):

    def __init__(self):
        super().__init__(use_timing_bar=True, use_log_console=True)
        self.timing_bar.model = SampleTimingBarModel()
        self.setWindowTitle("Subclassing Example")

        my_widget = QLabel("My custom application contents")
        my_widget.setStyleSheet("background-color: yellow; color: black")
        my_widget.setAlignment(Qt.AlignCenter)
        font = my_widget.font()
        font.setPointSize(32)
        my_widget.setFont(font)
        self.setCentralWidget(my_widget)

        menu_bar = QMenuBar()
        file = menu_bar.addMenu("File")
        quit = file.addAction("Exit", self.close)
        quit.setMenuRole(QAction.QuitRole)
        menu_bar.addMenu("View")
        help = menu_bar.addMenu("Help")
        about = help.addAction("About", self.showAboutDialog)
        about.setMenuRole(QAction.AboutRole)
        self.setMenuBar(menu_bar)
        self.resize(800, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
