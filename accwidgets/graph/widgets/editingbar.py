from typing import Dict, Optional
import warnings
from abc import abstractmethod

from qtpy.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)
from qtpy.QtCore import QSize, Signal, Qt
import qtawesome as qta

from accwidgets.graph.datamodel.datastructures import CurveData, AbstractQObjectMeta
from accwidgets.graph.widgets.plotwidget import ExPlotWidget


class EditingButtonBar(QWidget):

    sig_enable_selection_mode = Signal(bool)
    """
    Signal that will be emitted to enable or disable the selection mode
    in an editable plot widget.
    """

    sig_send = Signal()
    """
    Signal that will be emitted to send the edited data back to the source
    it came from.
    """

    def __init__(self,
                 orientation: Qt.Orientation = Qt.Horizontal,
                 *args,
                 **kwargs):
        """
        Bar containing buttons for interacting with an editable plot widget.
        To connect a widget, use the connect function, which will set up all
        neccessary connections between the bar and the plot for you.

        Args:
            orientation: Should the contents be aligned in a vertical or
                         horizontal layout
            args: positional arguments for QWidget base class
            kwargs: keyword arguments for QWidget base class
        """
        super().__init__(*args, **kwargs)
        if orientation == Qt.Horizontal:
            self.setLayout(QHBoxLayout())
        elif orientation == Qt.Vertical:
            self.setLayout(QVBoxLayout())
        else:
            raise ValueError(f'Unknown orientation "{orientation}"')
        # Standard button definition
        self.edit_button: QPushButton = QPushButton()
        self.undo_button: QPushButton = QPushButton()
        self.redo_button: QPushButton = QPushButton()
        self.send_button: QPushButton = QPushButton()

        self._style_standard_buttons()
        self._add_standard_buttons()
        self._connect_standard_buttons()
        self._plot_selections: Dict[ExPlotWidget, Optional[CurveData]] = {}

    def connect(self, plot: ExPlotWidget) -> None:
        """
        Connect an editable plot widget to the bar. This includes the following
        functionality:

        - enable / disable selection mode for the plot
        - send state of the plot to the connected source
        - apply transformations on the selection in the currently edited plot

        Args:
            plot: The plot we want to control through the bar
        """
        self.sig_enable_selection_mode.connect(plot.set_selection_mode)
        self.sig_send.connect(plot.send_all_editables_state)
        self._plot_selections[plot] = None
        plot.sig_selection_changed.connect(self._handle_plot_selection_change)

    def disconnect(self, plot: ExPlotWidget) -> None:
        """
        Disconnect an editable plot widget to the bar. This includes the
        following functionality:

        - enable / disable selection mode for the plot
        - send state of the plot to the connected source
        - apply transformations on the selection in the currently edited plot

        Args:
            plot: The plot we do not want anymore to be controlled through the
                  bar
        """
        try:
            self.sig_enable_selection_mode.disconnect(plot.set_selection_mode)
        except TypeError:
            warnings.warn('"set_selection_mode" was not properly connected')
        try:
            self.sig_send.disconnect(plot.send_all_editables_state)
        except TypeError:
            warnings.warn('"send_all_editables" was not properly connected')
        try:
            del self._plot_selections[plot]
        except KeyError:
            warnings.warn("no current selection entry for plot")
        try:
            plot.sig_selection_changed.disconnect(self._handle_plot_selection_change)
        except TypeError:
            warnings.warn('"sig_selection_changed" was not properly connected to')

    def enable_selection_mode(self, enable: bool) -> None:
        """
        Enables the selection mode on all the connected plot widgets. This
        function is the equivalent of pressing the selection mode toggle
        button in the gui.

        Args:
            enable: If true, the selection mode will be enabled
        """
        self.edit_button.setChecked(enable)
        self.sig_enable_selection_mode.emit(enable)

    def send(self) -> None:
        """
        Send the current states for all the connected plot widgets back to
        the source they are connected to.
        """
        self.sig_send.emit()

    # ~~~~~~~~~~~~~~~~~~ Private Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _handle_plot_selection_change(self,
                                      curve: CurveData) -> None:
        """The selection in a plot has changed or moved.

        Args:
            curve: new slected data
        """
        plot = self.sender()
        if curve.x.size > 0 and curve.y.size > 0:
            self._plot_selections[plot] = curve
        else:
            self._plot_selections[plot] = None

    def _style_standard_buttons(self):
        """Apply styling to the standard buttons"""
        # Selection Toggle Button
        self.edit_button.setIcon(qta.icon("mdi.chart-line"))
        self.edit_button.setIconSize(QSize(24, 24))
        self.edit_button.setCheckable(True)
        self.edit_button.setChecked(False)
        # Undo Button
        self.undo_button.setIcon(qta.icon("mdi.arrow-left"))
        self.undo_button.setIconSize(QSize(24, 24))
        # Redo Button
        self.redo_button.setIcon(qta.icon("mdi.arrow-right"))
        self.redo_button.setIconSize(QSize(24, 24))
        # Send Button
        self.send_button.setIcon(qta.icon("mdi.send"))
        self.send_button.setIconSize(QSize(24, 24))

    def _add_standard_buttons(self):
        """Add all standard buttons to the bar's layout"""
        # TODO: activate and show as soon as rollback is available
        buttons = (self.edit_button,
                   # self.undo_button,
                   # self.redo_button,
                   self.send_button)
        for button in buttons:
            self.layout().addWidget(button)

    def _connect_standard_buttons(self):
        """Connect standard buttons' click signal to slots."""
        self.edit_button.toggled.connect(self.enable_selection_mode)
        self.send_button.clicked.connect(self.send)


class AbstractTransformationButton(QPushButton, metaclass=AbstractQObjectMeta):

    """
    Abstract Baseclass for creating a button that transforms values
    for the plot editing bar.
    """

    @abstractmethod
    def transformation(self, curve: CurveData) -> CurveData:
        """
        Transform an input curve to an output curve.

        Args:
            curve: Input values for the transformation function

        Returns:
            Output values calculated by the transformation function
        """
        pass
