"""
This example shows the easiest way to introduce custom ticks to one of the plot's axes.
"""

import sys
from typing import List
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import ScrollingPlotWidget, TimeSpan
from example_sources import SinusCurveSource

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Graph custom axis ticks example")
        self.plot = ScrollingPlotWidget(parent=self,
                                        time_span=TimeSpan(right=10.0))
        self.live_curve = self.plot.addCurve(data_source=SinusCurveSource(0, 0))

        # To change the way the axis displays values, we can replace its
        # "tickStrings" method with another callable
        self.plot.getAxis("left").tickStrings = self.custom_tick_strings

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.resize(800, 600)

    def custom_tick_strings(self, values: List[float], scale: float, spacing: float) -> List[str]:
        """
        Custom tick generation from float values.

        This method replaces negative values on the axis with the label '-' and non-negative values with '+'.

        Args:
            values: Positions from the axis that are supposed to be labeled.
            scale: See AxisItem Documentation.
            spacing: See AxisItem Documentation.

        Returns:
            New value labels for the axis.
        """
        _ = scale
        _ = spacing
        return ["-" if v < 0 else "+" for v in values]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
