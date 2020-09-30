
import pytest
import numpy as np
import qtawesome as qta
from typing import List
from unittest.mock import patch
from scipy.signal import savgol_filter
from qtpy import QtWidgets, QtCore
from PyQt5 import QtTest  # qtpy.QTest incomplete: https://github.com/spyder-ide/qtpy/issues/197
from accwidgets.graph import (EditingToolBar, EditablePlotWidget, EditablePlotCurve, CurveData, UpdateSource,
                              ExPlotWidget, StandardTransformations)
from .mock_utils.utils import sim_selection_moved


def test_bar_toggle_editable_mode(qtbot, empty_testing_window):
    """
    Test if the right signals are emitted on an edit button press
    """
    qtbot.add_widget(empty_testing_window)
    bar = EditingToolBar()
    empty_testing_window.cw_layout.addWidget(bar)

    spy = QtTest.QSignalSpy(bar.sig_enable_selection_mode)
    assert len(spy) == 0
    # Multiple button presses for buttons which can be toggled
    bar.edit_action.trigger()
    assert len(spy) == 1
    bar.edit_action.trigger()
    assert len(spy) == 2


@pytest.mark.parametrize(
    "selected_plot, curve_1_selection, curve_2_selection, curve_1_edit, curve_2_edit",
    [
        # Plot 0 selected, nothing selected & edited
        (0, None, None, None, None),
        # Plot 0 selected & data selected, nothing edited
        (0, QtCore.QRectF(0, 1.5, 2, 1), None, None, None),
        # Plot 1 selected, nothing selected & edited
        (1, None, None, None, None),
        # Plot 1 selected & data selected, nothing edited
        (0, None, QtCore.QRectF(0, 1.5, 2, 1), None, None),
        # Plot 0 selected and edited
        (0, QtCore.QRectF(0, 1.5, 2, 1), None, ((0.0, 3.0), (1.0, 4.0)), None),
        # Plot 1 selected and edited
        (1, None, QtCore.QRectF(0, 1.5, 2, 1), None, ((0.0, 3.0), (1.0, 4.0))),
        # Plot 0 selected and both edited
        (0, QtCore.QRectF(0, 1.5, 2, 1), QtCore.QRectF(0, 1.5, 2, 1), ((0.0, 3.0), (1.0, 4.0)), ((0.0, 3.0), (1.0, 4.0))),
        # Plot 1 selected and both edited
        (0, QtCore.QRectF(0, 1.5, 2, 1), QtCore.QRectF(0, 1.5, 2, 1), ((0.0, 3.0), (1.0, 4.0)), ((0.0, 3.0), (1.0, 4.0))),
        # Plot 1 selected and Plot 0 edited
        (1, QtCore.QRectF(0, 1.5, 2, 1), None, ((0.0, 3.0), (1.0, 4.0)), None),
        # Plot 0 selected and Plot 1 edited
        (0, None, QtCore.QRectF(0, 1.5, 2, 1), None, ((0.0, 3.0), (1.0, 4.0))),
    ],
)
def test_bar_send(qtbot,
                  empty_testing_window,
                  selected_plot,
                  curve_1_selection,
                  curve_2_selection,
                  curve_1_edit,
                  curve_2_edit):
    """Test if send button is enabled /disabled properly"""
    qtbot.add_widget(empty_testing_window)
    plot_1 = EditablePlotWidget()
    plot_2 = EditablePlotWidget()
    plots = [plot_1, plot_2]
    bar = EditingToolBar()
    bar.connect(plots)
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot_1)
    empty_testing_window.cw_layout.addWidget(plot_2)

    source_1 = UpdateSource()
    source_2 = UpdateSource()
    with patch.object(source_1, "handle_data_model_edit") as handler_1:
        with patch.object(source_2, "handle_data_model_edit") as handler_2:
            curve_1: EditablePlotCurve = plot_1.addCurve(data_source=source_1)
            curve_2: EditablePlotCurve = plot_2.addCurve(data_source=source_2)
            source_1.send_data(CurveData([0, 1, 2], [0, 1, 2]))
            source_2.send_data(CurveData([0, 1, 2], [2, 1, 0]))

            plots[selected_plot].plotItem.toggle_plot_selection(True)
            assert bar.selected_plot == plots[selected_plot]

            if curve_1_selection:
                curve_1.select(curve_1_selection)
            if curve_2_selection:
                curve_2.select(curve_2_selection)

            # The send button should be enabled as soon as we have a curve
            assert bar.send_action.isEnabled()

            if curve_1_edit:
                sim_selection_moved(curve_1._selection, *curve_1_edit)
            if curve_2_edit:
                sim_selection_moved(curve_2._selection, *curve_2_edit)

            assert bar.send_action.isEnabled()
            bar.widgetForAction(bar.send_action).click()
            assert bar.send_action.isEnabled()

            if selected_plot == 0:
                handler_1.assert_called_once()
            else:
                handler_1.assert_not_called()
            if selected_plot == 1:
                handler_2.assert_called_once()
            else:
                handler_2.assert_not_called()


