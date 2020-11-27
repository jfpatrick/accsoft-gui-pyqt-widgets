"""
Example of a graph that appends incoming live data to pre-existing data taken from the logging system.
Even though the points are not emitted in the order of their timestamps, they are still displayed in the
right order.
"""

import sys
import numpy as np
from typing import List
from datetime import datetime
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import ScrollingPlotWidget, TimeSpan, UpdateSource, PointData, CurveData

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Graph example to append live data to historical")
        data_source = HybridCurveDataSource(updates_per_second=60)
        self.plot = ScrollingPlotWidget(time_span=TimeSpan(left=25.0, right=0.0),
                                        time_progress_line=False)
        # Add a blue curve with a thickness of 2 to our plot
        # Data for the curve is received by the passed data source
        self.plot.addCurve(data_source=data_source,
                           pen={
                               "color": "b",
                               "width": 2,
                           })
        self.plot.setYRange(-1, 1)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.resize(800, 600)


class HybridCurveDataSource(UpdateSource):

    def __init__(self, updates_per_second: int = 60):
        super().__init__()
        self.updates_per_second = updates_per_second
        self.timer_interval_ms = 1000 / updates_per_second
        self.y_values_live: List[float] = list(np.sin(
            np.array(np.arange(start=0.0, stop=720.0, step=60 / self.updates_per_second)) * np.pi / 180.0,
        ))
        self.y_values_logging = [y_value * 0.25 for y_value in self.y_values_live]
        delta = self.timer_interval_ms / (1000 * 2)
        start = datetime.now().timestamp()
        self.x_values_live = [(start + index * delta) for index, value in enumerate(self.y_values_live)]
        self.x_values_logging = [(start - (len(self.y_values_logging) - (index + 1)) * delta)
                                 for index, value in enumerate(self.y_values_logging)]
        self._update_data()
        self.data_length: int = len(self.y_values_live)
        self.current_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._create_new_value)
        self.timer.start(self.timer_interval_ms)

    def _update_data(self):
        last_timestamp = self.x_values_live[-1] if self.x_values_live else datetime.now().timestamp()
        # Half of the actual timer frequency
        delta = self.timer_interval_ms / (1000 * 2)
        self.x_values_logging = [(last_timestamp + index * delta) for index, value in enumerate(self.y_values_live)]
        last_timestamp = self.x_values_logging[-1] if self.x_values_logging else datetime.now().timestamp() + delta
        self.x_values_live = [(last_timestamp + index * delta) for index, value in enumerate(self.y_values_live)]

    def _create_new_value(self):
        if self.current_index < self.data_length:
            self._emit_next_live_point()
            self.current_index += 1
        else:
            self._emit_separator()
            self._emit_data_from_logging_system()
            self.current_index = 0
            self._update_data()

    def _emit_next_live_point(self):
        new_data = PointData(x=self.x_values_live[self.current_index],
                             y=self.y_values_live[self.current_index],
                             check_validity=False)
        self.send_data(new_data)

    def _emit_separator(self):
        separator = PointData(x=np.nan,
                              y=np.nan,
                              check_validity=False)
        self.sig_new_data[PointData].emit(separator)

    def _emit_data_from_logging_system(self):
        curve = CurveData(x=np.array(self.x_values_logging),
                          y=np.array(self.y_values_logging),
                          check_validity=False)
        self.send_data(curve)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
