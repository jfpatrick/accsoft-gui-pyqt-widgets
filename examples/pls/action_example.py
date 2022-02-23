"""
This example shows the simplest way of using CycleSelectorAction for integrating into user-defined button. Not
in this example, but the same action can be integrated into a QMenu menu. Whenever selector is updated, it will
appear in the label inside the window. CycleSelectorAction provides a wrapper that displays the
CycleSelector widget in a popup.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QToolBar, QLabel, QToolButton
from accwidgets.pls import PlsSelectorAction
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PlsSelector popup action example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        self.label = QLabel()
        action = PlsSelectorAction(parent=self) #, text="Choose PLS")
        action.valueChanged.connect(self.update_label)

        btn = QToolButton(self)
        btn.setAutoRaise(True)
        btn.setDefaultAction(action)
        btn.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(btn)

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().addWidget(self.label)
        self.resize(400, 170)
        self.update_label(None)

    def update_label(self, val: str):
        self.label.setText(f"Selected PLS: {val or None}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
