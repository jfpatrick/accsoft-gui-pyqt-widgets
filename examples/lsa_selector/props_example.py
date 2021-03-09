"""
This example shows the way to configure the widget with additional properties. It builds on top of "basic_example.py",
extending it with configuration UI. For the sake of example, we are using custom model
that does not require connection to LSA servers.
"""

import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QCheckBox, QVBoxLayout, QGroupBox
from accwidgets.lsa_selector import LsaSelector, AbstractLsaSelectorContext
from accwidgets.qt import exec_app_interruptable
from sample_model import SampleLsaSelectorModel


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("LsaSelector properties example")

        lsa_selector = LsaSelector(parent=self, model=SampleLsaSelectorModel(categories={
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.MD,
            AbstractLsaSelectorContext.Category.REFERENCE,
            AbstractLsaSelectorContext.Category.ARCHIVED,
            AbstractLsaSelectorContext.Category.OBSOLETE,
            AbstractLsaSelectorContext.Category.TEST,
        }))
        lsa_selector.contextSelectionChanged.connect(lambda ctx: print(f"New LSA context: {ctx}"))
        self.lsa = lsa_selector

        # Create some margin to the window edges
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QVBoxLayout())
        self.centralWidget().layout().addWidget(lsa_selector)

        layout = QHBoxLayout()
        name_filter = QCheckBox("Show name filter")

        def toggle_name_filter():
            lsa_selector.showNameFilter = not lsa_selector.showNameFilter

        name_filter.stateChanged.connect(toggle_name_filter)
        layout.addWidget(name_filter)

        category_filter = QCheckBox("Show category filter")

        def toggle_category_filter():
            lsa_selector.showCategoryFilter = not lsa_selector.showCategoryFilter

        category_filter.stateChanged.connect(toggle_category_filter)
        layout.addWidget(category_filter)

        resident_filter = QCheckBox("Show only resident contexts")
        resident_filter.setChecked(True)

        def toggle_resident_filter():
            lsa_selector.fetchResidentOnly = not lsa_selector.fetchResidentOnly

        resident_filter.stateChanged.connect(toggle_resident_filter)
        layout.addWidget(resident_filter)

        self.centralWidget().layout().addLayout(layout)

        group = QGroupBox("Fetched context categories")
        group.setLayout(QVBoxLayout())

        op_cat = QCheckBox(LsaSelector.ContextCategories.OPERATIONAL.name)
        op_cat.setChecked(True)

        def toggle_op_filter():
            if op_cat.isChecked():
                lsa_selector.contextCategories |= LsaSelector.ContextCategories.OPERATIONAL
            else:
                lsa_selector.contextCategories -= LsaSelector.ContextCategories.OPERATIONAL

        op_cat.stateChanged.connect(toggle_op_filter)
        group.layout().addWidget(op_cat)

        md_cat = QCheckBox(LsaSelector.ContextCategories.MD.name)
        md_cat.setChecked(True)

        def toggle_md_filter():
            if md_cat.isChecked():
                lsa_selector.contextCategories |= LsaSelector.ContextCategories.MD
            else:
                lsa_selector.contextCategories -= LsaSelector.ContextCategories.MD

        md_cat.stateChanged.connect(toggle_md_filter)
        group.layout().addWidget(md_cat)

        ref_cat = QCheckBox(LsaSelector.ContextCategories.REFERENCE.name)
        ref_cat.setChecked(True)

        def toggle_ref_filter():
            if ref_cat.isChecked():
                lsa_selector.contextCategories |= LsaSelector.ContextCategories.REFERENCE
            else:
                lsa_selector.contextCategories -= LsaSelector.ContextCategories.REFERENCE

        ref_cat.stateChanged.connect(toggle_ref_filter)
        group.layout().addWidget(ref_cat)

        arch_cat = QCheckBox(LsaSelector.ContextCategories.ARCHIVED.name)
        arch_cat.setChecked(True)

        def toggle_arch_filter():
            if arch_cat.isChecked():
                lsa_selector.contextCategories |= LsaSelector.ContextCategories.ARCHIVED
            else:
                lsa_selector.contextCategories -= LsaSelector.ContextCategories.ARCHIVED

        arch_cat.stateChanged.connect(toggle_arch_filter)
        group.layout().addWidget(arch_cat)

        obs_cat = QCheckBox(LsaSelector.ContextCategories.OBSOLETE.name)
        obs_cat.setChecked(True)

        def toggle_obs_filter():
            if obs_cat.isChecked():
                lsa_selector.contextCategories |= LsaSelector.ContextCategories.OBSOLETE
            else:
                lsa_selector.contextCategories -= LsaSelector.ContextCategories.OBSOLETE

        obs_cat.stateChanged.connect(toggle_obs_filter)
        group.layout().addWidget(obs_cat)

        test_cat = QCheckBox(LsaSelector.ContextCategories.TEST.name)
        test_cat.setChecked(True)

        def toggle_test_filter():
            if test_cat.isChecked():
                lsa_selector.contextCategories |= LsaSelector.ContextCategories.TEST
            else:
                lsa_selector.contextCategories -= LsaSelector.ContextCategories.TEST

        test_cat.stateChanged.connect(toggle_test_filter)
        group.layout().addWidget(test_cat)

        self.centralWidget().layout().addWidget(group)

        self.resize(500, 450)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
