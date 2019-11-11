"""
Simple example for the usage of the ExtendPlotWidget
"""

import sys

import pyqtgraph as pg
from qtpy.QtWidgets import (QApplication, QGridLayout, QMainWindow,
                            QWidget)

import accsoft_gui_pyqt_widgets.graph as accgraph


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__(*args, **kwargs)
        # Create example update sources for data and time
        # Create configuration that describes the way the data is supposed to be plotted
        self.plot = accgraph.ExPlotWidget()
        plot_item = self.plot.plotItem
        plot_item.getAxis("left").setLabel("Δ")
        plot_item.add_layer(
            identifier="sigma_layer",
            text="Σ",
        )
        plot_item.add_layer(
            identifier="omega_layer",
            showValues=False,
            maxTickLength=0,
            text="Ω",
        )
        plot_item.addItem(pg.PlotDataItem(x=[1, 2, 3], y=[101, 102, 103]))
        plot_item.addItem(
            layer="sigma_layer",
            item=pg.ScatterPlotItem(x=[1, 2, 3], y=[102, 103, 104]),
        )
        plot_item.addItem(
            layer="omega_layer",
            item=pg.BarGraphItem(
                x=[1, 2, 3], width=0.05, height=[101, 102, 103]
            ),
        )
        self.plot.setRange(yRange=(100.0, 104.0))
        self.plot.setRange(yRange=(100.0, 105.0), layer="sigma_layer")
        self.plot.setRange(yRange=(-110.0, 110.0), layer="omega_layer")
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
