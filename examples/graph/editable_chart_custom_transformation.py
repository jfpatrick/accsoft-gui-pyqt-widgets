"""
This example shows how to add a custom transformation to our Editing Tool Bar.
"""

import sys
from copy import deepcopy

import numpy as np
from qtpy.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QMainWindow,
    QWidget,
    QAction,
)
from qtpy.QtCore import Qt
import qtawesome as qta
import accwidgets.graph as accgraph

import example_sources


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plot = accgraph.EditablePlotWidget()
        source = example_sources.EditableSinusCurveDataSource()
        curve: accgraph.EditablePlotCurve = self.plot.addCurve(data_source=source)
        curve.selection.points_labeled = True

        self.bar = accgraph.EditingToolBar()
        self.bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.bar.connect(self.plot)

        # To add a transformation function, we need a QAction we can display
        # and the function
        self.avg_action = QAction(qta.icon("fa5.gem"), "Average")
        self.bar.add_transformation(action=self.avg_action,
                                    transformation=self.avg)

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.addToolBar(self.bar)
        self.show()

    @staticmethod
    def avg(curve: accgraph.CurveData) -> accgraph.CurveData:
        """ Transformation Function for the selected data
        It is save for us to operate directly on the curve, since it is
        only a copy.

        Args:
            curve: selected points we want to transform

        Returns:
            transformed version of the passed points
        """
        curve = deepcopy(curve)
        curve.y = np.average(curve.y)
        return curve


if __name__ == "__main__":
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())