def test_send_action_plot_switch(qtbot,
                                 empty_testing_window):
    """Send Button disabled when switching to plot without changes and enabled
    again when switching back"""
    qtbot.add_widget(empty_testing_window)
    plot_1 = EditablePlotWidget()
    plot_2 = EditablePlotWidget()
    plots = [plot_1, plot_2]
    bar = EditingToolBar()
    bar.connect(plots)
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot_1)
    empty_testing_window.cw_layout.addWidget(plot_2)

    source_1 = UpdateSource()
    source_2 = UpdateSource()
    curve_1: EditablePlotCurve = plot_1.addCurve(data_source=source_1)
    _: EditablePlotCurve = plot_2.addCurve(data_source=source_2)
    source_1.send_data(CurveData([0, 1, 2], [0, 1, 2]))
    source_2.send_data(CurveData([0, 1, 2], [2, 1, 0]))

    plots[0].plotItem.toggle_plot_selection(True)
    curve_1.select(QtCore.QRectF(0, 1.5, 2, 1))
    assert bar.send_action.isEnabled()
    sim_selection_moved(curve_1._selection, (0.0, 3.0), (1.0, 4.0))
    assert bar.send_action.isEnabled()
    plots[1].plotItem.toggle_plot_selection(True)
    assert bar.send_action.isEnabled()
    plots[0].plotItem.toggle_plot_selection(True)
    assert bar.send_action.isEnabled()


def test_send_enabled_after_data_unselect(qtbot,
                                          empty_testing_window):
    """Send button should still be enabled even when deselected the edited data"""
    qtbot.add_widget(empty_testing_window)
    plot_1 = EditablePlotWidget()
    bar = EditingToolBar()
    bar.connect(plot_1)
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot_1)

    source_1 = UpdateSource()
    curve_1: EditablePlotCurve = plot_1.addCurve(data_source=source_1)
    source_1.send_data(CurveData([0, 1, 2], [0, 1, 2]))

    plot_1.plotItem.toggle_plot_selection(True)
    curve_1.select(QtCore.QRectF(0, 1.5, 2, 1))
    assert bar.send_action.isEnabled()
    sim_selection_moved(curve_1._selection, (0.0, 3.0), (1.0, 4.0))
    assert bar.send_action.isEnabled()
    curve_1.select(QtCore.QRectF(-100, -100, 1, 1))
    assert bar.send_action.isEnabled()


