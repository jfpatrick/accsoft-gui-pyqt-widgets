"""
Simple example for the usage of the ExtendPlotWidget
"""

import sys
from qtpy.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout
from accsoft_gui_pyqt_widgets.graph import ExtendedPlotWidgetConfig,\
    ExtendedPlotWidget, PlotWidgetStyle, SinusCurveSource, LocalTimerTimingSource


class MainWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__()
        cycle_size_in_s = 10.0
        # Create example update sources for data and time
        timing_source = LocalTimerTimingSource()
        data_source = SinusCurveSource()
        # Create configuration that describes the way the data is supposed to be plotted
        plot_config = ExtendedPlotWidgetConfig(
            cycle_size=cycle_size_in_s,
            plotting_style=PlotWidgetStyle.SCROLLING_PLOT,
            time_progress_line=False,
            v_draw_line=False,
            h_draw_line=False,
            draw_point=False
        )
        self.plot = ExtendedPlotWidget(timing_source=timing_source, data_source=data_source, config=plot_config)
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
    gui = MainWindow()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
