"""
This is the example of stylizing the widget with custom colors using QSS stylesheets.
We are presenting the color scheme that matches the dark mode style. Colors here are similar to the programmatic ones
in "palette_example.py".
For the sake of example, we are using custom model that does not require connection to real devices.
"""

import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from accwidgets.timing_bar import TimingBar
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleTimingBarModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("TimingBar QSS example")

        style = Path(__file__).parent.parent / "_common" / "dark.qss"
        dark_mode = style.read_text()
        self.setStyleSheet(dark_mode + """
TimingBar {
    qproperty-timingMarkColor: red;
    qproperty-timingMarkTextColor: black;
    qproperty-normalCycleColor: rgb(191, 191, 191);
    qproperty-highlightedCycleColor: rgb(236, 228, 182);
    qproperty-backgroundPatternColor: black;
    qproperty-backgroundPatternAltColor: rgb(48, 48, 48);
    qproperty-backgroundTopColor: rgb(79, 79, 79);
    qproperty-backgroundBottomColor: rgb(38, 38, 38);
    qproperty-backgroundTopAltColor: rgb(85, 85, 85);
    qproperty-backgroundBottomAltColor: rgb(49, 49, 49);
    qproperty-textColor: rgb(238, 238, 238);
    qproperty-frameColor: black;
    qproperty-errorTextColor: rgb(221, 9, 2);
}
""")

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
    sys.exit(exec_app_interruptable(app))
