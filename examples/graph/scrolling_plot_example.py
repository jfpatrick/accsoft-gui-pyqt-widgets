"""
Simple example for the usage of the ExtendPlotWidget
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

import accsoft_gui_pyqt_widgets.graph as accgraph
import example_sources


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__(*args, **kwargs)
        # Create example update sources for data and time
        timing_source = example_sources.LocalTimerTimingSource()
        data_source_1 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=0, updates_per_second=60
        )
        data_source_2 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=3, updates_per_second=60
        )
        data_source_3 = example_sources.SinusCurveSource(
            x_offset=-1.0, y_offset=6, updates_per_second=60
        )
        data_source_4 = example_sources.SinusCurveSource(
            x_offset=1.0, y_offset=9, updates_per_second=60
        )
        # Create configuration that describes the way the data is supposed to be plotted
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
            time_span=10,
            time_progress_line=True,
            scrolling_plot_fixed_x_range=True,
            scrolling_plot_fixed_x_range_offset=1
        )
        self.plot = accgraph.ExPlotWidget(
            timing_source=timing_source, config=plot_config
        )
        self.plot.addCurve(data_source=data_source_1, pen="r")
        self.plot.addCurve(data_source=data_source_2, pen="b")
        self.plot.addCurve(data_source=data_source_3, pen="y")
        self.plot.addCurve(data_source=data_source_4, pen="g")
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
