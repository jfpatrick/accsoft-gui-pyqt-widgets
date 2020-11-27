"""
This example shows combination of different data presentation types in a ScrollingPlotWidget. The displayed styles are:
curve, bar graph, injection bar graph, scatter plot and timestamp marker. Each of the data items is attached to
its own data source producing a sin curve.
"""

import sys
from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget
from accwidgets.graph import ScrollingPlotWidget, TimeSpan
from example_sources import SinusCurveSource, SinusCurveSourceEmitTypes

# Allow smooth exit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Graph data representation types example")
        self.plot = ScrollingPlotWidget(time_span=TimeSpan(left=30.0))
        # 5 different sources for data for different types of data visualization
        data_source_curve = SinusCurveSource(x_offset=0.0, y_offset=0, updates_per_second=20)
        data_source_scatter_plot = SinusCurveSource(x_offset=0.0, y_offset=4, updates_per_second=1)
        data_source_bar_graph = SinusCurveSource(x_offset=0.0,
                                                 y_offset=-4,
                                                 updates_per_second=1,
                                                 types_to_emit=[SinusCurveSourceEmitTypes.BAR])
        data_source_injection_bar = SinusCurveSource(x_offset=0.0,
                                                     y_offset=-8,
                                                     updates_per_second=0.5,
                                                     types_to_emit=[SinusCurveSourceEmitTypes.INJECTION_BAR])
        data_source_timestamp_marker = SinusCurveSource(x_offset=0.0,
                                                        y_offset=-8,
                                                        updates_per_second=0.2,
                                                        types_to_emit=[SinusCurveSourceEmitTypes.INFINITE_LINE])

        self.plot.add_layer(layer_id="layer_1")

        # A bar graph with green bars and blue borders
        bar_graph = self.plot.addBarGraph(layer="layer_1",
                                          data_source=data_source_bar_graph,
                                          brush="g",
                                          pen="b",
                                          width=0.75)

        # A visual item visually similar to an error bar with an label representing the injection of particles
        injection_bar = self.plot.addInjectionBar(layer="layer_1",
                                                  data_source=data_source_injection_bar,
                                                  pen={
                                                      "color": "b",
                                                      "width": 3,
                                                  })

        # Vertical Lines with labels that mark specific timestamps
        self.plot.addTimestampMarker(data_source=data_source_timestamp_marker)

        # As in PyQtGraph, scrolling scatter plots are curves with # symbols but without a pen
        # connecting each data point
        scatter_plot = self.plot.addCurve(data_source=data_source_scatter_plot,
                                          pen=None,
                                          symbol="o",
                                          symbolPen={
                                              "color": "w",
                                              "width": 1,
                                          },
                                          symbolSize=8,
                                          symbolBrush=(255, 0, 0, 255))

        # A red curve with a thickness of 3
        curve_plot = self.plot.addCurve(data_source=data_source_curve,
                                        pen={
                                            "color": "r",
                                            "width": 3,
                                        })

        # Let's create a legend item and add all our created items to it
        legend_item = self.plot.addLegend()
        legend_item.addItem(item=curve_plot, name="Curve")
        legend_item.addItem(item=bar_graph, name="Bar Graph")
        legend_item.addItem(item=scatter_plot, name="Scatter Plot")
        legend_item.addItem(item=injection_bar, name="Injection Bar")

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
