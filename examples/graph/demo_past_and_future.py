"""
Example of Widgets with different time and data sources
"""

import sys
from qtpy.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, QLabel
from accsoft_gui_pyqt_widgets.graph import ExtendedPlotWidgetConfig,\
    ExtendedPlotWidget, PlotWidgetStyle, SinusCurveSource, FutureSinCurveSource, PastSinCurveSource,\
    OneSecDelayedTimingSource, LocalTimerTimingSource, OneSecFutureTimingSource


class DelayDemoWindow(QMainWindow):
    """Example for the usage of the Extended PlotWidget in an QMainWindow"""

    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Create a new MainWindow instance with an Extended Plot Widget"""
        super().__init__()
        cycle_size_in_s = 10.0
        # Two Threads for Time and Data updates
        timing_source = LocalTimerTimingSource()
        timing_source_delayed = OneSecDelayedTimingSource()
        timing_source_future = OneSecFutureTimingSource()
        sinus_data_source = SinusCurveSource()
        future_sin_source = FutureSinCurveSource()
        past_sin_source = PastSinCurveSource()
        sliding_pointer_config = ExtendedPlotWidgetConfig(
            cycle_size=cycle_size_in_s,
            plotting_style=PlotWidgetStyle.SLIDING_POINTER,
            time_progress_line=True,
            v_draw_line=False,
            h_draw_line=False,
            draw_point=True
        )
        self.plot_1 = ExtendedPlotWidget(timing_source=timing_source, data_source=sinus_data_source, config=sliding_pointer_config)
        self.plot_2 = ExtendedPlotWidget(timing_source=timing_source, data_source=future_sin_source, config=sliding_pointer_config)
        self.plot_3 = ExtendedPlotWidget(timing_source=timing_source, data_source=past_sin_source, config=sliding_pointer_config)
        self.plot_4 = ExtendedPlotWidget(timing_source=timing_source_future, data_source=sinus_data_source, config=sliding_pointer_config)
        self.plot_5 = ExtendedPlotWidget(timing_source=timing_source_future, data_source=future_sin_source, config=sliding_pointer_config)
        self.plot_6 = ExtendedPlotWidget(timing_source=timing_source_future, data_source=past_sin_source, config=sliding_pointer_config)
        self.plot_7 = ExtendedPlotWidget(timing_source=timing_source_delayed, data_source=sinus_data_source, config=sliding_pointer_config)
        self.plot_8 = ExtendedPlotWidget(timing_source=timing_source_delayed, data_source=future_sin_source, config=sliding_pointer_config)
        self.plot_9 = ExtendedPlotWidget(timing_source=timing_source_delayed, data_source=past_sin_source, config=sliding_pointer_config)
        self.label_1 = QLabel("Timing: + 0s  , Data; + 0s")
        self.label_2 = QLabel("Timing: + 0s  , Data: + 1s")
        self.label_3 = QLabel("Timing: + 0s  , Data: - 1s")
        self.label_4 = QLabel("Timing: + 2s  , Data: + 0s")
        self.label_5 = QLabel("Timing: + 2s  , Data: + 1s")
        self.label_6 = QLabel("Timing: + 2s  , Data: - 1s")
        self.label_7 = QLabel("Timing: - 2s  , Data: + 0s")
        self.label_8 = QLabel("Timing: - 2s  , Data: + 1s")
        self.label_9 = QLabel("Timing: - 2s  , Data: - 1s")
        self.show()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.label_1, 0, 0)
        main_layout.addWidget(self.plot_1, 1, 0)
        main_layout.addWidget(self.label_2, 2, 0)
        main_layout.addWidget(self.plot_2, 3, 0)
        main_layout.addWidget(self.label_3, 4, 0)
        main_layout.addWidget(self.plot_3, 5, 0)
        main_layout.addWidget(self.label_4, 0, 1)
        main_layout.addWidget(self.plot_4, 1, 1)
        main_layout.addWidget(self.label_5, 2, 1)
        main_layout.addWidget(self.plot_5, 3, 1)
        main_layout.addWidget(self.label_6, 4, 1)
        main_layout.addWidget(self.plot_6, 5, 1)
        main_layout.addWidget(self.label_7, 0, 2)
        main_layout.addWidget(self.plot_7, 1, 2)
        main_layout.addWidget(self.label_8, 2, 2)
        main_layout.addWidget(self.plot_8, 3, 2)
        main_layout.addWidget(self.label_9, 4, 2)
        main_layout.addWidget(self.plot_9, 5, 2)


def run():
    """Run Application"""
    # pylint: disable=missing-docstring,unused-variable
    app = QApplication(sys.argv)
    gui = DelayDemoWindow()  # noqa: F841
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