@pytest.mark.parametrize("selected_plots, data_selections, enabled", [
    ([False, False], [None, QtCore.QRectF(0, 0, 2, 2)], False),
    ([True, False], [None, QtCore.QRectF(0, 0, 2, 2)], False),
    ([False, True], [QtCore.QRectF(0, 0, 2, 2), None], False),
    ([True, True], [None, None], False),
    ([True, False], [QtCore.QRectF(0, 0, 2, 2), None], True),
    ([True, False], [QtCore.QRectF(0, 0, 2, 2), QtCore.QRectF(0, 0, 2, 2)], True),
    ([False, True], [None, QtCore.QRectF(0, 0, 2, 2)], True),
    ([False, True], [QtCore.QRectF(0, 0, 2, 1), QtCore.QRectF(0, 0, 2, 2)], True),
    ([True, True], [QtCore.QRectF(0, 0, 2, 2), QtCore.QRectF(0, 0, 2, 2)], True),
])
def test_function_buttons_enabled(qtbot,
                                  empty_testing_window,
                                  selected_plots,
                                  data_selections,
                                  enabled):
    qtbot.add_widget(empty_testing_window)
    plot_1 = EditablePlotWidget()
    plot_2 = EditablePlotWidget()
    bar = EditingToolBar()
    bar.connect([plot_1, plot_2])
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot_1)
    empty_testing_window.cw_layout.addWidget(plot_2)

    source_1 = UpdateSource()
    source_2 = UpdateSource()
    curve_1: EditablePlotCurve = plot_1.addCurve(data_source=source_1)
    curve_2: EditablePlotCurve = plot_2.addCurve(data_source=source_2)
    source_1.send_data(CurveData([0, 1, 2], [0, 1, 2]))
    source_2.send_data(CurveData([0, 1, 2], [2, 1, 0]))

    for plot, sp in zip([plot_1, plot_2], selected_plots):
        plot.plotItem.toggle_plot_selection(sp)
    for curve, ds in zip([curve_1, curve_2], data_selections):
        if ds is not None:
            curve.select(ds)
        else:
            curve.unselect()

    # First plot selected , no data selected
    for a in bar._transformation_actions:
        assert bar.widgetForAction(a).isEnabled() == enabled


@pytest.mark.parametrize("selection, disabled_count", [
    (QtCore.QRectF(0, 0, 2, 2), 0),
    (QtCore.QRectF(0, 0, 2, 1), 3),
])
def test_function_buttons_with_multiple_point_min_selection(
    qtbot,
    empty_testing_window,
    selection,
    disabled_count,
):
    qtbot.add_widget(empty_testing_window)
    plot_1 = EditablePlotWidget()
    bar = EditingToolBar()
    bar.connect(plot_1)
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot_1)
    source = UpdateSource()
    curve: EditablePlotCurve = plot_1.addCurve(data_source=source)
    source.send_data(CurveData([0, 1, 2], [0, 1, 2]))
    # Only two points will be selected
    curve.select(selection)

    # First plot selected , no data selected
    actually_disabled = 0
    for a in bar._transformation_actions:
        minimum = bar._transformation_actions_min_selection[a]
        sel_points = len(curve.selection_data.x)
        assert bar.widgetForAction(a).isEnabled() == (sel_points >= minimum)
        if not bar.widgetForAction(a).isEnabled():
            actually_disabled += 1
    assert actually_disabled == disabled_count


@pytest.mark.parametrize("plot_count", [1, 2])
def test_plot_connection(qtbot,
                         empty_testing_window,
                         plot_count):
    """
    Check if the editable toggle button press is properly forwarded
    to the connected plots.
    """
    with patch.object(ExPlotWidget, "set_selection_mode") as selection_mock:
        qtbot.add_widget(empty_testing_window)
        bar = EditingToolBar()
        plots: List[ExPlotWidget] = []
        for _ in range(plot_count):
            plot = EditablePlotWidget()
            plots.append(plot)
            empty_testing_window.cw_layout.addWidget(plot)
        bar.connect(plots)
        empty_testing_window.addToolBar(bar)

        # Enable point selection
        bar.widgetForAction(bar.edit_action).click()
        assert len(selection_mock.mock_calls) == len(plots)
        plot.set_selection_mode.assert_called_with(True)

        selection_mock.reset_mock()

        # Disable point selection
        bar.widgetForAction(bar.edit_action).click()
        assert len(plot.set_selection_mode.mock_calls) == len(plots)
        plot.set_selection_mode.assert_called_with(False)


