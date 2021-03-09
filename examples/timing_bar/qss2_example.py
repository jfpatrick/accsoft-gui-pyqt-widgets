"""
This is the alternative color scheme to the one proposed in "qss_example.py", still using QSS stylesheets.
Everything else stays the same.
"""

import sys
from qtpy.QtWidgets import QApplication
from accwidgets.qt import exec_app_interruptable
from qss_example import MainWindow
from dark_mode import dark_mode_style


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setStyleSheet(dark_mode_style + """
TimingBar {
    qproperty-timingMarkColor: red;
    qproperty-timingMarkTextColor: black;
    qproperty-normalCycleColor: rgb(131, 129, 95);
    qproperty-highlightedCycleColor: rgb(67, 61, 50);
    qproperty-backgroundPatternColor: rgb(206, 198, 148);
    qproperty-backgroundPatternAltColor: rgb(197, 189, 141);
    qproperty-backgroundBottomColor: rgb(236, 228, 182);
    qproperty-backgroundTopColor: rgb(198, 192, 154);
    qproperty-backgroundBottomAltColor: rgb(222, 215, 172);
    qproperty-backgroundTopAltColor: rgb(181, 175, 141);
    qproperty-textColor: black;
    qproperty-errorTextColor: rgb(221, 9, 2);
    qproperty-frameColor: rgb(218, 218, 218);
}
    """)
    window.show()
    sys.exit(exec_app_interruptable(app))
