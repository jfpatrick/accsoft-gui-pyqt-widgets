import pytest
import numpy as np
from typing import Type, List, Tuple, Any
from pytestqt.qtbot import QtBot
from unittest import mock
from qtpy.QtWidgets import QDialogButtonBox
from PyQt5.QtTest import QAbstractItemModelTester
from accwidgets.graph import ExPlotWidget, ScrollingPlotWidget, CyclicPlotWidget, StaticPlotWidget, UpdateSource
from accwidgets.graph.designer import PlotLayerEditingDialog, PlotLayerTableModel
from .mock_utils.widget_test_window import MinimalTestWindow


_PLOT_TYPES = [ScrollingPlotWidget,
               CyclicPlotWidget,
               StaticPlotWidget]
"""Plot Types against which we want to execute the extension tests."""


@pytest.fixture
def table_model():
    def model_builder(qtbot: QtBot, plot: ExPlotWidget) -> Tuple[PlotLayerTableModel, PlotLayerEditingDialog]:
        dialog = PlotLayerEditingDialog(plot=plot)
        qtbot.add_widget(dialog)
        _ = QAbstractItemModelTester(dialog.table.model())  # Test for common model mistakes
        return dialog.table.model(), dialog
    return model_builder


def compare_table_contents(model: PlotLayerTableModel, desired: List[List[Any]]):
    assert model.rowCount() == len(desired)
    assert model.columnCount() == len(desired[0])
    for i, row in enumerate(desired):
        for j, cell in enumerate(row):
            assert str(model.data(model.index(i, j))) == str(cell)

