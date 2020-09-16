"""
This example shows the use of ApplicationFrame window with TimingBar enabled. For the sake of example, we are using
custom model that does not require connection to real devices (same model as used in examples of TimingBar itself).
Timing domain can be configured on the model of the TimingBar widget. Menus here are configured to partially recreate
the experience provided by "CERN Application Frame" Qt Designer template.
"""

import sys
from qtpy.QtWidgets import QApplication, QLabel, QMenuBar, QAction
from qtpy.QtCore import Qt
from accwidgets.app_frame import ApplicationFrame
from accwidgets.timing_bar import TimingBarDomain
from sample_model import SampleTimingBarModel

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = QLabel("My custom application contents")
    my_widget.setStyleSheet("background-color: yellow; color: black")
    my_widget.setAlignment(Qt.AlignCenter)
    font = my_widget.font()
    font.setPointSize(32)
    my_widget.setFont(font)
    window = ApplicationFrame(use_timing_bar=True)
    window.timing_bar.model = SampleTimingBarModel(domain=TimingBarDomain.LHC)
    window.setWindowTitle("TimingBar Example")
    window.setCentralWidget(my_widget)
    window.resize(800, 600)
    window.show()
    menu_bar = QMenuBar()
    file = menu_bar.addMenu("File")
    quit = file.addAction("Exit", window.close)
    quit.setMenuRole(QAction.QuitRole)
    menu_bar.addMenu("View")
    help = menu_bar.addMenu("Help")
    about = help.addAction("About", window.showAboutDialog)
    about.setMenuRole(QAction.AboutRole)
    window.setMenuBar(menu_bar)
    sys.exit(app.exec_())