def test_disconnect(qtbot, empty_testing_window):
    """
    Check if disconnecting a single plot is possible without any side effects
    """
    with patch.object(ExPlotWidget, "set_selection_mode") as selection_mock:
        plots = [EditablePlotWidget(),
                 EditablePlotWidget()]
        qtbot.add_widget(empty_testing_window)
        bar = EditingToolBar()
        empty_testing_window.addToolBar(bar)
        empty_testing_window.cw_layout.addWidget(plots[0])
        empty_testing_window.cw_layout.addWidget(plots[1])

        bar.connect(plots)
        selection_mock.reset_mock()

        # Enable point selection
        bar.widgetForAction(bar.edit_action).click()
        assert len(plots[0].set_selection_mode.mock_calls) == 2
        bar.disconnect(plots[0])

        bar.widgetForAction(bar.edit_action).click()
        assert len(plots[0].set_selection_mode.mock_calls) == 3


@pytest.mark.parametrize("pl1_sel, pl2_sel, selected", [
    (None, None, 0),
    (True, None, 0),
    (True, False, 0),
    (None, False, 0),
    (False, None, 0),  # Can't be deselected
    (False, False, 0),  # Can't be deselected
    (None, True, 1),
    (False, True, 1),
    (True, True, 1),
])
def test_plot_item_selection(qtbot,
                             empty_testing_window,
                             pl1_sel,
                             pl2_sel,
                             selected):
    qtbot.add_widget(empty_testing_window)
    plot_1 = EditablePlotWidget()
    plot_2 = EditablePlotWidget()
    plots = [plot_1, plot_2]
    bar = EditingToolBar()
    bar.connect(plots)
    for w in plots + [bar]:
        empty_testing_window.cw_layout.addWidget(w)

    if pl1_sel is not None:
        plot_1.plotItem.toggle_plot_selection(pl1_sel)
    if pl2_sel is not None:
        plot_2.plotItem.toggle_plot_selection(pl2_sel)

    if isinstance(selected, int):
        assert bar.selected_plot == plots[selected]
    else:
        assert bar.selected_plot is None


@pytest.mark.parametrize("selections, selected", [
    # Try deselecting the selected plot
    ([0], 0),
    ([0, 0], 0),
    # Select other plot
    ([1], 1),
    ([0, 1], 1),
    # Select other plot and try to unselect it
    ([0, 1, 1], 1),
    ([0, 1, 1, 1], 1),
    # Select previous plot again
    ([0, 1, 0], 0),
    ([0, 1, 1, 0], 0),
    # Unselect plot that was deselected before
    ([0, 1, 0, 0], 0),
])
def test_change_plot_item_selection_sequence(qtbot,
                                             empty_testing_window,
                                             selections,
                                             selected):
    qtbot.add_widget(empty_testing_window)
    pl1 = EditablePlotWidget()
    pl2 = EditablePlotWidget()
    plots = [pl1, pl2]
    bar = EditingToolBar()
    empty_testing_window.cw_layout.addWidget(pl1)
    empty_testing_window.cw_layout.addWidget(pl2)
    empty_testing_window.addToolBar(bar)
    bar.connect(plots)
    for selection in selections:
        plots[selection].plotItem.toggle_plot_selection(True)
    for index, plot in enumerate(plots):
        assert plot.plotItem._plot_selectable
        assert plot.plotItem._plot_selected == (index == selected)


def test_single_connected_plot_not_selectable(qtbot, empty_testing_window):
    """Plot selecting should be disabled if only a single plot is connected."""
    qtbot.add_widget(empty_testing_window)
    pl1 = EditablePlotWidget()
    bar = EditingToolBar()
    bar.connect(pl1)
    empty_testing_window.cw_layout.addWidget(pl1)
    empty_testing_window.addToolBar(bar)
    assert not pl1.plotItem._plot_selectable
    assert not pl1.plotItem._plot_selected
    assert bar.selected_plot == pl1
    pl1.plotItem.toggle_plot_selection(True)
    assert not pl1.plotItem._plot_selectable
    assert not pl1.plotItem._plot_selected
    assert bar.selected_plot == pl1


