"""
This example shows fitting a curve into a plot showing live data
as a scatter plot.
"""

import sys
from datetime import datetime
import random
import math

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from qtpy.QtCore import QTimer
from scipy import optimize
import numpy as np

from accwidgets import graph as accgraph
import pyqtgraph as pg


class RoughSinusSource(accgraph.UpdateSource):

    def __init__(self):
        """
        This Source will emit some offset sinus values we will later fit a
        sinus curve into.
        """
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_values)
        self.timer.start(1000 / 60)

    def _create_new_values(self) -> None:
        """Simulate some sinus values with some offset."""
        new_data = accgraph.PointData(
            x=datetime.now().timestamp(),
            y=math.sin(datetime.now().timestamp()) + random.uniform(-0.5, 0.5),
            check_validity=False,
        )
        self.send_data(new_data)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        """
        Create a window containing a scatter plot with 'raw' data as a scatter
        plot and a line that fits a sinus curve into it.

        Args:
            args: QMainWindow positional arguments
            kwargs: QMainWindow keyword arguments
        """
        super().__init__(*args, **kwargs)
        # We feed the live curve with imperfect sinus values
        rough_sinus = RoughSinusSource()
        # Now we create a scrolling live data plot showing 10s of data
        self.plot = accgraph.ScrollingPlotWidget(
            parent=self,
            time_span=accgraph.TimeSpan(left=10.0),
        )
        # This scatter plot will display our raw sinus data
        self.live_curve = self.plot.addCurve(data_source=rough_sinus,
                                             pen=None,
                                             symbol="o")
        # We want to update our fitted curve every time the live curve gets
        # updated
        self.live_curve.model().sig_data_model_changed.connect(self.update_fitted_curve)
        # Since the fitted curve is not appending live data, we will use a
        # normal pyqtgraph curve to display it.
        self.fitted_curve = pg.PlotDataItem()
        self.plot.addItem(self.fitted_curve)
        # Setting up our window and layout
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)

    def _sin_func(self, x: np.ndarray, a: float, b: float) -> np.ndarray:
        """
        The function we will use for the curve fitting.

        Args:
            x: x values which's sinus value we want to calculate
            a: parameter for the sinus calculation
            b: parameter for the sinus calculation

        Returns:
            sinus values for the given x values and parameters
        """
        return a * np.sin(b * x)

    def update_fitted_curve(self):
        """
        Update the fitted curve in the plot using the data that is currently
        displayed in the plot.
        """
        # The area of data which is currently visible in the plot
        # We need this because the data model's buffer holds more data than is
        # displayed
        start = self.plot.plotItem.time_span.start
        end = self.plot.plotItem.time_span.end
        # Now we can get the x and y values in this visible range
        x_values, y_values = self.live_curve.model().subset_for_xrange(start=start,
                                                                       end=end)
        try:
            # Now we can fit our sinus curve in the visible data range
            params, _ = optimize.curve_fit(self._sin_func, x_values, y_values)
        except TypeError:
            # In case there are not yet enough points for curve fitting, a Type
            # Error is raised -> we can safely ignore it
            return
        fitted_y = self._sin_func(x_values, params[0], params[1])
        # Replace the curve's displayed data -> The x range will be the same
        # as the one of the live curve
        self.fitted_curve.setData(x_values, fitted_y)


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
