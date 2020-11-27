"""
This example shows fitting a sinus curve into a plot showing live data as a scatter plot.
"""

import sys
import random
import math
import numpy as np
import pyqtgraph as pg
from datetime import datetime
from scipy import optimize
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from qtpy.QtCore import QTimer
from accwidgets.graph import UpdateSource, PointData, ScrollingPlotWidget, TimeSpan

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Graph curve fitting example")
        update_source = ApproximateSinusSource()
        self.plot = ScrollingPlotWidget(parent=self,
                                        time_span=TimeSpan(left=10.0))
        # This scatter plot will display our raw sinus data
        self.live_curve = self.plot.addCurve(data_source=update_source,
                                             pen=None,
                                             symbol="o")
        # We want to update our fitted curve every time the live curve gets updated
        self.live_curve.model().sig_data_model_changed.connect(self.update_fitted_curve)
        # Since the fitted curve is not appending live data, we will use a normal pyqtgraph curve to display it.
        self.fitted_curve = pg.PlotDataItem()
        self.plot.addItem(self.fitted_curve)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.resize(800, 600)

    def update_fitted_curve(self):
        """
        Update the fitted curve in the plot using the data that is currently
        displayed in the plot.
        """
        # The area of data which is currently visible in the plot. We need this because the data model's
        # buffer may hold more data than is displayed.
        start = self.plot.plotItem.time_span.start
        end = self.plot.plotItem.time_span.end
        # Now we can get the x and y values in this visible range
        x_values, y_values = self.live_curve.model().subset_for_xrange(start=start, end=end)
        # Now we can fit our sinus curve in the visible data range
        try:
            params, _ = optimize.curve_fit(self.fit_sin, x_values, y_values)
        except TypeError:
            # In case there are not yet enough points for curve fitting, a TypeError is raised,
            # so we can safely ignore it
            return
        fitted_y = self.fit_sin(x_values, params[0], params[1])
        # Replace the curve's displayed data, so the x-range will be the same as the one of the live curve
        self.fitted_curve.setData(x_values, fitted_y)

    def fit_sin(self, x: np.ndarray, a: float, b: float) -> np.ndarray:
        """
        The function we will use for the curve fitting.

        Args:
            x: x values, whose sin value we want to calculate
            a: parameter for the sinus calculation
            b: parameter for the sinus calculation

        Returns:
            Sinus values for the given x values and parameters.
        """
        return a * np.sin(b * x)


class ApproximateSinusSource(UpdateSource):

    def __init__(self):
        """Live curve with imperfect sinus values."""
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_values)
        self.timer.start(1000 / 60)

    def _create_new_values(self):
        """Simulate sinus values with random error."""
        new_data = PointData(x=datetime.now().timestamp(),
                             y=math.sin(datetime.now().timestamp()) + random.uniform(-0.5, 0.5),
                             check_validity=False)
        self.send_data(new_data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
