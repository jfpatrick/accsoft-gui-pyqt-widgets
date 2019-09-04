"""
Simple example for the usage of the ExtendPlotWidget
"""

import sys

from qtpy.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

import accsoft_gui_pyqt_widgets.graph as accgraph
import example_sources


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__(*args, **kwargs)
        plot_config = accgraph.ExPlotWidgetConfig(
            cycle_size=30,
            plotting_style=accgraph.PlotWidgetStyle.SCROLLING_PLOT,
            time_progress_line=False,
            scrolling_plot_fixed_x_range=True,
            scrolling_plot_fixed_x_range_offset=0.0
        )
        self.plot = accgraph.ExPlotWidget(config=plot_config)
        # Create example update sources for data and time
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
        self.plot.plotItem.add_layer(
            identifier="layer_1"
        )
        # Add graph items to the plot
        bargraph = self.plot.addBarGraph(
            layer_identifier="layer_1",
            data_source=data_source_3,
            brush="g",
            pen="b",
            width=0.75
        )
        injectionbar = self.plot.addInjectionBar(
            layer_identifier="layer_1",
            data_source=data_source_4,
            pen={"color": "b", "width": 3}
        )
        self.plot.addTimestampMarker(
            data_source=data_source_5
        )
        scatter_plot = self.plot.addCurve(
            data_source=data_source_2,
            pen=None,
            symbol="o",
            symbolPen={"color": "w", "width": 1},
            symbolSize=8,
            symbolBrush=(255, 0, 0, 255)
        )
        curve_plot = self.plot.addCurve(data_source=data_source_1, pen={"color": "r", "width": 3})
        # Create Legend
        legend_item = self.plot.plotItem.addLegend()
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
