"""
The configuration used when creating the plot can also be changed
to a later time after the creation. This example will show a window with
different input elements that can be used to change this configuration
on a running plot that is displaying data.
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget, QComboBox, QSpinBox, QLabel, QCheckBox, QFrame
import pyqtgraph as pg

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # In the beginning we want to show 10 seconds of data
        self.time_span = accgraph.TimeSpan(left=10.0, right=0.0)
        # Two sources of sinus curves with different update frequencies
        data_source_1 = example_sources.SinusCurveSource(x_offset=0.0,
                                                         y_offset=0,
                                                         updates_per_second=20,
                                                         types_to_emit=[
                                                             example_sources.SinusCurveSourceEmitTypes.POINT,
                                                         ])
        data_source_2 = example_sources.SinusCurveSource(x_offset=0.0,
                                                         y_offset=5,
                                                         updates_per_second=5,
                                                         types_to_emit=[
                                                             example_sources.SinusCurveSourceEmitTypes.POINT,
                                                         ])
        # In the beginning the plot should show the data as sliding pointer curves
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.CYCLIC_PLOT,
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
        self.time_span_input_left.valueChanged.connect(self.change_plot_config)
        self.time_span_input_right.valueChanged.connect(self.change_plot_config)
        self.time_span_left_checkbox.stateChanged.connect(self.change_plot_config)
        self.time_line_checkbox.stateChanged.connect(self.change_plot_config)

    def create_input(self, main_layout: QGridLayout, main_container: QWidget):
        """Create input fields for different plot config parameters"""
        # Style Combobox that lets you switch the plot's display style
        self.style_combobox = QComboBox()
        label_1 = QLabel("Plot Style")
        self.style_combobox.addItems(["Cyclic", "Scrolling"])
        main_layout.addWidget(label_1)
        main_layout.addWidget(self.style_combobox)
        self.add_sperator(main_layout)
        # Input that lets you change the time span of the displayed data
        self.time_span_input_left = QSpinBox()
        self.time_span_input_left.setValue(int(self.time_span.left_boundary_offset))
        self.time_span_input_left.setRange(1, 100)
        label_2 = QLabel("Left Time Span Boundary")
        main_layout.addWidget(label_2)
        main_layout.addWidget(self.time_span_input_left)
        self.add_sperator(main_layout)
        main_container.setLayout(main_layout)
        # Input that lets you add an offset to the time span of the
        # displayed data.
        self.time_span_input_right = QSpinBox()
        # If activated the value of the offset_input is used
        self.time_span_left_checkbox = QCheckBox()
        # If activated, the current timestamp is represented
        # by a vertical line with a label showing the current time
        self.time_line_checkbox = QCheckBox()
        self.time_span_left_checkbox.setChecked(False)
        self.time_span_input_right.setRange(-10.0, 10.0)
        self.time_span_input_right.setValue(0.0)
        label_3 = QLabel("Right Time Span Boundary")
        label_4 = QLabel("Ignore Left Border")
        label_5 = QLabel("Show time line")
        main_layout.addWidget(label_3)
        main_layout.addWidget(self.time_span_input_right)
        self.add_sperator(main_layout)
        main_layout.addWidget(label_4)
        main_layout.addWidget(self.time_span_left_checkbox)
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
        ts_left = self.time_span_input_left.value()
        ts_right = self.time_span_input_right.value()
        ts_left_ignored = self.time_span_left_checkbox.isChecked()
        style = accgraph.PlotWidgetStyle.CYCLIC_PLOT if self.style_combobox.currentText() == "Cyclic" else accgraph.PlotWidgetStyle.SCROLLING_PLOT
        if ts_left_ignored and style == accgraph.PlotWidgetStyle.SCROLLING_PLOT:
            ts = accgraph.TimeSpan(None, ts_right)
        else:
            ts = accgraph.TimeSpan(ts_left, ts_right)
        # Create new configuration object according to the values
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=style,
            time_progress_line=self.time_line_checkbox.isChecked(),
            time_span=ts,
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
