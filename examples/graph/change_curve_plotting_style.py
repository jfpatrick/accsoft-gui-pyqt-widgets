"""
The configuration used when creating the plot can also be changed
to a later time after the creation. This example will show a window with
different input elements that can be used to change this configuration
on a running plot that is displaying data.
"""

import sys

import numpy as np
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget, QComboBox, QSpinBox, QLabel, QCheckBox, QFrame
import pyqtgraph as pg

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # In the beginning we want to show 10 seconds of data
        self.time_span = 10.0
        # Two sources of sinus curves with different update frequencies
        data_source_1 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=0, updates_per_second=20, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.POINT]
        )
        data_source_2 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=5, updates_per_second=5, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.POINT]
        )
        # In the beginning the plot should show the data as sliding pointer curves
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.SLIDING_POINTER,
            time_progress_line=False,
            time_span=self.time_span,
        )
        self.plot = accgraph.ExPlotWidget(config=plot_config)
        self.plot.addCurve(data_source=data_source_1)
        # Our second curve should be plotted against a second independent y axis
        self.plot.add_layer(layer_id="layer_1")
        self.plot.addCurve(data_source=data_source_2, layer="layer_1", sybol="o", symbolPen="g", pen="y")
        # Let's draw a static, horizontal line with y=0
        line = pg.InfiniteLine(pos=0.0, angle=0)
        self.plot.addItem(line)
        # Let all y axes range be set automatically depending on their shown data
        self.plot.enableAutoRange()
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot, 0, 0, 1, 14)
        self.create_input(main_layout, main_container)
        main_container.setLayout(main_layout)
        # As soon as one of the inputs have been changed, we take the
        # value and update our plots configuration accordingly
        self.style_combobox.currentTextChanged.connect(self.change_plot_config)
        self.time_span_input.valueChanged.connect(self.change_plot_config)
        self.offset_input.valueChanged.connect(self.change_plot_config)
        self.offset_checkbox.stateChanged.connect(self.change_plot_config)
        self.time_line_checkbox.stateChanged.connect(self.change_plot_config)

    def create_input(self, main_layout: QGridLayout, main_container: QWidget):
        """Create input fields for different plot config parameters"""
        # Style Combobox that lets you switch the plot's display style
        self.style_combobox = QComboBox()
        label_1 = QLabel("Plot Style")
        self.style_combobox.addItems(["Sliding", "Scrolling"])
        main_layout.addWidget(label_1)
        main_layout.addWidget(self.style_combobox)
        self.add_sperator(main_layout)
        # Input that lets you change the time span of the displayed data
        self.time_span_input = QSpinBox()
        self.time_span_input.setValue(self.time_span)
        self.time_span_input.setRange(1, 100)
        label_2 = QLabel("Time Span")
        main_layout.addWidget(label_2)
        main_layout.addWidget(self.time_span_input)
        self.add_sperator(main_layout)
        main_container.setLayout(main_layout)
        # Input that lets you add an offset to the time span of the
        # displayed data.
        self.offset_input = QSpinBox()
        # If activated the value of the offset_input is used
        self.offset_checkbox = QCheckBox()
        # If activated, the current timestamp is represented
        # by a vertical line with a label showing the current time
        self.time_line_checkbox = QCheckBox()
        self.offset_checkbox.setChecked(False)
        self.offset_input.setRange(-10.0, 10.0)
        self.offset_input.setValue(0.0)
        label_3 = QLabel("Offset")
        label_4 = QLabel("Fixed x-range")
        label_5 = QLabel("Show time line")
        main_layout.addWidget(label_3)
        main_layout.addWidget(self.offset_input)
        self.add_sperator(main_layout)
        main_layout.addWidget(label_4)
        main_layout.addWidget(self.offset_checkbox)
        self.add_sperator(main_layout)
        main_layout.addWidget(label_5)
        main_layout.addWidget(self.time_line_checkbox)

    @staticmethod
    def add_sperator(layout: QGridLayout):
        """
        For more visual separation we want to add a small vertical line
        between each input element.
        """
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

    def change_plot_config(self, *_) -> None:
        """Change the plot's configuration with the values from the inputs"""
        time_span = self.time_span_input.value()
        fixed_range = self.offset_checkbox.isChecked()
        offset = self.offset_input.value() if fixed_range else np.nan
        style = accgraph.PlotWidgetStyle.SLIDING_POINTER if self.style_combobox.currentText() == "Sliding" else accgraph.PlotWidgetStyle.SCROLLING_PLOT
        # Create new configuration object according to the values
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=style,
            time_progress_line=self.time_line_checkbox.isChecked(),
            time_span=time_span,
            is_xrange_fixed=fixed_range,
            fixed_xrange_offset=offset
        )
        # Update our plot with the new configuration
        self.plot.update_config(config=plot_config)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    gui = MainWindow()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
