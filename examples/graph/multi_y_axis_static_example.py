"""
ExPlotWidget offers the possibility to plot against multiple
y axes. Each additional y axis is attached to an extra view box,
the area in which e.g. a curve is drawn in. The y-axis and its
attached view box are grouped together as a 'layer'. Each layer has
its own user given string identifier.

For this example we can use PyQtGraph's PlotDataItem, which is a
simple static curve.
"""

import sys

import pyqtgraph as pg
from qtpy.QtWidgets import (QApplication, QGridLayout, QMainWindow,
                            QWidget)

from accwidgets import graph as accgraph

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We want a simple static plot with float values as the x axis instead
        # of times.
        self.plot = accgraph.StaticPlotWidget()
        # Let's add an additional axis
        self.plot.add_layer(
            layer_id="sigma_layer",
        )
        # We can also make the axis not show any values
        self.plot.add_layer(
            layer_id="omega_layer",
            show_values=False,
            max_tick_length=0,
        )
        # Let's make our axes show some text
        self.plot.setLabel(axis="left", text="Δ")
        self.plot.setLabel(axis="omega_layer", text="Ω")
        self.plot.setLabel(axis="sigma_layer", text="Σ")
        # Let's add a standard PyQtGraph curve to our plot
        self.plot.addItem(pg.PlotDataItem(x=[1, 2, 3], y=[101, 102, 103]))
        # PyQtGraph curves can also be displayed in our two new layer
        self.plot.addItem(
            layer="sigma_layer",
            item=pg.ScatterPlotItem(x=[1, 2, 3], y=[102, 103, 104]),
        )
        self.plot.addItem(
            layer="omega_layer",
            item=pg.BarGraphItem(x=[1, 2, 3], width=0.05, height=[101, 102, 103]),
        )
        # Each layer can have its own custom y range set
        self.plot.setRange(
            yRange=(100.0, 104.0),
            sigma_layer=(100.0, 105.0),
            omega_layer=(-110.0, 110.0),
        )
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