# ~~~~~ Read data from plot and display in dialog ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_data_standard_plot(qtbot,
                                         table_model,
                                         empty_testing_window: MinimalTestWindow,
                                         plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, _ = table_model(qtbot=qtbot, plot=plot)
    compare_table_contents(model=model, desired=[
        ["x", "", True, "Auto", "Auto"],
        ["y", "", True, "Auto", "Auto"],
    ])


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_data_plot_with_custom_view_ranges_and_labels(qtbot,
                                                                   table_model,
                                                                   empty_testing_window: MinimalTestWindow,
                                                                   plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.setRange(xRange=(-5, 5), yRange=(-2, 8), padding=0.0)
    plot.setLabels(bottom="x", top="x", left="y", right="y")
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, _ = table_model(qtbot=qtbot, plot=plot)
    compare_table_contents(model=model, desired=[
        ["x", "x", False, -5.0, 5.0],
        ["y", "y", False, -2.0, 8.0],
    ])


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_data_plot_with_additional_standard_layer(qtbot,
                                                               table_model,
                                                               empty_testing_window: MinimalTestWindow,
                                                               plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.add_layer("my new layer")
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, _ = table_model(qtbot=qtbot, plot=plot)
    compare_table_contents(model=model, desired=[
        ["x", "", True, "Auto", "Auto"],
        ["y", "", True, "Auto", "Auto"],
        ["my new layer", "", True, "Auto", "Auto"],
    ])


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_data_plot_with_additional_altered_layer(qtbot,
                                                              table_model,
                                                              empty_testing_window: MinimalTestWindow,
                                                              plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.add_layer("l1")
    plot.setLabel(axis="l1", text="some label text")
    plot.setRange(l1=(-100, 100), padding=0.0)
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, _ = table_model(qtbot=qtbot, plot=plot)
    compare_table_contents(model=model, desired=[
        ["x", "", True, "Auto", "Auto"],
        ["y", "", True, "Auto", "Auto"],
        ["l1", "some label text", False, -100.0, 100.0],
    ])


# ~~~~~ Update Plot using the Layer Dialog ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


_COLUMN_LAYER_ID = 0
_COLUMN_LABEL_TEXT = 1
_COLUMN_AUTO_RANGE = 2
_COLUMN_RANGE_MIN = 3
_COLUMN_RANGE_MAX = 4


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_set_view_ranges(qtbot,
                                      table_model,
                                      empty_testing_window: MinimalTestWindow,
                                      plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, dialog = table_model(qtbot=qtbot, plot=plot)
    model.setData(model.index(0, _COLUMN_LABEL_TEXT), "New X Label")
    model.setData(model.index(0, _COLUMN_AUTO_RANGE), False)
    model.setData(model.index(0, _COLUMN_RANGE_MIN), -123.0)
    model.setData(model.index(0, _COLUMN_RANGE_MAX), 456.0)
    # Change settings for the default y-axis
    model.setData(model.index(1, _COLUMN_LABEL_TEXT), "New Y Label")
    model.setData(model.index(1, _COLUMN_AUTO_RANGE), False)
    model.setData(model.index(1, _COLUMN_RANGE_MIN), -1.0)
    model.setData(model.index(1, _COLUMN_RANGE_MAX), 1.0)
    # Pretend we are inside designer and cursor is found
    with mock.patch("accwidgets.graph.designer.designer_extensions.get_designer_cursor", return_value=plot):
        dialog.buttons.button(QDialogButtonBox.Ok).click()
    assert plot.getAxis("left").label.toPlainText().strip() == "New Y Label"
    assert plot.getAxis("bottom").label.toPlainText().strip() == "New X Label"
    assert not any(plot.getViewBox().autoRangeEnabled())
    assert np.allclose(plot.getViewBox().targetRange()[0], [-123.0, 456.0])
    assert np.allclose(plot.getViewBox().targetRange()[1], [-1.0, 1.0])


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_add_layer(qtbot,
                                table_model,
                                empty_testing_window: MinimalTestWindow,
                                plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, dialog = table_model(qtbot=qtbot, plot=plot)
    # Add a layer through the dialog and change it
    dialog.add_btn.click()
    model.setData(model.index(2, _COLUMN_LABEL_TEXT), "layer")
    model.setData(model.index(2, _COLUMN_AUTO_RANGE), False)
    model.setData(model.index(2, _COLUMN_RANGE_MIN), -12.0)
    model.setData(model.index(2, _COLUMN_RANGE_MAX), 8.0)
    # Pretend we are inside designer and cursor is found
    with mock.patch("accwidgets.graph.designer.designer_extensions.get_designer_cursor", return_value=plot):
        dialog.buttons.button(QDialogButtonBox.Ok).click()
    # Check if new layer is there
    assert len(plot.plotItem.layers) == 2
    lid = plot.plotItem.layers[1].id
    assert plot.getAxis(lid).label.toPlainText().strip() == "layer"
    assert not plot.getViewBox(lid).autoRangeEnabled()[1]
    assert np.allclose(plot.getViewBox(lid).targetRange()[1], [-12, 8])


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_remove_layer(qtbot,
                                   table_model,
                                   empty_testing_window: MinimalTestWindow,
                                   plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.add_layer("remove_me")
    assert len(plot.plotItem.layers) == 2
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, dialog = table_model(qtbot=qtbot, plot=plot)
    # Remove layer by selecting it and pressing the deleted button
    dialog.table.selectRow(2)
    dialog.remove_btn.click()
    # Pretend we are inside designer and cursor is found
    with mock.patch("accwidgets.graph.designer.designer_extensions.get_designer_cursor", return_value=plot):
        dialog.buttons.button(QDialogButtonBox.Ok).click()
    # Check if new layer is there
    assert len(plot.plotItem.layers) == 1


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_rename_layer(qtbot,
                                   table_model,
                                   empty_testing_window: MinimalTestWindow,
                                   plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.add_layer("rename_me")
    plot.setRange(rename_me=(-12.0, 34.0), padding=0)
    plot.setLabels(rename_me="my label")
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, dialog = table_model(qtbot=qtbot, plot=plot)
    model.setData(model.index(2, 0), "renamed")
    # Pretend we are inside designer and cursor is found
    with mock.patch("accwidgets.graph.designer.designer_extensions.get_designer_cursor", return_value=plot):
        dialog.buttons.button(QDialogButtonBox.Ok).click()
    # Check if new layer is there
    assert len(plot.plotItem.layers) == 2
    assert plot.plotItem.layers[1].id == "renamed"
    assert np.allclose(plot.getViewBox("renamed").targetRange()[1], [-12.0, 34.0])
    assert plot.getAxis("renamed").label.toPlainText().strip() == "my label"


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_press_cancel_button(qtbot,
                                          table_model,
                                          empty_testing_window: MinimalTestWindow,
                                          plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.add_layer("l1")
    plot.setRange(xRange=(-5.0, 5.0), yRange=(-2.0, 8.0), l1=(-10.0, 100.0), padding=0.0)
    plot.setLabels(bottom="x", top="x", left="y", right="y", l1="l1")
    # Plot is configured as we want
    assert len(plot.plotItem.layers) == 2  # do not forget the default one
    assert plot.getAxis("left").label.toPlainText().strip() == "y"
    assert plot.getAxis("bottom").label.toPlainText().strip() == "x"
    assert plot.getAxis("l1").label.toPlainText().strip() == "l1"
    assert not any(plot.getViewBox().autoRangeEnabled())
    assert np.allclose(plot.getViewBox().targetRange()[0], [-5.0, 5.0])
    assert np.allclose(plot.getViewBox().targetRange()[1], [-2.0, 8.0])
    assert np.allclose(plot.getViewBox("l1").targetRange()[1], [-10.0, 100.0])
    # Lets change some stuff in the dialog
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    model, dialog = table_model(qtbot=qtbot, plot=plot)
    model.setData(model.index(0, _COLUMN_LABEL_TEXT), "New X Label")
    model.setData(model.index(0, _COLUMN_AUTO_RANGE), True)
    model.setData(model.index(1, _COLUMN_LABEL_TEXT), "New Y Label")
    model.setData(model.index(1, _COLUMN_AUTO_RANGE), True)
    model.setData(model.index(2, _COLUMN_LABEL_TEXT), "Layer")
    model.setData(model.index(2, _COLUMN_AUTO_RANGE), True)
    dialog.add_btn.click()
    model.setData(model.index(3, _COLUMN_LABEL_TEXT), "Added")
    model.setData(model.index(3, _COLUMN_AUTO_RANGE), False)
    model.setData(model.index(3, _COLUMN_RANGE_MIN), -100.0)
    model.setData(model.index(3, _COLUMN_RANGE_MAX), 100.0)
    # CANCEL
    # Pretend we are inside designer and cursor is found
    with mock.patch("accwidgets.graph.designer.designer_extensions.get_designer_cursor", return_value=plot):
        dialog.buttons.button(QDialogButtonBox.Cancel).click()
    # Plot should not have changed
    assert len(plot.plotItem.layers) == 2  # do not forget the default one
    assert plot.getAxis("left").label.toPlainText().strip() == "y"
    assert plot.getAxis("bottom").label.toPlainText().strip() == "x"
    assert plot.getAxis("l1").label.toPlainText().strip() == "l1"
    assert not any(plot.getViewBox().autoRangeEnabled())
    assert np.allclose(plot.getViewBox().targetRange()[0], [-5.0, 5.0])
    assert np.allclose(plot.getViewBox().targetRange()[1], [-2.0, 8.0])
    assert np.allclose(plot.getViewBox("l1").targetRange()[1], [-10.0, 100.0])


# ~~~~~~~~~~~~~ Test change layers that contain items ~~~~~~~~~~~~~~~~~~~~~~~~

# These tests are especially interesting for ComRAD, since there the plot can
# already contain items.


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_modify_non_empty_layer(qtbot,
                                table_model,
                                empty_testing_window: MinimalTestWindow,
                                plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.add_layer("l1")
    default_item = plot.plotItem.addCurve(data_source=UpdateSource())
    layer_item = plot.plotItem.addCurve(data_source=UpdateSource(), layer="l1")
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    # Check current situation
    assert len(plot.plotItem.layers) == 2
    assert len(plot.getViewBox().addedItems) == 1
    assert default_item in plot.getViewBox().addedItems
    assert len(plot.getViewBox("l1").addedItems) == 1
    assert layer_item in plot.getViewBox("l1").addedItems
    # Lets modify the layer in the dialog
    model, dialog = table_model(qtbot=qtbot, plot=plot)
    model.setData(model.index(2, _COLUMN_LAYER_ID), "new_id")
    # Apply
    # Pretend we are inside designer and cursor is found
    with mock.patch("accwidgets.graph.designer.designer_extensions.get_designer_cursor", return_value=plot):
        dialog.buttons.button(QDialogButtonBox.Ok).click()
    # Plot should not have changed
    with pytest.raises(KeyError):
        plot.plotItem.getViewBox("l1")
    assert len(plot.plotItem.layers) == 2
    assert len(plot.getViewBox().addedItems) == 1
    assert default_item in plot.getViewBox().addedItems
    assert len(plot.getViewBox("new_id").addedItems) == 1
    assert layer_item in plot.getViewBox("new_id").addedItems


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_remove_non_empty_layer(qtbot,
                                table_model,
                                empty_testing_window: MinimalTestWindow,
                                plot_type: Type[ExPlotWidget]):
    plot = plot_type()
    plot.add_layer("l1")
    default_item = plot.plotItem.addCurve(data_source=UpdateSource())
    layer_item = plot.plotItem.addCurve(data_source=UpdateSource(), layer="l1")
    empty_testing_window.setCentralWidget(plot)
    qtbot.add_widget(empty_testing_window)
    # Check current situation
    assert len(plot.plotItem.layers) == 2
    assert len(plot.getViewBox().addedItems) == 1
    assert default_item in plot.getViewBox().addedItems
    assert len(plot.getViewBox("l1").addedItems) == 1
    assert layer_item in plot.getViewBox("l1").addedItems
    # Remove extra layer
    _, dialog = table_model(qtbot=qtbot, plot=plot)
    dialog.table.selectRow(2)
    dialog.remove_btn.click()
    # Pretend we are inside designer and cursor is found
    with mock.patch("accwidgets.graph.designer.designer_extensions.get_designer_cursor", return_value=plot):
        dialog.buttons.button(QDialogButtonBox.Ok).click()
    # Plot should not have changed
    with pytest.raises(KeyError):
        plot.plotItem.getViewBox("l1")
    assert len(plot.plotItem.layers) == 1
    assert len(plot.getViewBox().addedItems) == 2
    assert set(plot.getViewBox().addedItems) == {default_item, layer_item}