def test_disconnect_selected_plot(qtbot, empty_testing_window):
    """Disconnect a selected plot"""
    qtbot.add_widget(empty_testing_window)
    plots = []
    for _ in range(3):
        plots.append(EditablePlotWidget())
    bar = EditingToolBar()
    bar.connect(plots)
    empty_testing_window.addToolBar(bar)
    for plot in plots:
        empty_testing_window.cw_layout.addWidget(plot)
    plots[2].plotItem.toggle_plot_selection(True)
    for i, plot in enumerate(plots):
        assert plot.plotItem._plot_selected == (i == 2)
    bar.disconnect(plots[2])
    selected_plots = 0
    for plot in plots:
        selected_plots += 1 if plot.plotItem._plot_selected else 0
    assert selected_plots == 1
    assert bar.selected_plot in plots


@pytest.mark.parametrize("pl1_sel, pl2_sel, active_plot, selection", [
    (QtCore.QRectF(0, 2.5, 4, 1), QtCore.QRectF(0, 2.5, 4, 1), 0, CurveData([0, 4], [3, 3])),
    (None, QtCore.QRectF(0, 2.5, 4, 1), 1, CurveData([2], [3])),
    (QtCore.QRectF(0, 2.5, 4, 1), QtCore.QRectF(0, 2.5, 4, 1), 1, CurveData([2], [3])),
])
def test_selection_of_current_plotitem(qtbot,
                                       empty_testing_window,
                                       pl1_sel,
                                       pl2_sel,
                                       active_plot,
                                       selection):
    qtbot.add_widget(empty_testing_window)
    pl1 = EditablePlotWidget()
    pl2 = EditablePlotWidget()
    bar = EditingToolBar()
    plots = [pl1, pl2]

    for w in [pl1, pl2, bar]:
        empty_testing_window.cw_layout.addWidget(w)
    bar.connect(plots)

    s1: UpdateSource = UpdateSource()
    c1: EditablePlotCurve = pl1.addCurve(data_source=s1)
    s1.send_data(CurveData(x=[0, 1, 2, 3, 4], y=[3, 2, 1, 2, 3]))

    s2: UpdateSource = UpdateSource()
    c2: EditablePlotCurve = pl2.addCurve(data_source=s2)
    s2.send_data(CurveData(x=[0, 1, 2, 3, 4], y=[1, 2, 3, 2, 1]))

    if pl1_sel:
        c1.select(selection=pl1_sel)
    if pl2_sel:
        c2.select(selection=pl2_sel)
    for i, p in enumerate(plots):
        p.plotItem.toggle_plot_selection(i == active_plot)

    if active_plot is not None:
        assert bar.selected_plot == plots[active_plot]
    else:
        assert bar.selected_plot is None
    if selection is not None:
        assert bar.current_plots_selection == selection
    else:
        assert bar.current_plots_selection is None


def test_add_action_to_toolbar(qtbot,
                               empty_testing_window):
    qtbot.add_widget(empty_testing_window)
    plot = EditablePlotWidget()
    bar = EditingToolBar()
    bar.connect(plot)
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot)

    source: UpdateSource = UpdateSource()
    curve: EditablePlotCurve = plot.addCurve(data_source=source)
    source.send_data(CurveData(x=[0, 1, 2, 3, 4], y=[3, 2, 1, 2, 3]))
    curve.select(selection=QtCore.QRectF(0, 1.5, 4, 2))

    action = QtWidgets.QAction(qta.icon("fa5b.reddit-alien"), "My Transformation")
    transformation_calls = 0

    def transformation(curve: CurveData):
        nonlocal transformation_calls
        transformation_calls += 1
        assert curve == CurveData(x=[0, 1, 3, 4], y=[3, 2, 2, 3])
        curve.y *= 2
        return curve

    old_transformation_count = len(bar.actions())
    bar.add_transformation(action, transformation)
    new_transformation_count = len(bar.actions())
    assert new_transformation_count == old_transformation_count + 1
    bar.widgetForAction(action).click()
    assert transformation_calls == 1

    curve_x, curve_y = curve.getData()
    assert np.array_equal(curve_x, [0, 1, 2, 3, 4])
    assert np.array_equal(curve_y, [6, 4, 1, 4, 6])


