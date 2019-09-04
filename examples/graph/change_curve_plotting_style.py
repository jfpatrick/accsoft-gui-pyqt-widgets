"""
Example of changing the Plot Configuration in a running realtime-plot
"""

import sys

import numpy as np
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget, QComboBox, QSpinBox, QLabel, QCheckBox

import accsoft_gui_pyqt_widgets.graph as accgraph
import pyqtgraph as pg
import example_sources


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__()
        self.cycle_size = 10.0
        data_source_1 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=0, updates_per_second=20, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.POINT]
        )
        data_source_2 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=5, updates_per_second=5, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.POINT]
        )
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.SLIDING_POINTER,
            time_progress_line=False,
            cycle_size=self.cycle_size,
        )
        self.plot = accgraph.ExPlotWidget(config=plot_config)
        self.plot.addCurve(data_source=data_source_1)
        self.plot.plotItem.add_layer(identifier="layer_1")
        self.plot.addCurve(data_source=data_source_2, layer_identifier="layer_1", sybol="o", symbolPen="g", pen="y")
        line = pg.InfiniteLine(pos=0.0, angle=0)
        self.plot.addItem(line)
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot, 0, 0, 1, 10)
        self.plot.plotItem.enableAutoRange()
        self.create_input(main_layout, main_container)
        main_container.setLayout(main_layout)
        # Connect for changes
        self.style_combobox.currentTextChanged.connect(self.change_plot_config)
        self.cycle_size_input.valueChanged.connect(self.change_plot_config)
        self.offset_input.valueChanged.connect(self.change_plot_config)
        self.offset_checkbox.stateChanged.connect(self.change_plot_config)
        self.time_line_checkbox.stateChanged.connect(self.change_plot_config)

    def create_input(self, main_layout: QGridLayout, main_container: QWidget):
        """Create input fields for different plot config parameters"""
        # Style Combobox
        self.style_combobox = QComboBox()
        label_1 = QLabel("Plot Style")
        self.style_combobox.addItems(["Sliding", "Scrolling"])
        main_layout.addWidget(self.style_combobox)
        main_layout.addWidget(label_1)
        # Cycle Size Input
        self.cycle_size_input = QSpinBox()
        self.cycle_size_input.setValue(self.cycle_size)
        self.cycle_size_input.setRange(1, 100)
        label_2 = QLabel("s Cycle")
        main_layout.addWidget(self.cycle_size_input)
        main_layout.addWidget(label_2)
        main_container.setLayout(main_layout)
        # Cycle Offset Input
        self.offset_input = QSpinBox()
        self.offset_checkbox = QCheckBox()
        self.time_line_checkbox = QCheckBox()
        self.offset_checkbox.setChecked(False)
        self.offset_input.setRange(-10.0, 10.0)
        self.offset_input.setValue(0.0)
        label_3 = QLabel("s Offset")
        label_4 = QLabel("Fixed x-range")
        label_5 = QLabel("Show time line")
        main_layout.addWidget(self.offset_input)
        main_layout.addWidget(label_3)
        main_layout.addWidget(label_4)
        main_layout.addWidget(self.offset_checkbox)
        main_layout.addWidget(label_5)
        main_layout.addWidget(self.time_line_checkbox)

    def change_plot_config(self, *args):
        """Change the plot's configuration with the values from the inputs"""
        cycle_size = self.cycle_size_input.value()
        fixed_range = self.offset_checkbox.isChecked()
        offset = self.offset_input.value() if fixed_range else np.nan
        style = accgraph.PlotWidgetStyle.SLIDING_POINTER if self.style_combobox.currentText() == "Sliding" else accgraph.PlotWidgetStyle.SCROLLING_PLOT
        # Create new configuration object
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=style,
            time_progress_line=self.time_line_checkbox.isChecked(),
            cycle_size=cycle_size,
            scrolling_plot_fixed_x_range=fixed_range,
            scrolling_plot_fixed_x_range_offset=offset
        )
        # update plot with the new configuration
        self.plot.update_configuration(config=plot_config)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    gui = MainWindow()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()