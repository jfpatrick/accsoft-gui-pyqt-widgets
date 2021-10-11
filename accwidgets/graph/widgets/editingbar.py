"""
This module exposes toolbar that accommodates transformation functions and common controls
for the editable charts.
"""

import warnings
import numpy as np
import pyqtgraph as pg
import qtawesome as qta
from typing import Optional, List, Callable, cast, Union, Any, Tuple, Dict
from collections import defaultdict
from copy import deepcopy
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
from qtpy.QtWidgets import QSpinBox, QLabel, QGridLayout, QDialog, QDialogButtonBox, QToolBar, QAction, QWidget
from qtpy.QtCore import Signal, Slot
from accwidgets.graph import CurveData, ExPlotWidget


TransformationFunction = Callable[[CurveData], CurveData]
"""
Transformation function is used by editing charts to convert an input curve points into
another set of output points. The size of the input and output curves is not necessarily the same.
"""


class StandardTransformations:
    """Collection of standard transformation functions."""

    @staticmethod
    def aligned(curve: CurveData, value: Optional[int] = None) -> CurveData:
        """
        Align the passed curve to the given value. If the ``value`` is :obj:`None`,
        a dialog is shown to choose the value.

        Args:
            curve: Data which should be aligned.
            value: Value that each y-value of the curve should be set to.

        Returns:
            Aligned curve with y-value of each point being set to the passed ``value``.
        """
        curve = deepcopy(curve)
        if value is None:
            spin_box = pg.SpinBox()
            dialog = QDialog()
            dialog.setWindowTitle("Align selected values")
            dialog.setLayout(QGridLayout())
            button_bar = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            explanation = "Set selected points y value to:"
            dialog.layout().addWidget(QLabel(explanation), 1, 1, 1, 2)
            dialog.layout().addWidget(QLabel("New Value: "), 2, 1)
            dialog.layout().addWidget(spin_box, 2, 2)
            dialog.layout().addWidget(button_bar, 3, 1, 1, 2)

            def accept():
                nonlocal value
                value = spin_box.value()
                dialog.close()

            button_bar.accepted.connect(accept)
            button_bar.rejected.connect(dialog.close)
            dialog.exec_()
        if value is not None:
            curve.y[:] = value
        return curve

    @staticmethod
    def lin_fitted(curve: CurveData) -> CurveData:
        """
        Fit a line into the passed curve.

        Args:
            curve: Original points.

        Returns:
            Curve, whose y-values are positioned on the fitted line.
        """
        curve = deepcopy(curve)

        def func(x, m, c):
            return m * x + c

        popt, pcov = curve_fit(func, curve.x, curve.y)
        curve.y = func(curve.x, *popt)
        return curve

    @staticmethod
    def poly_fitted(curve: CurveData, degree: Optional[int] = None) -> CurveData:
        """
        Fit a polynomial of the given degree into the curve's points.

        Args:
            curve: Input curve that is used to fit the polynomial into.

        Return:
            Curve whose points are positioned on the fitted polynomial.
        """
        curve = deepcopy(curve)
        if degree is None:
            spinbox = pg.SpinBox()
            spinbox.setValue(1)
            spinbox.setOpts(
                bounds=(1, None),
                step=1,
            )
            dialog = QDialog()
            dialog.setWindowTitle("Fit Polynomial to Selection")
            dialog.setLayout(QGridLayout())
            button_bar = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            explanation = "Fit a Polynomial of the given degree to the " \
                          "given selection."
            dialog.layout().addWidget(QLabel(explanation), 1, 1, 1, 2)
            dialog.layout().addWidget(QLabel("Degree: "), 2, 1)
            dialog.layout().addWidget(spinbox, 2, 2)
            dialog.layout().addWidget(button_bar, 3, 1, 1, 2)

            def accept():
                nonlocal degree
                degree = spinbox.value()
                dialog.close()

            button_bar.accepted.connect(accept)
            button_bar.rejected.connect(dialog.close)
            dialog.exec_()
        if degree is not None:
            coefficients = np.polyfit(curve.x, curve.y, degree)
            curve.y = np.poly1d(coefficients)(curve.y)
        return curve

    @staticmethod
    def reduced_to_nth_point(curve: CurveData,
                             start_index: Optional[int] = None,
                             n: Optional[int] = None) -> CurveData:
        """
        Reduce curve to every n-th point.

        The results is equal to calling ``a[start_index::n]`` on a :class:`numpy.ndarray`.

        Args:
            curve: Input curve which should be reduced.
            start_index: Index from which the slicing should start.
            n: Every n-th point will be returned starting from the ``start_index``.

        Returns:
            Reduced curve.
        """
        curve = deepcopy(curve)
        if start_index is None and n is None:
            start_spinbox = QSpinBox()
            start_spinbox.setMinimum(0)
            start_spinbox.setMaximum(len(curve.x) - 1)
            n_spinbox = QSpinBox()
            n_spinbox.setValue(1)
            n_spinbox.setMinimum(1)
            n_spinbox.setMaximum(len(curve.x) - 1)
            dialog = QDialog()
            dialog.setLayout(QGridLayout())
            dialog.setWindowTitle("Reduce to every n-th point")
            button_bar = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            explanation = "Reduce the selection to every nth point \n" \
                          "starting from the given starting index."
            dialog.layout().addWidget(QLabel(explanation), 1, 1, 1, 2)
            dialog.layout().addWidget(QLabel("Start Index"), 2, 1)
            dialog.layout().addWidget(start_spinbox, 2, 2)
            dialog.layout().addWidget(QLabel("N"), 3, 1)
            dialog.layout().addWidget(n_spinbox, 3, 2)
            dialog.layout().addWidget(button_bar, 4, 1, 1, 2)

            def accept():
                nonlocal start_index, n
                start_index = start_spinbox.value()
                n = n_spinbox.value()
                dialog.close()

            button_bar.accepted.connect(accept)
            button_bar.rejected.connect(dialog.close)
            dialog.exec_()
        if start_index is not None and n is not None:
            curve.x = curve.x[start_index::n]
            curve.y = curve.y[start_index::n]
        return curve

    @staticmethod
    def cleared(curve: CurveData) -> CurveData:
        """
        Delete the selected points.

        Args:
            curve: Curve which should be deleted

        Returns:
            Empty curve.
        """
        _ = curve
        return CurveData([], [], check_validity=False)

    @staticmethod
    def moved(curve: CurveData, dy: Optional[float] = None) -> CurveData:
        """
        Move the curve in y-direction by the given delta.

        Args:
            curve: Curve whose y-values should be moved by ``dy``.
            dy: Offset for the y-values.

        Returns:
            Moved curve.
        """
        curve = deepcopy(curve)
        if dy is None:
            dy_spinbox = pg.SpinBox()
            dialog = QDialog()
            dialog.setWindowTitle("Move Points in Y direction")
            dialog.setLayout(QGridLayout())
            button_bar = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            explanation = "Move the curve in y-direction by the given delta."
            dialog.layout().addWidget(QLabel(explanation), 1, 1, 1, 2)
            dialog.layout().addWidget(QLabel("Delta Y"), 2, 1)
            dialog.layout().addWidget(dy_spinbox, 2, 2)
            dialog.layout().addWidget(button_bar, 3, 1, 1, 2)

            def accept():
                nonlocal dy
                dy = dy_spinbox.value()
                dialog.close()

            button_bar.accepted.connect(accept)
            button_bar.rejected.connect(dialog.close)
            dialog.exec_()
        if dy is not None:
            curve.y = np.add(curve.y, dy, casting="safe")
        return curve

    @staticmethod
    def smoothed(curve: CurveData,
                 window_length: Optional[int] = None,
                 poly_order: Optional[int] = None) -> CurveData:
        """
        Smoothen the curve by using the *Savitzky-Golay filter*.

        Args:
            curve: Curve which should be smoothened using the filter.
            window_length: Window length for the filter function.
            poly_order: Polynomial order for the filter function.

        Returns:
            Smoothened curve.
        """
        curve = deepcopy(curve)
        if poly_order is None or window_length is None:
            dialog = QDialog()
            dialog.setWindowTitle("Smooth selected curve")
            dialog.setLayout(QGridLayout())
            buttonBar = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            poly_order_spinbox = pg.SpinBox()
            window_length_spinbox = pg.SpinBox()
            window_length_upper_bound = len(curve.x) if len(curve.x) % 2 == 1 else len(curve.x) - 1

            window_length_spinbox.setMaximum(window_length_upper_bound)
            window_length_spinbox.setValue(1)
            window_length_spinbox.setOpts(int=True, step=2)
            window_length_spinbox.setMinimum(1)

            poly_order_spinbox.setValue(0)
            poly_order_spinbox.setOpts(int=True, step=1)
            poly_order_spinbox.setMaximum(window_length_upper_bound - 1)
            poly_order_spinbox.setMinimum(0)

            explanation = "Smooth the curve using the Savitzky-Golay-Filter.\n" \
                          "Window Length has to be an odd integer.\n" \
                          "Polynomial Order must be less than Window Length."

            dialog.layout().addWidget(QLabel(explanation), 1, 1, 1, 2)
            dialog.layout().addWidget(QLabel("Window Length"), 2, 1)
            dialog.layout().addWidget(QLabel("Polynomial Order"), 3, 1)
            dialog.layout().addWidget(window_length_spinbox, 2, 2)
            dialog.layout().addWidget(poly_order_spinbox, 3, 2)
            dialog.layout().addWidget(buttonBar, 4, 1, 1, 2)

            def accept():
                nonlocal poly_order, window_length
                poly_order = poly_order_spinbox.value()
                # window length has to be an odd integer
                spv = window_length_spinbox.value()
                window_length = spv if spv % 2 == 1 else spv + 1
                dialog.close()

            buttonBar.accepted.connect(accept)
            buttonBar.rejected.connect(dialog.close)
            dialog.exec_()
        if window_length is not None and poly_order is not None:
            curve.y = savgol_filter(curve.y,
                                    window_length=window_length,
                                    polyorder=poly_order)
        return curve


