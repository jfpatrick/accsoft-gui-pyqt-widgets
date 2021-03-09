"""
This example shows how to add a custom transformation to EditingToolBar that is used in tandem with
EditablePlotWidget.
"""

import sys
import numpy as np
import qtawesome as qta
from qtpy.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QWidget, QAction
from qtpy.QtCore import Qt
from accwidgets.graph import EditablePlotWidget, EditingToolBar, EditablePlotCurve, CurveData
from accwidgets.qt import exec_app_interruptable
from example_sources import EditableSinusCurveDataSource


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("EditablePlotWidget custom transformation example")

        self.plot = EditablePlotWidget()
        curve: EditablePlotCurve = self.plot.addCurve(data_source=EditableSinusCurveDataSource())
        curve.selection.points_labeled = True

        self.bar = EditingToolBar()
        self.bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.bar.connect(self.plot)

        # To add a transformation function, we need a QAction we can display and the function
        self.avg_action = QAction(qta.icon("fa5.gem"), "Average")
        self.bar.add_transformation(action=self.avg_action,
                                    transformation=avg_transformation)

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
        self.addToolBar(self.bar)


def avg_transformation(curve: CurveData) -> CurveData:
    """
    Transformation function for the selected data. Input data is a copy of the original, so it is
    safe to modify it directly.
    """
    curve.y = np.average(curve.y)
    return curve


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
