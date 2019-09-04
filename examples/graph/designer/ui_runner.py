"""
Example for creating a gui with an ui file from designer
with the AccPyQtGraph QtDesigner plugin.
The UI file contains the layout of the window as well as
each plot with its configuration. Layers and curves are
not added in Designer but by hand after loading the UI file.
"""

import sys
import random
from datetime import datetime

from qtpy import QtWidgets, QtCore, uic
import accsoft_gui_pyqt_widgets.graph as accgraph
import pyqtgraph


class Ui(
    QtWidgets.QMainWindow,
):
    def __init__(self):
        super(Ui, self).__init__()
        # References to the plots from the ui file with typing info for auto completion
        self.widget_1: accgraph.ExPlotWidget
        self.widget_2: accgraph.ExPlotWidget
        self.widget_3: accgraph.ExPlotWidget
        # Load UI file with given name
        uic.loadUi('plot.ui', self)
        # Create items to add to the plots
        item = accgraph.LivePlotCurve.create(plot_item=self.widget_1.plotItem, data_source=RandomDataSource(50))
        item_2 = accgraph.LivePlotCurve.create(plot_item=self.widget_2.plotItem, data_source=RandomDataSource(1000))
        item_3 = accgraph.LivePlotCurve.create(plot_item=self.widget_2.plotItem, data_source=RandomDataSource(500))
        item_4 = pyqtgraph.BarGraphItem(x=[0.0, 1.0, 2.0, 3.0], height=[1.0, 0.5, -0.5, 1.0], width=0.75)
        item_5 = pyqtgraph.PlotDataItem(y=[1.0, 0.5, -0.5, 1.0])
        # Add layers
        self.widget_2.plotItem.add_layer(identifier="2.1")
        self.widget_3.plotItem.add_layer(identifier="3.1")
        # Add items
        self.widget_1.plotItem.addItem(item)
        self.widget_2.plotItem.addItem(item_2)
        self.widget_2.plotItem.addItem(item_3, layer="2.1")
        self.widget_3.plotItem.addItem(item_4, layer="3.1")
        self.widget_3.plotItem.addItem(item_5)
        # Set ranges for the plots
        self.widget_1.plotItem.vb.setYRange(0.0, 11.0)
        self.widget_2.plotItem.vb.setYRange(-10, 10)
        self.widget_2.plotItem.get_layer_by_identifier(layer_identifier="2.1").view_box.setYRange(0.0, 20.0)
        self.widget_3.plotItem.vb.setYRange(-1.0, 5.0)
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

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()