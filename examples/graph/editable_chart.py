"""
Example of one plot with a simple standard curve with
the standard plot configuration.
"""

import sys

from qtpy.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QMainWindow,
    QWidget,
    QLabel,
)
from qtpy.QtCore import Qt

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    def __init__(self, *args, **kwargs):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__(*args, **kwargs)
        # Data sources for our two plots
        self._cs_source = accgraph.UpdateSource()
        # Display data directly on the GUI
        self._edit_ds = example_sources.EditableSinusCurveDataSource(
            self._cs_source.new_data)
        self._edit_ds_2 = example_sources.EditableSinusCurveDataSource(
            self._cs_source.new_data)
        # Plot widgets, one for the local data and one for the control system
        self.local = accgraph.EditablePlotWidget()
        self.local_2 = accgraph.EditablePlotWidget()
        self.control_system = accgraph.StaticPlotWidget()
        # Local and Control System Curves
        curve = self.local.addCurve(data_source=self._edit_ds)
        self.local_2.addCurve(data_source=self._edit_ds_2)
        # Per default the selected points are unlabeled, with this property we
        # can activate it
        curve.selection.points_labeled = True
        self.control_system.addCurve(data_source=self._cs_source)
        # Bar with buttons for editing the local plot
        self.bar = accgraph.EditingToolBar()
        self.bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.bar.connect(self.local)
        self.bar.connect(self.local_2)
        self.bar.setFloatable(True)
        # Windowing & Layouting
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout()
        main_container.setLayout(main_layout)
        # Add widgets
        main_layout.addWidget(QLabel("Editable plots:"))
        main_layout.addWidget(self.local)
        main_layout.addWidget(self.local_2)
        self.addToolBar(self.bar)
        main_layout.addWidget(QLabel("Last sent value from both plots:"))
        main_layout.addWidget(self.control_system)


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
