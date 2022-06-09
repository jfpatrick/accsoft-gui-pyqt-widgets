"""
This example shows how a cycle selector (via CycleSelectorAction) could be integrated with the TimingBar.
Choosing a specific selector, will reconfigure TimingBar to display the timing of the respective timing domain.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QToolBar, QToolButton
from accwidgets.cycle_selector import CycleSelectorAction, CycleSelectorValue
from accwidgets.timing_bar import TimingBar, TimingBarDomain
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("CycleSelector-TimingBar integration example")
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        action = CycleSelectorAction(parent=self)
        action.value = CycleSelectorValue(domain="PSB", group="USER", line="ALL")
        action.requireSelector = True
        action.onlyUsers = True
        self.selector_action = action

        btn = QToolButton(self)
        btn.setAutoRaise(True)
        btn.setDefaultAction(action)
        btn.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(btn)

        timing_bar = TimingBar()
        self.timing_bar = timing_bar
        toolbar.addWidget(timing_bar)

        action.valueChanged.connect(self.update_timing_bar)

        # Create some margin to the window edges
        self.resize(700, 100)
        self.update_timing_bar()

    def update_timing_bar(self):
        selector = self.selector_action.value
        assert selector is not None
        try:
            timing_domain = TimingBarDomain(selector.domain)
        except ValueError as e:
            print(e)
        else:
            self.timing_bar.domain = timing_domain


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
