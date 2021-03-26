"""
This example shows the basic usage of the EditablePlotWidget with the standard curve
and standard plot configuration. In the window, 2 top graphs represent separate curve editors, that
can be used to propagate changes to the same control system location. In this case, committing changes
from either will override previous changes, even if they were sent from another graph. The bottom graph
represents the values that are recorded in the control system. Switching between graphs is done by double-clicking
them in the editing mode.
"""

import sys
import pyqtgraph as pg
from qtpy.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QWidget, QLabel
from qtpy.QtGui import QColor
from qtpy.QtCore import Qt
from accwidgets.graph import UpdateSource, EditablePlotWidget, StaticPlotWidget, EditingToolBar
from accwidgets.qt import exec_app_interruptable
from example_sources import EditableSinusCurveDataSource


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Simple EditablePlotWidget example")

        # Widgets to simultaneously edit the same curve
        self.plot1 = EditablePlotWidget()
        self.plot2 = EditablePlotWidget()

        # This plot represents the data that is actually saved in the control system
        self.remote_plot = StaticPlotWidget()

        self.gateway_data_source = UpdateSource()
        self.plot1.addCurve(data_source=EditableSinusCurveDataSource(edit_callback=self.gateway_data_source.send_data),
                            pen=pg.mkPen(color=QColor("yellow"), width=2))
        self.plot2.addCurve(data_source=EditableSinusCurveDataSource(edit_callback=self.gateway_data_source.send_data),
                            pen=pg.mkPen(color=QColor("yellow"), width=2))
        self.remote_plot.addCurve(data_source=self.gateway_data_source)

        self.bar = EditingToolBar()
        self.bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.bar.connect(self.plot1)
        self.bar.connect(self.plot2)
        self.bar.setFloatable(True)

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(QLabel("Editable plots:"))
        main_layout.addWidget(self.plot1)
        main_layout.addWidget(self.plot2)
        self.addToolBar(self.bar)
        main_layout.addWidget(QLabel("Last sent value from both plots:"))
        main_layout.addWidget(self.remote_plot)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
