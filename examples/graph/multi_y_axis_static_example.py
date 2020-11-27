"""
accwidgets graphs offer the possibility to plot against multiple Y-axes. Each additional Y-axis is attached to an
extra view box, the area in which e.g. a curve is drawn in. The Y-axis and its attached view box are grouped
together as a "layer". Each layer has its own user given string identifier. For this example we can use PyQtGraph's
PlotDataItem, which is a simple static curve without extra capabilities. The X-axis is defined by an array of simple
float values, instead of timestamps.
"""

import sys
import pyqtgraph as pg
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import StaticPlotWidget

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Multiple Y-axes StaticPlotWidget example")
        self.plot = StaticPlotWidget()
        self.plot.add_layer(layer_id="sigma_layer")
        # Extra layer that does not display scale values on the axis
        self.plot.add_layer(layer_id="omega_layer",
                            show_values=False,
                            max_tick_length=0)

        self.plot.setLabel(axis="left", text="Δ")
        self.plot.setLabel(axis="omega_layer", text="Ω")
        self.plot.setLabel(axis="sigma_layer", text="Σ")

        self.plot.addItem(pg.PlotDataItem(x=[1, 2, 3], y=[101, 102, 103]))
        self.plot.addItem(layer="sigma_layer", item=pg.ScatterPlotItem(x=[1, 2, 3], y=[102, 103, 104]))
        self.plot.addItem(layer="omega_layer", item=pg.BarGraphItem(x=[1, 2, 3], width=0.05, height=[101, 102, 103]))

        # Each layer can have its own custom y range set
        self.plot.setRange(yRange=(100.0, 104.0),
                           sigma_layer=(100.0, 105.0),
                           omega_layer=(-110.0, 110.0))
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.resize(800, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
