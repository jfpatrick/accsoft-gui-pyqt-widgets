"""Update Source for timestamps for Testing purposes"""

from accsoft_gui_pyqt_widgets.graph import UpdateSource


class MockTimingSource(UpdateSource):
    """Timing Source for Testing Purposes

    Class for sending the right signals to the ExtendedPlotWidget. This
    allows precise control over updates that are sent to the widget compared to
    timer based solutions.
    """

    def create_new_value(self, timestamp: float) -> None:
        """Manually emit timestamp

        Args:
            timestamp (float): timestamp to emit
        """
        self.sig_timing_update.emit(timestamp)
