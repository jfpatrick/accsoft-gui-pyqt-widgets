"""
Window with Extended PlotWidget for Testing purposes
"""

from typing import Optional, Type, Union, Dict

from qtpy.QtWidgets import QGridLayout, QMainWindow, QWidget

from accwidgets.graph import (
    AbstractBasePlotCurve,
    AbstractBaseBarGraphItem,
    AbstractBaseInjectionBarGraphItem,
    AbstractBaseTimestampMarker,
    ExPlotWidget,
    ExPlotWidgetConfig,
    DataModelBasedItem,
)

from .mock_data_source import MockDataSource
from .mock_timing_source import MockTimingSource


class PlotWidgetTestWindow(QMainWindow):
    """Test window with data and timing source"""

    def __init__(
        self,
        plot_config: ExPlotWidgetConfig,
        item_to_add: Union[Type[DataModelBasedItem], str, None] = None,
        opts: Optional[Dict] = None,
        should_create_timing_source: bool = True,
    ):
        """Constructor :param plot_config: Configuration for the Plot Widget

        Args:
            plot_config (ExtendedPlotWidgetConfig):
            curve_configs:
        """
        super().__init__()
        if opts is None:
            opts = {}
        # Two Threads for Time and Data updates
        self.time_source_mock: Optional[MockTimingSource]
        if should_create_timing_source:
            self.time_source_mock = MockTimingSource()
        else:
            self.time_source_mock = None
        self.data_source_mock: MockDataSource = MockDataSource()
        self.plot_config: ExPlotWidgetConfig = plot_config
        self.plot: ExPlotWidget = ExPlotWidget(
            timing_source=self.time_source_mock, config=plot_config,
        )
        self.item_to_add: Union[Type[DataModelBasedItem], str, None] = item_to_add
        self.opts: dict = opts
        self.add_item()
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)

    def add_item(self):
        """Add requested item to the """
        try:
            if self.item_to_add is not None:
                if issubclass(self.item_to_add, AbstractBasePlotCurve):
                    self.plot.addCurve(data_source=self.data_source_mock, **self.opts)
                elif issubclass(self.item_to_add, AbstractBaseBarGraphItem):
                    self.plot.addBarGraph(data_source=self.data_source_mock, **self.opts)
                elif issubclass(self.item_to_add, AbstractBaseInjectionBarGraphItem):
                    self.plot.addInjectionBar(data_source=self.data_source_mock, **self.opts)
                elif issubclass(self.item_to_add, AbstractBaseTimestampMarker):
                    self.plot.addTimestampMarker(data_source=self.data_source_mock)
        except ValueError:
            # ValueError -> Configuration does not support the required
            #               Test has to check if this is wanted, but here
            #               it is allowed to fail
            pass


class MinimalTestWindow(QMainWindow):
    """Helper class for creating a Window containing an ExtendedPlotWidget with
    timing and data sources that allow convenient testing by giving the option
    to manually triggering updates with given values.
    """

    def __init__(
        self,
        plot_config: Optional[ExPlotWidgetConfig] = None,
        plot_widget: Optional[ExPlotWidget] = None,
    ):
        """Constructor :param plot_config: Configuration for the Plot Widget

        Args:
            plot_config (ExtendedPlotWidgetConfig): Configuration for the created plot widget
        """
        super().__init__()
        self.plot_config: ExPlotWidgetConfig
        self.plot: ExPlotWidget
        if plot_widget:
            self.plot = plot_widget
            self.plot_config = plot_widget.plotItem.plot_config
        else:
            self.plot_config = plot_config or ExPlotWidgetConfig()
            self.plot = ExPlotWidget(config=plot_config)
        self.resize(800, 600)
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QGridLayout()
        main_container.setLayout(main_layout)
        main_layout.addWidget(self.plot)
