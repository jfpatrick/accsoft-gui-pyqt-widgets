"""
The configuration used when creating the plot can also be changed after the creation. This example shows a window
with ability to adjust the visible time span.
"""

import sys
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget, QSpinBox, QLabel
from accwidgets.graph import ScrollingPlotWidget, TimeSpan, ExPlotWidgetConfig, PlotWidgetStyle
from accwidgets.qt import exec_app_interruptable
from example_sources import SinusCurveSourceEmitTypes, SinusCurveSource


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph dynamic time span example")
        # Plot will initially show 10 seconds of data
        time_span = 10
        data_source_curve = SinusCurveSource(x_offset=0.0,
                                             y_offset=0,
                                             updates_per_second=20,
                                             types_to_emit=[SinusCurveSourceEmitTypes.POINT])
        data_source_bar = SinusCurveSource(x_offset=0.0,
                                           y_offset=3,
                                           updates_per_second=1,
                                           types_to_emit=[SinusCurveSourceEmitTypes.BAR])
        data_source_injection = SinusCurveSource(x_offset=0.0,
                                                 y_offset=6,
                                                 updates_per_second=2,
                                                 types_to_emit=[SinusCurveSourceEmitTypes.INJECTION_BAR])
        data_source_timestamp = SinusCurveSource(x_offset=0.0,
                                                 y_offset=9,
                                                 updates_per_second=0.2,
                                                 types_to_emit=[SinusCurveSourceEmitTypes.INFINITE_LINE])
        # We want a plot with an fixed scrolling range, which means
        # we display always 10 seconds of data, even if there is less than
        # 10 seconds of data available to keep the X-range from changing
        # in its scaling level.
        self.plot = ScrollingPlotWidget(time_span=TimeSpan(left=time_span))
        self.plot.add_layer(layer_id="layer_1")
        self.plot.add_layer(layer_id="layer_2")
        # We add 4 different types of data visualization to our plot
        # that are attached to their own source of data
        self.plot.addCurve(data_source=data_source_curve, pen="b")
        self.plot.addBarGraph(data_source=data_source_bar, width=0.25, layer="layer_1", pen="g")
        self.plot.addInjectionBar(data_source=data_source_injection, layer="layer_2", pen="y")
        self.plot.addTimestampMarker(data_source=data_source_timestamp)
        # Let's make all Y-axes in the plot scale automatically to fit displayed data
        self.plot.enableAutoRange()
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot, 0, 0, 1, 4)
        self.time_span_input = QSpinBox()
        self.time_span_input.setValue(time_span)
        self.time_span_input.setRange(1, 100)
        self.time_span_input.setSuffix(" s")
        main_layout.addWidget(self.time_span_input)
        main_layout.addWidget(QLabel("Left Boundary"))
        # Offset for the above mentioned time span.
        self.offset_input = QSpinBox()
        self.offset_input.setRange(-10, 10)
        self.offset_input.setValue(0)
        self.offset_input.setSuffix(" s")
        main_layout.addWidget(self.offset_input)
        main_layout.addWidget(QLabel("s Right Boundary"))
        # Update the plots configuration on changes from the input elements
        self.time_span_input.valueChanged.connect(self.change_plot_config)
        self.offset_input.valueChanged.connect(self.change_plot_config)
        main_container.setLayout(main_layout)

    def change_plot_config(self, *_):
        """Change plot configuration depending on the input"""
        time_span = TimeSpan(left=self.time_span_input.value(),
                             right=self.offset_input.value())
        plot_config = ExPlotWidgetConfig(plotting_style=PlotWidgetStyle.SCROLLING_PLOT,
                                         time_progress_line=False,
                                         time_span=time_span)
        self.plot.update_config(config=plot_config)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(exec_app_interruptable(app))
