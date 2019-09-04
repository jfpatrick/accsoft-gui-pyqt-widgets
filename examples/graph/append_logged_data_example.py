"""
Example for an system that not only emits single live points but also
saved points that will be emitted later.
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
        data_source_1 = example_sources.LoggingCurveDataSource(updates_per_second=60)
        plot_config = accgraph.ExPlotWidgetConfig(
            cycle_size=25,
            plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
            time_progress_line=False,
            scrolling_plot_fixed_x_range=True,
            scrolling_plot_fixed_x_range_offset=0
        )
        self.plot = accgraph.ExPlotWidget()
        self.plot.update_configuration(config=plot_config)
        self.plot.addCurve(data_source=data_source_1, pen={"color": "b", "width": 2})
        self.plot.setYRange(-1, 1)
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
