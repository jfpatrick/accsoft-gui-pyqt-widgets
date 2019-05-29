"""

"""

import sys
import itertools
from typing import List
from qtpy.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, QLabel
from accsoft_gui_pyqt_widgets.graph import ExtendedPlotWidgetConfig,\
    ExtendedPlotWidget, PlotWidgetStyle, PastSinCurveSource, LocalTimerTimingSource, ScrollingPlotItem, SlidingPointerPlotItem, ExtendedPlotItem


class ConfigDemoWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__()

        plots: List[ExtendedPlotItem] = []

        # Two Threads for Time and Data updates
        timing_source = LocalTimerTimingSource()
        sinus_data_source = PastSinCurveSource()

        cycle_sizes = [10.0]
        plotting_styles = [[PlotWidgetStyle.SCROLLING_PLOT, ScrollingPlotItem], [PlotWidgetStyle.SLIDING_POINTER, SlidingPointerPlotItem]]
        time_progress_line_values = [False, True]
        v_draw_line_values = [False, True]
        h_draw_line_values = [False, True]
        draw_point_values = [False, True]
        combined = itertools.product(cycle_sizes, plotting_styles, time_progress_line_values, v_draw_line_values,
                                     h_draw_line_values, draw_point_values)
        for item in combined:
            plot_config = ExtendedPlotWidgetConfig(
                cycle_size=item[0],
                plotting_style=item[1][0],
                time_progress_line=item[2],
                v_draw_line=item[3],
                h_draw_line=item[4],
                draw_point=item[5]
            )
            plots.append(ExtendedPlotWidget(timing_source=timing_source, data_source=sinus_data_source, config=plot_config))

        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        for index, plot in enumerate(plots):
            main_layout.addWidget(plot, int(index / 8), index % 8)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    gui = ConfigDemoWindow()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
