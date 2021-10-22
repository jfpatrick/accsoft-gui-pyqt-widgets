"""
The configuration used when creating the plot can also be changed after the creation. This example shows
a window with different input elements that can be used to change the configuration on a running plot that
is displaying data.
"""

import sys
import pyqtgraph as pg
from qtpy.QtWidgets import (QApplication, QGridLayout, QMainWindow, QWidget, QComboBox, QSpinBox, QLabel, QCheckBox,
                            QFrame)
from accwidgets.graph import TimeSpan, ExPlotWidgetConfig, ExPlotWidget, PlotWidgetStyle
from accwidgets.qt import exec_app_interruptable
from example_sources import SinusCurveSource, SinusCurveSourceEmitTypes


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph dynamic plotting style example")
        # In the beginning we want to show 10 seconds of data
        self.time_span = TimeSpan(left=10.0, right=0.0)
        # Start by showing cyclic plot curves
        plot_config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.CYCLIC_PLOT,
                                         time_progress_line=False,
                                         time_span=self.time_span)
        self.plot = ExPlotWidget(config=plot_config)
        # Two sources of sinus curves with different update frequencies
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=0.0,
                                                        y_offset=0,
                                                        updates_per_second=20,
                                                        types_to_emit=[SinusCurveSourceEmitTypes.POINT]))
        # Second curve should be plotted against a second independent Y-axis
        self.plot.add_layer(layer_id="layer_1")
        self.plot.addCurve(data_source=SinusCurveSource(x_offset=0.0,
                                                        y_offset=5,
                                                        updates_per_second=5,
                                                        types_to_emit=[SinusCurveSourceEmitTypes.POINT]),
                           layer="layer_1",
                           sybol="o",
                           symbolPen="g",
                           pen="y")
        # Let's draw a static, horizontal line with y=0
        line = pg.InfiniteLine(pos=0.0, angle=0)
        self.plot.addItem(line)
        # Let all Y-axes range be set automatically depending on their shown data
        self.plot.enableAutoRange()
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot, 0, 0, 1, 14)
        self.style_combobox = QComboBox()
        self.style_combobox.addItems(["Cyclic", "Scrolling"])
        main_layout.addWidget(QLabel("Plot Style"))
        main_layout.addWidget(self.style_combobox)
        self.add_layout_separator(main_layout)
        self.time_span_input_left = QSpinBox()
        self.time_span_input_left.setValue(int(self.time_span.left_boundary_offset))
        self.time_span_input_left.setRange(1, 100)
        self.time_span_input_left.setSuffix(" s")
        main_layout.addWidget(QLabel("Left Time Span Boundary"))
        main_layout.addWidget(self.time_span_input_left)
        self.add_layout_separator(main_layout)
        main_container.setLayout(main_layout)
        self.time_span_input_right = QSpinBox()
        self.time_span_left_checkbox = QCheckBox()
        self.time_line_checkbox = QCheckBox()
        self.time_span_left_checkbox.setChecked(False)
        self.time_span_input_right.setRange(-10, 10)
        self.time_span_input_right.setValue(0)
        self.time_span_input_right.setSuffix(" s")
        main_layout.addWidget(QLabel("Right Time Span Boundary"))
        main_layout.addWidget(self.time_span_input_right)
        self.add_layout_separator(main_layout)
        main_layout.addWidget(QLabel("Ignore Left Border"))
        main_layout.addWidget(self.time_span_left_checkbox)
        self.add_layout_separator(main_layout)
        main_layout.addWidget(QLabel("Show time line"))
        main_layout.addWidget(self.time_line_checkbox)
        main_container.setLayout(main_layout)
        # As soon as one of the inputs have been changed, we take the
        # value and update our plots configuration accordingly
        self.style_combobox.currentTextChanged.connect(self.change_plot_config)
        self.time_span_input_left.valueChanged.connect(self.change_plot_config)
        self.time_span_input_right.valueChanged.connect(self.change_plot_config)
        self.time_span_left_checkbox.stateChanged.connect(self.change_plot_config)
        self.time_line_checkbox.stateChanged.connect(self.change_plot_config)

    @staticmethod
    def add_layout_separator(layout: QGridLayout):
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

    def change_plot_config(self, *_):
        """Change the plot's configuration with the values from the inputs."""
        ts_left = self.time_span_input_left.value()
        ts_right = self.time_span_input_right.value()
        ts_left_ignored = self.time_span_left_checkbox.isChecked()
        style = (PlotWidgetStyle.CYCLIC_PLOT if self.style_combobox.currentText() == "Cyclic"
                 else PlotWidgetStyle.SCROLLING_PLOT)
        if ts_left_ignored and style == PlotWidgetStyle.SCROLLING_PLOT:
            ts = TimeSpan(right=ts_right)
        else:
            ts = TimeSpan(left=ts_left, right=ts_right)
        plot_config = ExPlotWidgetConfig(plotting_style=style,
                                         time_progress_line=self.time_line_checkbox.isChecked(),
                                         time_span=ts)
        self.plot.update_config(config=plot_config)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
