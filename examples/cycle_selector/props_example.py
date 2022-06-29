"""
This is a more complex example that lets you configure the CycleSelector widget via UI, and experience its behavior
and errors, given certain constraints. For instance, requireSelector will raise an error if no selector is provided.
Similarly, enforcedDomain will make sure that a selector for the specific machine is given.
"""

import sys
from typing import Optional, Tuple
from qtpy.QtCore import QSignalBlocker
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QCheckBox, QLineEdit, QFrame, QLabel
from accwidgets.cycle_selector import CycleSelector
from accwidgets.qt import exec_app_interruptable


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("CycleSelector configuration example")

        layout = QVBoxLayout()

        selector = CycleSelector(parent=self)
        selector.valueChanged.connect(self.update_curr_val)
        self.selector = selector
        layout.addWidget(selector)

        sep = QFrame()
        sep.setFrameStyle(QFrame.HLine)
        layout.addWidget(sep)

        line = QLineEdit()
        line.setPlaceholderText("MACHINE (Press Enter to submit)")
        line.setText(selector.enforcedDomain)
        line.returnPressed.connect(self.update_domain)
        form = QFormLayout()
        form.addRow("Enforced domain:", line)
        layout.addLayout(form)

        chkbx = QCheckBox("Allow only *.USER.* selector")
        chkbx.setChecked(selector.onlyUsers)
        chkbx.stateChanged.connect(self.set_only_users)
        layout.addWidget(chkbx)

        chkbx = QCheckBox("Offer artificial *.USER.ALL selector")
        chkbx.setChecked(selector.allowAllUser)
        chkbx.stateChanged.connect(self.set_user_all)
        layout.addWidget(chkbx)

        chkbx = QCheckBox("Always require a selector")
        chkbx.setChecked(selector.requireSelector)
        chkbx.stateChanged.connect(self.set_require_sel)
        layout.addWidget(chkbx)

        line = QLineEdit()
        line.setPlaceholderText("MACHINE.GROUP.LINE (Press Enter to submit)")
        line.setText(selector_to_str(selector.value))
        line.returnPressed.connect(self.update_widget_val)
        form = QFormLayout()
        form.addRow("Value:", line)
        layout.addLayout(form)

        sep = QFrame()
        sep.setFrameStyle(QFrame.HLine)
        layout.addWidget(sep)

        val = QLabel()
        self.val = val
        self.update_curr_val(selector_to_str(selector.value))
        layout.addWidget(val)

        err = QLabel()
        self.err = err
        layout.addWidget(err)

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(layout)
        self.resize(400, 200)

    def set_only_users(self):
        try:
            self.selector.onlyUsers = self.sender().isChecked()
        except Exception as e:  # noqa: B902
            self.show_err(e)  # FIXME: Somehow on double tap the checkbox does get set
            blocker = QSignalBlocker(self.sender())
            self.sender().setChecked(self.selector.onlyUsers)
            blocker.unblock()
        else:
            self.show_err(None)

    def set_user_all(self):
        try:
            self.selector.allowAllUser = self.sender().isChecked()
        except Exception as e:  # noqa: B902
            self.show_err(e)
            blocker = QSignalBlocker(self.sender())
            self.sender().setChecked(self.selector.allowAllUser)
            blocker.unblock()
        else:
            self.show_err(None)

    def set_require_sel(self):
        try:
            self.selector.requireSelector = self.sender().isChecked()
        except Exception as e:  # noqa: B902
            self.show_err(e)
            blocker = QSignalBlocker(self.sender())
            self.sender().setChecked(self.selector.requireSelector)
            blocker.unblock()
        else:
            self.show_err(None)

    def update_widget_val(self):
        try:
            self.selector.value = self.sender().text()
        except Exception as e:  # noqa: B902
            self.show_err(e)
            self.sender().setText(selector_to_str(self.selector.value))
        else:
            self.show_err(None)

    def update_domain(self):
        try:
            self.selector.enforcedDomain = self.sender().text()
        except Exception as e:  # noqa: B902
            self.show_err(e)
            self.sender().setText(self.selector.enforcedDomain)
        else:
            self.show_err(None)

    def update_curr_val(self, val: str):
        self.val.setText(f"Currently selected: {val or None}")
        print(f"New cycle: {val or None}")

    def show_err(self, e: Optional[Exception]):
        if e:
            self.err.setText(f"Error: {e!s}")
        else:
            self.err.setText(None)


def selector_to_str(val: Optional[Tuple[str, str, str]]) -> str:
    return ".".join(val) if val is not None else ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))