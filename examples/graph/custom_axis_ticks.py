"""
This example shows the easiest way to introduce custom ticks to one
of the plot's axes.
"""

import sys
from typing import List

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

from accwidgets import graph as accgraph
from example_sources import SinusCurveSource


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    def __init__(self, *args, **kwargs):
        """Create a window containing a scatter plot with 'raw' data and a
        line that fits a sinus curve into it."""
        super().__init__(*args, **kwargs)
        # Data Source, Curve and Plot
        sinus_source = SinusCurveSource(0, 0)
        self.plot = accgraph.ScrollingPlotWidget(
            parent=self,
            time_span=accgraph.TimeSpan(10.0),
        )
        self.live_curve = self.plot.addCurve(data_source=sinus_source)
        # To change the way the axis displays values, we can replace its
        # tickStrings function with another callable
        self.plot.getAxis("left").tickStrings = self.custom_tick_strings
        # Setting up our window and layout
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)

    def custom_tick_strings(self,
                            values: List[float],
                            scale: float,
                            spacing: float) -> List[str]:
        """Custom tick generation from float values

        This function will replace negative values on the axis with the
        word 'negative' and positive values with 'positive'

        Args:
            values: Positions from the axis that are supposed to be labeled
            scale: See AxisItem Documentation
            spacing: See AxisItem Documentation

        Returns:
            New value labels for the axis
        """
        return ["negative" if v < 0 else "positive" for v in values]


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