class EditingToolBar(QToolBar):

    sig_enable_selection_mode = Signal(bool)
    """Emits the command to toggle the selection mode in an :class:`EditablePlotWidget`."""

    standard_functions: List[Tuple[Tuple[str, str], Callable[[CurveData], CurveData], int]] = [
        (("mdi.ray-start-end", "Align"), StandardTransformations.aligned, 1),
        (("mdi.arrow-up-down", "Move"), StandardTransformations.moved, 1),
        (("mdi.vector-line", "Linear Fit"), StandardTransformations.lin_fitted, 3),
        (("mdi.vector-polyline", "Polynomial Fit"), StandardTransformations.poly_fitted, 3),
        (("mdi.filter", "Smooth Curve"), StandardTransformations.smoothed, 3),
        (("mdi.box-cutter", "Reduce Points"), StandardTransformations.reduced_to_nth_point, 1),
        (("mdi.trash-can", "Delete"), StandardTransformations.cleared, 1),
    ]
    """Mapping of the default transformation functions added to the editing toolbar and their button appearance."""

    def __init__(self,
                 title: Optional[str] = None,
                 parent: Optional[QWidget] = None):
        """
        Toolbar for interaction with :class:`EditablePlotWidget`.
        To connect a widget, use the :meth:`connect` method, which will set up all
        necessary signals-slot attachments with the plot widget.

        Args:
            title: The given window ``title`` identifies the toolbar and is shown
                   in the context menu provided by :class:`QMainWindow`.
            parent: Parent widget of the toolbar.
        """
        super().__init__(title, parent)
        # Standard button definition
        self.edit_action: QAction = QAction(qta.icon("mdi.select-drag"), "Editing Mode")
        self.undo_action: QAction = QAction(qta.icon("mdi.undo"), "Undo")
        self.redo_action: QAction = QAction(qta.icon("mdi.redo"), "Redo")
        self.send_action: QAction = QAction(qta.icon("mdi.send"), "Send")
        # Edit action is a toggle
        self.edit_action.setCheckable(True)
        self.edit_action.setChecked(False)
        # Fields for selection
        self._transformation_actions: List[QAction] = []
        self._transformation_actions_min_selection: Dict[QAction, int] = defaultdict(lambda: 1)
        self._connected_plots: List[ExPlotWidget] = []
        self._selected_plot: Optional[ExPlotWidget] = None
        # Setting up actions
        self._setup_actions()

    def connect(self, plot: Union[ExPlotWidget, List[ExPlotWidget]]):
        """
        Connect an editable plot widget to the bar. This includes the following
        functionality:

        * Toggling selection mode of the plot widget
        * Committing changes made on the plot to the connected :class:`UpdateSource`
        * Apply transformations on the selection in the currently edited plot

        Args:
            plot: The plot widget or widgets that should be controlled via the bar actions.
        """
        if not isinstance(plot, list):
            plot = [plot]
        for p in plot:
            self._connect(p)

    def disconnect(self, plot: Union[ExPlotWidget, List[ExPlotWidget]]):
        """
        Disconnect an editable plot widget to the bar.

        This method does the opposite of :meth:`connect`.

        Args:
            plot: The plot widget or widgets that should be no longer controlled via the bar actions.
        """
        if not isinstance(plot, list):
            plot = [plot]
        for p in plot:
            self._disconnect(p)

    def add_transformation(self,
                           action: QAction,
                           transformation: TransformationFunction,
                           min_points_needed: int = 1):
        """
        Add a transformation function that should be triggered by the related action when
        triggered from the toolbar.

        This method takes care of wiring up connections between the action and the
        transformation function. The transformation function will always receive a **copy**
        of the selected data. The input to the transformation function is selected
        part of the data (at the time of execution) from currently selected plot widget
        (if more than one is connected to the toolbar).

        Args:
            action: Action to add to the toolbar.
            transformation: Transformation function which should be called when the
                            action is triggered.
            min_points_needed: The minimum amount of points needed for the
                               transformation. If less are selected, the action
                               will be disabled.
        """
        self._transformation_actions.append(action)
        self._transformation_actions_min_selection[action] = min_points_needed
        action.triggered.connect(lambda *_: self.transform(transformation))
        self.addAction(action)
        self._update_buttons_enable_state()

    def remove_transformation(self, action: QAction):
        """
        Remove an action and the attached transformation from the toolbar that was
        previously added via :meth:`add_transformation`.

        Args:
            action: Action to remove from the toolbar.
        """
        self._transformation_actions.remove(action)
        self.removeAction(action)

    def transform(self, transformation: TransformationFunction):
        """
        Transform the current selection with the given ``transformation``
        function. The result of the transformation will overwrite
        the current selection in the currently selected plot.

        The transformation function will always receive a **copy**
        of the selected data.

        Args:
            transformation: Function which should be applied to the current
                            selection.
        """
        curve = self.current_plots_selection
        if curve:
            try:
                result = transformation(deepcopy(curve))
                cast(ExPlotWidget, self.selected_plot).replace_selection(result)
            except BaseException as e:  # noqa: B902
                # In case an added transformation fails
                warnings.warn(f"Transformation failed because a "
                              f"{type(e).__name__} was risen:\n{str(e)}")

    def enable_selection_mode(self, enable: bool):
        """
        Toggles the selection mode on all the connected plot widgets. This
        method is the equivalent to pressing the selection mode toggle
        button in the toolbar GUI.

        Args:
            enable: If :obj:`True`, the selection mode will be enabled.
        """
        self.edit_action.setChecked(enable)
        self.sig_enable_selection_mode.emit(enable)

    def send(self, *_):
        """
        Commit the current changes for all the connected plot widgets back to
        the :class:`UpdateSource` that they are connected to.
        """
        if self.selected_plot:
            self.selected_plot.send_all_editables_state()
        self._update_buttons_enable_state()

    def undo(self, *_: Any):
        """Undo the last change for the currently selected plot."""
        if self.selected_plot and self.selected_plot.plotItem.current_editable:
            self.selected_plot.plotItem.current_editable.undo()

    def redo(self, *_: Any):
        """Redo the next change for the currently selected plot."""
        if self.selected_plot and self.selected_plot.plotItem.current_editable:
            self.selected_plot.plotItem.current_editable.redo()

    @property
    def selected_plot(self) -> Optional[ExPlotWidget]:
        """
        Currently selected plot. If only one plot is connected, it will always be returned.
        When no plot is connected, :obj:`None` is returned.
        """
        if len(self._connected_plots) == 1:
            return self._connected_plots[0]
        return self._selected_plot

    @property
    def current_plots_selection(self) -> Optional[CurveData]:
        """
        Data selection of the currently selected plot. If no data is selected
        or the :attr:`selected_plot` is :obj:`None`, :obj:`None` is returned.
        """
        if self.selected_plot:
            data = self.selected_plot.current_selection_data
            if data and len(data.x) > 0 and len(data.y) > 0:
                return CurveData(x=np.array(data.x),
                                 y=np.array(data.y),
                                 check_validity=False)
            return None
        return None

    @property
    def connected_plots(self) -> List[ExPlotWidget]:
        """List of plots that are connected to the bar."""
        return self._connected_plots

    # ~~~~~~~~~~~~~~~~~~~~~~~~~ Slots ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @Slot(bool)
    def handle_plot_selection_changed(self, selected: bool):
        """
        Handle the plot selection change. If one plot gets selected, all other
        plots are deselected. If the currently selected plot is unselected,
        it will be selected again to make sure that one plot of the managed
        plots is always selected.

        The sender of the signal is expected to be the plot, where the selection
        was toggled.

        Args:
            selected: Marks whether the sender plot is currently selected.
        """
        plot: ExPlotWidget = self.sender()
        if selected:
            self._selected_plot = plot
            for p in self.connected_plots:
                if p != plot and p.plotItem._plot_selected:
                    p.plotItem.toggle_plot_selection(False)
        # Make sure there is always a selected plot
        elif plot == self._selected_plot and not selected:
            self._selected_plot.plotItem.toggle_plot_selection(True)
        self._update_buttons_enable_state()

    # ~~~~~~~~~~~~~~~~~ Private Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _connect(self, plot: ExPlotWidget):
        """Connect a single plot"""
        self.sig_enable_selection_mode.connect(plot.set_selection_mode)
        plot.sig_plot_selected.connect(self.handle_plot_selection_changed)
        plot.sig_selection_changed.connect(lambda *_: self._update_buttons_enable_state())
        self._connected_plots.append(plot)
        self._update_plots_selectable()
        # If we do not have a plot selection, we want to have one selected in
        # the beginning
        if self._selected_plot is None:
            self.connected_plots[0].toggle_plot_selection(True)
        self._update_buttons_enable_state()

    def _disconnect(self, plot: ExPlotWidget):
        """Disconnect a single plot"""
        try:
            self.sig_enable_selection_mode.disconnect(plot.set_selection_mode)
        except TypeError:
            warnings.warn("The plot seems to be not properly connected: "
                          '"set_selection_mode" was not properly connected')
        self._update_plots_selectable()

    def _update_plots_selectable(self):
        """
        Activate the plot selection if more than two plots are connected.
        If only one plot is connected, the plot will be made non selectable.
        """
        activated = len(self._connected_plots) > 1
        for plot in self._connected_plots:
            plot.plotItem.make_selectable(activated)

    def _update_buttons_enable_state(self):
        """Update, if buttons are enabled/disabled."""
        self._update_function_actions()
        self._update_send_button()
        self._update_undo_button()
        self._update_redo_button()

    def _update_function_actions(self):
        """Update actions being enabled / disabled by the current selection."""
        selection = self.current_plots_selection
        for action in self._transformation_actions:
            minimum = self._transformation_actions_min_selection[action]
            action.setEnabled(selection is not None and len(selection.x) >= minimum)

    def _update_send_button(self):
        """Update if the send button is enabled or not."""
        enable = (
            self.selected_plot is not None
            and self.selected_plot.plotItem.current_editable is not None
            and self.selected_plot.plotItem.current_editable.sendable_state_exists
        )
        self.send_action.setEnabled(enable)

    def _update_undo_button(self):
        """Update if the send button is enabled or not."""
        enable = (
            self.selected_plot is not None
            and self.selected_plot.plotItem.current_editable is not None
            and self.selected_plot.plotItem.current_editable.undoable
        )
        self.undo_action.setEnabled(enable)

    def _update_redo_button(self):
        """Update if the send button is enabled or not."""
        enable = (
            self.selected_plot is not None
            and self.selected_plot.plotItem.current_editable is not None
            and self.selected_plot.plotItem.current_editable.redoable
        )
        self.redo_action.setEnabled(enable)

    def _setup_actions(self):
        """Setup Actions for the Editing-Bar including the standard functions"""
        self._add_standard_actions()
        self._connect_standard_actions()
        self.addSeparator()
        for action, transformation, minimum in EditingToolBar.standard_functions:
            action = QAction(qta.icon(action[0]), action[1])
            self.add_transformation(action,
                                    cast(TransformationFunction, transformation),
                                    minimum)

    def _add_standard_actions(self):
        """Add all standard buttons to the bar's layout"""
        actions = (self.edit_action,
                   self.undo_action,
                   self.redo_action,
                   self.send_action)
        for action in actions:
            self.addAction(action)

    def _connect_standard_actions(self):
        """Connect standard buttons' click signal to slots."""
        self.edit_action.toggled.connect(self.enable_selection_mode)
        self.undo_action.triggered.connect(self.undo)
        self.redo_action.triggered.connect(self.redo)
        self.send_action.triggered.connect(self.send)