def test_remove_action_from_toolbar(qtbot,
                                    empty_testing_window):
    qtbot.add_widget(empty_testing_window)
    plot = EditablePlotWidget()
    bar = EditingToolBar()
    bar.connect(plot)
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot)

    action = QtWidgets.QAction(qta.icon("fa5b.reddit-alien"), "My Transformation")

    def transformation(*_):
        pass

    old_transformation_count = len(bar.actions())
    bar.add_transformation(action, transformation)
    assert len(bar.actions()) == old_transformation_count + 1
    bar.remove_transformation(action)
    assert len(bar.actions()) == old_transformation_count
    assert action not in bar._transformation_actions


def test_redo_undo_button_enabled(qtbot, empty_testing_window):
    """Check if the undo button gets properly enabled / disabled"""
    qtbot.add_widget(empty_testing_window)
    plot = EditablePlotWidget()
    plot_2 = EditablePlotWidget()
    bar = EditingToolBar()
    bar.connect([plot, plot_2])
    empty_testing_window.addToolBar(bar)
    empty_testing_window.cw_layout.addWidget(plot)
    empty_testing_window.cw_layout.addChildWidget(plot)

    # In the beginning everything is disabled
    assert not bar.send_action.isEnabled()
    assert not bar.undo_action.isEnabled()
    assert not bar.redo_action.isEnabled()

    source = UpdateSource()
    curve: EditablePlotCurve = plot.addCurve(data_source=source)
    source.send_data(CurveData([0, 1, 2, 3, 4], [3, 2, 1, 2, 3]))
    curve.select(QtCore.QRectF(-0.25, 1.75, 1.5, 1.5))
    curve.replace_selection(CurveData([0, 1], [6, 4]))

    # Selection replaces -> undoable & sendable
    assert bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert not bar.redo_action.isEnabled()

    # Plot Switch
    plot_2.plotItem.toggle_plot_selection(True)
    assert not bar.send_action.isEnabled()  # We do not have a curve in this plot
    assert not bar.undo_action.isEnabled()
    assert not bar.redo_action.isEnabled()
    plot.plotItem.toggle_plot_selection(True)
    assert bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert not bar.redo_action.isEnabled()

    # Undo
    bar.undo()
    assert not bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert bar.redo_action.isEnabled()

    # Plot Switch
    plot_2.plotItem.toggle_plot_selection(True)
    assert not bar.undo_action.isEnabled()
    assert not bar.send_action.isEnabled()  # We do not have a curve in this plot
    assert not bar.redo_action.isEnabled()
    plot.plotItem.toggle_plot_selection(True)
    assert not bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert bar.redo_action.isEnabled()

    # Redo
    bar.redo()
    assert bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert not bar.redo_action.isEnabled()

    # Plot Switch
    plot_2.plotItem.toggle_plot_selection(True)
    assert not bar.undo_action.isEnabled()
    assert not bar.send_action.isEnabled()  # We do not have a curve in this plot
    assert not bar.redo_action.isEnabled()
    plot.plotItem.toggle_plot_selection(True)
    assert bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert not bar.redo_action.isEnabled()

    # Send changes -> should not have an effect
    bar.send()
    assert bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert not bar.redo_action.isEnabled()

    # Plot Switch
    plot_2.plotItem.toggle_plot_selection(True)
    assert not bar.undo_action.isEnabled()
    assert not bar.send_action.isEnabled()  # We do not have a curve in this plot
    assert not bar.redo_action.isEnabled()
    plot.plotItem.toggle_plot_selection(True)
    assert bar.undo_action.isEnabled()
    assert bar.send_action.isEnabled()
    assert not bar.redo_action.isEnabled()


