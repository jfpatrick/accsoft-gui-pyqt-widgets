"""
Example for creating a gui with an ui file from designer
with the AccPyQtGraph QtDesigner plugin.
The UI file contains the layout of the window as well as
each plot with its configuration. Layers and curves are
not added in Designer but by hand after loading the UI file.
"""

import sys
import os
import random
from datetime import datetime

from qtpy import QtWidgets, QtCore, uic
import pyqtgraph as pg

import accsoft_gui_pyqt_widgets.graph as accgraph


class Ui(
    QtWidgets.QMainWindow,
):

    """
    Window which's content is loaded from the 'plot.ui' UI File created with Qt Designer.
    """

    def __init__(self):
        super(Ui, self).__init__()
        # References to the plots from the ui file with typing info for auto completion
        self.static_plot: accgraph.StaticPlotWidget
        self.scrolling_plot: accgraph.ScrollingPlotWidget
        self.sliding_plot: accgraph.SlidingPlotWidget
        # Load UI file with given name
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plot.ui")
        uic.loadUi(file_path, self)
        # Create items to add to the plots
        sliding_item = accgraph.LivePlotCurve.create(plot_item=self.sliding_plot.plotItem, data_source=RandomDataSource(500))
        scrolling_item_1 = accgraph.LivePlotCurve.create(plot_item=self.scrolling_plot.plotItem, data_source=RandomDataSource(1000))
        scrolling_item_2 = accgraph.LivePlotCurve.create(plot_item=self.scrolling_plot.plotItem, data_source=RandomDataSource(500))
        static_item_1 = pg.BarGraphItem(x=[0.0, 1.0, 2.0, 3.0], height=[1.0, 0.5, -0.5, 1.0], width=0.75)
        static_item_2 = pg.PlotDataItem(y=[1.0, 0.5, -0.5, 1.0])
        # Add items
        self.static_plot.plotItem.addItem(static_item_1)
        self.static_plot.plotItem.addItem(static_item_2, layer="layer_0")
        self.scrolling_plot.plotItem.addItem(scrolling_item_1)
        self.scrolling_plot.plotItem.addItem(scrolling_item_2, layer="layer_0")
        self.sliding_plot.plotItem.addItem(sliding_item)
        # Set ranges for the plots
        self.show()


class RandomDataSource(accgraph.UpdateSource):
    """Some thing that emits a signal with a single float"""

    def __init__(self, update_freq: float = 50):
        super().__init__()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.emit)
        self.timer.start(update_freq)

    def emit(self):
        """Emit new float value"""
        self.sig_data_update[accgraph.PointData].emit(
            accgraph.PointData(
                x_value=datetime.now().timestamp(),
                y_value=random.uniform(0.0, 10.0)
            )
        )


def run():
    """Run Application"""
    app = QtWidgets.QApplication(sys.argv)
    _ = Ui()
    app.exec_()


if __name__ == "__main__":
    run()
