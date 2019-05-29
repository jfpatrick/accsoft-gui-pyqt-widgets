"""Update Source for Data for Testing purposes"""

from accsoft_gui_pyqt_widgets.graph import UpdateSource


class ManualDataSource(UpdateSource):
    """Data Source for Testing purposes

    Class for sending the right signals to the ExtendedPlotWidget. This
    allows precise control over updates that are sent to the widget compared to
    timer based solutions.
    """

    def create_new_value(self, timestamp: float, value: float) -> None:
        """Manually emit a signal with a given new value.

        Args:
            timestamp (float): timestamp to emit
            value (float): value to emit
        """
        new_data = {
            "x": timestamp,
            "y": value,
        }
        self.data_signal.emit(new_data)
