import sys
import json
from typing import Dict, Any, List, Callable, Optional
from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGroupBox, QLabel, QHBoxLayout
from accwidgets.property_edit import PropertyEdit, PropertyEditField, AbstractPropertyEditLayoutDelegate

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class CustomLayoutDelegate(AbstractPropertyEditLayoutDelegate[QHBoxLayout]):
    """
    Custom delegate that creates horizontal layout, as opposed to default "Form-like" layout.
    """

    def create_layout(self) -> QHBoxLayout:
        return QHBoxLayout()

    def layout_widgets(self,
                       layout: QHBoxLayout,
                       widget_config: List[PropertyEditField],
                       create_widget: Callable[[PropertyEditField, Optional[QWidget]], QWidget],
                       parent: Optional[QWidget] = None):
        # Add new widgets
        for conf in widget_config:
            widget = create_widget(conf, parent)
            layout.addWidget(widget)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        """
        This example embeds a single PropertyEdit widget, which contains 2 fields of different types.
        The purpose is to show how to layout inner widgets differently, than the standard "Form" way.
        The rest of the setup if similar to "amplitude_example.py".
        """
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Custom layout")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setLayout(QVBoxLayout())
        property_edit = PropertyEdit()
        property_edit.buttons = PropertyEdit.Buttons.SET | PropertyEdit.Buttons.GET
        property_edit.sendOnlyUpdatedValues = False
        property_edit.fields = [
            PropertyEditField(field="amplitude", label="Amplitude (mA)", editable=True, type=PropertyEdit.ValueType.REAL),
            PropertyEditField(field="frequency", label="Frequency (Hz)", editable=True, type=PropertyEdit.ValueType.INTEGER),
        ]
        property_edit.layout_delegate = CustomLayoutDelegate()
        property_edit.valueUpdated.connect(self.format_data)
        property_edit.valueRequested.connect(self.create_data_sample)
        self.property_edit = property_edit
        main_widget.layout().addWidget(property_edit)
        main_widget.layout().addStretch()
        res_box = QGroupBox("Sent data sample")
        label = QLabel()
        res_box.setLayout(QVBoxLayout())
        res_box.layout().addWidget(label)
        main_widget.layout().addWidget(res_box)
        self.label = label

        self.show()

    def format_data(self, incoming: Dict[str, Any]):
        formatted_text = json.dumps(incoming, indent=4)
        self.label.setText(formatted_text)

    def create_data_sample(self):
        self.property_edit.setValue({
            "amplitude": 0.5,
            "frequency": 30,
        })


def run():
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
