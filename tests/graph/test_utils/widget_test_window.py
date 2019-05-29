"""
Window with Extended PlotWidget for Testing purposes
"""

from qtpy.QtWidgets import QMainWindow, QWidget, QGridLayout
from accsoft_gui_pyqt_widgets.graph import ExtendedPlotWidget, ExtendedPlotWidgetConfig
from .manual_data_source import ManualDataSource
from .manual_timing_source import ManualTimingSource


class ExtendedPlotWidgetTestingWindow(QMainWindow):
    """Helper class for creating a Window containing an ExtendedPlotWidget with
    timing and data sources that allow convenient testing by giving the option
    to manually triggering updates with given values.
    """

    def __init__(self, plot_config: ExtendedPlotWidgetConfig):
        """Constructor :param plot_config: Configuration for the Plot Widget

        Args:
            plot_config (ExtendedPlotWidgetConfig):
        """
        super().__init__()
        # Two Threads for Time and Data updates
        self.time_source_mock = ManualTimingSource()
        self.data_source_mock = ManualDataSource()
        self.plot: ExtendedPlotWidget = ExtendedPlotWidget(
            timing_source=self.time_source_mock, data_source=self.data_source_mock, config=plot_config)
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