# ~~~~~~~~~~~~~~~~ Tests for the provided standard functions ~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("input_val, param, output_val", [
    (CurveData([], []), 0, CurveData([], [])),
    (CurveData([1], [1]), 0, CurveData([1], [0])),
    (CurveData([0, 1], [1, 2]), 0, CurveData([0, 1], [0, 0])),
])
def test_func_align(input_val, param, output_val):
    assert StandardTransformations.aligned(input_val, param) == output_val


@pytest.mark.parametrize("input_val, output_val", [
    (CurveData([0, 1, 2], [0, 1, 2]), CurveData([0, 1, 2], [0, 1, 2])),
    (CurveData([0, 1, 2, 3], [1, 0, 1, 2]), CurveData([0, 1, 2, 3], [0.4, 0.8, 1.2, 1.6])),
])
def test_func_linfit(input_val, output_val):
    assert StandardTransformations.lin_fitted(input_val) == output_val


@pytest.mark.parametrize("input_val, degree", [
    (CurveData([0, 1, 2], [0, 1, 2]), 1),
    (CurveData([0, 1, 2, 3], [1, 0, 1, 2]), 2),
])
def test_func_polyfit(input_val, degree):
    coefficients = np.polyfit(input_val.x, input_val.y, degree)
    output_val = np.poly1d(coefficients)(input_val.y)
    actual = StandardTransformations.poly_fitted(input_val, degree)
    assert np.allclose(actual.y, output_val)
    assert np.array_equal(actual.x, input_val.x)


@pytest.mark.parametrize("input_val, params, output_val", [
    (CurveData([0, 1, 2], [0, 1, 2]), (0, 1), CurveData([0, 1, 2], [0, 1, 2])),
    (CurveData([0, 1, 2], [0, 1, 2]), (1, 1), CurveData([1, 2], [1, 2])),
    (CurveData([0, 1, 2, 3], [0, 1, 2, 3]), (0, 2), CurveData([0, 2], [0, 2])),
    (CurveData([0, 1, 2, 3], [0, 1, 2, 3]), (1, 2), CurveData([1, 3], [1, 3])),
])
def test_func_reduce_to_nth_point(input_val, params, output_val):
    assert StandardTransformations.reduced_to_nth_point(input_val, *params) == output_val


@pytest.mark.parametrize("input_val, output_val", [
    (CurveData([0, 1, 2], [0, 1, 2]), CurveData([], [])),
])
def test_func_delete(input_val, output_val):
    assert StandardTransformations.cleared(input_val) == output_val


@pytest.mark.parametrize("input_val, param, output_val", [
    (CurveData([], []), 1, CurveData([], [])),
    (CurveData([0, 1, 2], [0, 1, 2]), 1, CurveData([0, 1, 2], [1, 2, 3])),
    (CurveData([0, 1, 2], [0, 1, 2]), 0.1, CurveData([0, 1, 2], [0.1, 1.1, 2.1])),
    (CurveData([0, 1, 2], [0, 1, 2]), -1, CurveData([0, 1, 2], [-1, 0, 1])),
])
def test_func_move(input_val, param, output_val):
    assert StandardTransformations.moved(input_val, param) == output_val


@pytest.mark.parametrize("input_val, params, output_val", [
    (CurveData([0, 1, 2, 3], [0, 1, 2, 4]),
     (3, 2),
     CurveData([0, 1, 2, 3], savgol_filter([0, 1, 2, 4],
                                           window_length=3,
                                           polyorder=2))),
])
def test_func_smooth_curve(input_val, params, output_val):
    assert StandardTransformations.smoothed(input_val, *params) == output_val
