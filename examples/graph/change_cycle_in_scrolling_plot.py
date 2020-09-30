"""
The configuration used when creating the plot can also be changed
to a later time after the creation. This example will show a window with
different input elements that can be used to change this configuration
on a running plot that is displaying data with different visualizations.
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget, QSpinBox, QLabel

from accwidgets import graph as accgraph
import example_sources


# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Our plot should initially show 10 seconds of data
        time_span = 10.0
        # 4 different sources for updates for 4 different types of data
        # visualization we want to add to our plot
        data_source_1 = example_sources.SinusCurveSource(x_offset=0.0,
                                                         y_offset=0,
                                                         updates_per_second=20,
                                                         types_to_emit=[
                                                             example_sources.SinusCurveSourceEmitTypes.POINT,
                                                         ])
        data_source_2 = example_sources.SinusCurveSource(x_offset=0.0,
                                                         y_offset=3,
                                                         updates_per_second=1,
                                                         types_to_emit=[
                                                             example_sources.SinusCurveSourceEmitTypes.BAR,
                                                         ])
        data_source_3 = example_sources.SinusCurveSource(x_offset=0.0,
                                                         y_offset=6,
                                                         updates_per_second=2,
                                                         types_to_emit=[
                                                             example_sources.SinusCurveSourceEmitTypes.INJECTIONBAR,
                                                         ])
        data_source_4 = example_sources.SinusCurveSource(x_offset=0.0,
                                                         y_offset=9,
                                                         updates_per_second=0.2,
                                                         types_to_emit=[
                                                             example_sources.SinusCurveSourceEmitTypes.INFINITELINE,
                                                         ])
        # We want a plot with an fixed scrolling range, which means
        # we display always 10 seconds of data, even if there is less than
        # 10 seconds of data available to keep the x range from changing
        # in its scaling level
        self.plot = accgraph.ScrollingPlotWidget(
            time_span=accgraph.TimeSpan(left=time_span),
        )
        # We add two seperate layers with their own y axis to our plot
        self.plot.add_layer(layer_id="layer_1")
        self.plot.add_layer(layer_id="layer_2")
        # We add 4 different types of data visualization to our plot
        # that are attached to their own source of data
        self.plot.addCurve(data_source=data_source_1, pen="b")
        self.plot.addBarGraph(data_source=data_source_2, width=0.25, layer="layer_1", pen="g")
        self.plot.addInjectionBar(data_source=data_source_3, layer="layer_2", pen="y")
        self.plot.addTimestampMarker(data_source=data_source_4)
        # Let's make all y axes in the plot scale automatically so they fit
        # the data they are displaying
        self.plot.enableAutoRange()
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot, 0, 0, 1, 4)
        self._create_time_span_config_elements(main_layout, time_span)
        main_container.setLayout(main_layout)

    def _create_time_span_config_elements(
            self,
            main_layout: QGridLayout,
            time_span: float,
    ):
        """
        To change the plots configuration for the time span, we add
        some
        """
        # Input for the time span of which the displayed data should be
        self.time_span_input = QSpinBox()
        self.time_span_input.setValue(time_span)
        self.time_span_input.setRange(1, 100)
        label_2 = QLabel("s Left Boundary")
        main_layout.addWidget(self.time_span_input)
        main_layout.addWidget(label_2)
        # Offset for the above mentioned time span.
        self.offset_input = QSpinBox()
        self.offset_input.setRange(-10.0, 10.0)
        self.offset_input.setValue(0.0)
        label_3 = QLabel("s Right Boundary")
        main_layout.addWidget(self.offset_input)
        main_layout.addWidget(label_3)
        # Update the plots configuration on changes from the input elements
        self.time_span_input.valueChanged.connect(self.change_plot_config)
        self.offset_input.valueChanged.connect(self.change_plot_config)

    def change_plot_config(self, *_):
        """Change plot configuration depending on the input"""
        time_span = accgraph.TimeSpan(
            left=self.time_span_input.value(),
            right=self.offset_input.value(),
        )
        plot_config = accgraph.ExPlotWidgetConfig(
            plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
            time_progress_line=False,
            time_span=time_span,
        )
        self.plot.update_config(config=plot_config)


def run():
    """Run Application"""
    app = QApplication(sys.argv)
    gui = MainWindow()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
