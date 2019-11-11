"""
Example of changing the timeSpan size and offset in a running realtime-plot
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget, QSpinBox, QLabel

import accsoft_gui_pyqt_widgets.graph as accgraph
import example_sources


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__()
        time_span = 10.0
        data_source_1 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=0, updates_per_second=20, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.POINT]
        )
        data_source_2 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=3, updates_per_second=1, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.BAR]
        )
        data_source_3 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=6, updates_per_second=2, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.INJECTIONBAR]
        )
        data_source_4 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=9, updates_per_second=0.2, types_to_emit=[example_sources.SinusCurveSourceEmitTypes.INFINITELINE]
        )
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
            time_progress_line=False,
            time_span=time_span,
            scrolling_plot_fixed_x_range=True,
            scrolling_plot_fixed_x_range_offset=0.0
        )
        self.plot = accgraph.ExPlotWidget(config=plot_config)
        self.plot.addCurve(data_source=data_source_1, pen="b")
        self.plot.plotItem.add_layer(identifier="layer_1")
        self.plot.addBarGraph(data_source=data_source_2, width=0.25, layer="layer_1", pen="g")
        self.plot.plotItem.add_layer(identifier="layer_2")
        self.plot.addInjectionBar(data_source=data_source_3, layer="layer_2", pen="y")
        self.plot.addTimestampMarker(data_source=data_source_4)
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot, 0, 0, 1, 4)
        self.plot.plotItem.enableAutoRange()
        # time span input
        self.time_span_input = QSpinBox()
        self.time_span_input.setValue(time_span)
        self.time_span_input.setRange(1, 100)
        label_2 = QLabel("s Time Span")
        main_layout.addWidget(self.time_span_input)
        main_layout.addWidget(label_2)
        main_container.setLayout(main_layout)
        # time span offset input
        self.offset_input = QSpinBox()
        self.offset_input.setRange(-10.0, 10.0)
        self.offset_input.setValue(0.0)
        label_3 = QLabel("s Offset")
        main_layout.addWidget(self.offset_input)
        main_layout.addWidget(label_3)
        main_container.setLayout(main_layout)
        # Connect for changes
        self.time_span_input.valueChanged.connect(self.change_plot_config)
        self.offset_input.valueChanged.connect(self.change_plot_config)

    def change_plot_config(self, *_):
        """Change plot configuration depending on the input"""
        time_span = self.time_span_input.value()
        offset = self.offset_input.value()
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
            time_progress_line=False,
            time_span=time_span,
            scrolling_plot_fixed_x_range=True,
            scrolling_plot_fixed_x_range_offset=offset
        )
        self.plot.update_configuration(config=plot_config)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    gui = MainWindow()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
