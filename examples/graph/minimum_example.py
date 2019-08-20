"""
Simple example for a widget without configuration and timing source
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
        data_source_1 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=0, updates_per_second=5
        )
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
            time_progress_line=False,
        )
        self.plot = accgraph.ExPlotWidget(config=plot_config)
        self.plot.addCurve(data_source=data_source_1)
        # Uncomment for second curve in additional layer
        # self.plot.plotItem.add_layer_with_y_axis(layer_identifier="layer_1")
        # self.plot.add_curve(layer="layer_1", data_source=data_source_1)
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
