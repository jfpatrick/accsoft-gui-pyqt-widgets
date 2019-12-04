"""
Simple example for the usage of the ExtendPlotWidget
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

from accwidgets import graph as accgraph
import example_sources


class MainWindow(QMainWindow):

    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We want to create a scrolling plot widget showing 30 seconds of data
        self.plot = accgraph.ScrollingPlotWidget(
            time_span=30.0,
            is_xrange_fixed=True
        )
        # 5 different sources for data for different types of data visualization
        data_source_1 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=0, updates_per_second=20
        )
        data_source_2 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=4, updates_per_second=1
        )
        data_source_3 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=-4, updates_per_second=1, types_to_emit=[
                example_sources.SinusCurveSourceEmitTypes.BAR
            ]
        )
        data_source_4 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=-8, updates_per_second=0.5, types_to_emit=[
                example_sources.SinusCurveSourceEmitTypes.INJECTIONBAR
            ]
        )
        data_source_5 = example_sources.SinusCurveSource(
            x_offset=0.0, y_offset=-8, updates_per_second=0.2, types_to_emit=[
                example_sources.SinusCurveSourceEmitTypes.INFINITELINE
            ]
        )
        # Let's add a second y axis to our plot
        self.plot.add_layer(
            layer_id="layer_1"
        )
        # A bar graph with green bars and blue borders
        bargraph = self.plot.addBarGraph(
            layer="layer_1",
            data_source=data_source_3,
            brush="g",
            pen="b",
            width=0.75
        )
        # A visual item visually similar to an error bar with an
        # label representing the injection of particles
        injectionbar = self.plot.addInjectionBar(
            layer="layer_1",
            data_source=data_source_4,
            pen={"color": "b", "width": 3}
        )
        # Vertical Lines with labels that mark specific timestamps
        self.plot.addTimestampMarker(
            data_source=data_source_5
        )
        # As in pyqtgraph, scrolling scatter plots are curves with
        # symbols but without a pen connecting each data point
        scatter_plot = self.plot.addCurve(
            data_source=data_source_2,
            pen=None,
            symbol="o",
            symbolPen={"color": "w", "width": 1},
            symbolSize=8,
            symbolBrush=(255, 0, 0, 255)
        )
        # A red curve with a thickness of 3
        curve_plot = self.plot.addCurve(
            data_source=data_source_1, pen={"color": "r", "width": 3}
        )
        # Let's create a legend item and add all our created items to it
        legend_item = self.plot.addLegend()
        legend_item.addItem(item=curve_plot, name="Curve")
        legend_item.addItem(item=bargraph, name="Bar Graph")
        legend_item.addItem(item=scatter_plot, name="Scatter Plot")
        legend_item.addItem(item=injectionbar, name="Injection Bar")
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    _ = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
