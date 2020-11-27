"""
Example for creating a window from Qt Designer file featuring the StaticPlotWidget, ScrollingPlotWidget and
CyclicPlotWidget Qt Designer plugins. Layers and curves are not added in Qt Designer but by hand after
loading the UI file.
"""

import sys
import random
import pyqtgraph as pg
from pathlib import Path
from datetime import datetime
from qtpy.uic import loadUi
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QApplication, QMainWindow
from accwidgets.graph import (StaticPlotWidget, ScrollingPlotWidget, CyclicPlotWidget, LivePlotCurve, UpdateSource,
                              PointData)


# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.static_plot: StaticPlotWidget = None
        self.scrolling_plot: ScrollingPlotWidget = None
        self.sliding_plot: CyclicPlotWidget = None
        loadUi(Path(__file__).absolute().parent / "designer_example.ui", self)
        cyclic_item = LivePlotCurve.from_plot_item(plot_item=self.cyclic_plot.plotItem,
                                                   data_source=RandomDataSource(500))
        scrolling_item_1 = LivePlotCurve.from_plot_item(plot_item=self.scrolling_plot.plotItem,
                                                        data_source=RandomDataSource(1000))
        scrolling_item_2 = LivePlotCurve.from_plot_item(plot_item=self.scrolling_plot.plotItem,
                                                        data_source=RandomDataSource(500))
        static_item_1 = pg.BarGraphItem(x=[0.0, 1.0, 2.0, 3.0],
                                        height=[1.0, 0.5, -0.5, 1.0],
                                        width=0.75)
        static_item_2 = pg.PlotDataItem(y=[1.0, 0.5, -0.5, 1.0])
        self.static_plot.plotItem.addItem(static_item_1)
        self.static_plot.plotItem.addItem(static_item_2, layer="y_0")
        self.scrolling_plot.plotItem.addItem(scrolling_item_1)
        self.scrolling_plot.plotItem.addItem(scrolling_item_2, layer="y_0")
        self.cyclic_plot.plotItem.addItem(cyclic_item)


class RandomDataSource(UpdateSource):

    def __init__(self, update_freq: float = 50):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.emit)
        self.timer.start(update_freq)

    def emit(self):
        data = PointData(x=datetime.now().timestamp(),
                         y=random.uniform(0.0, 10.0))
        self.send_data(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
