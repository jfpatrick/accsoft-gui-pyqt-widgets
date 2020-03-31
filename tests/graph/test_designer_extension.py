from typing import Type
import pytest
from qtpy.QtWidgets import QDialogButtonBox
import numpy as np

import accwidgets.graph as accgraph
from accwidgets.graph.designer.designer_extensions import PlotLayerEditingDialog
from .mock_utils.widget_test_window import MinimalTestWindow


_PLOT_TYPES = [accgraph.ScrollingPlotWidget,
               accgraph.CyclicPlotWidget,
               accgraph.StaticPlotWidget]
"""Plot Types against which we want to execute the extension tests."""


# ~~~~~ Read data from plot and display in dialog ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_tmp_data_standard_plot(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # check if all default layers are there
    table_values = dialog.layer_table_model._tmp
    assert set(table_values.layer_ids) == set()
    assert table_values.axis_labels == {"bottom": "",
                                        "top": "",
                                        "left": "",
                                        "right": ""}
    assert table_values.axis_ranges == {"x": "auto",
                                        "y": "auto"}


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_tmp_data_plot_with_custom_view_ranges_and_labels(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.setRange(xRange=(-5, 5), yRange=(-2, 8), padding=0.0)
    plot.setLabels(bottom="x", top="x", left="y", right="y")
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # check if all default layers are there
    table_values = dialog.layer_table_model._tmp
    assert set(table_values.layer_ids) == set()
    assert table_values.axis_labels == {"bottom": "x",
                                        "top": "x",
                                        "left": "y",
                                        "right": "y"}
    assert table_values.axis_ranges == {"x": [-5, 5],
                                        "y": [-2, 8]}


@pytest.mark.parametrize(
    "plot_type",
    [
        accgraph.ScrollingPlotWidget,
        accgraph.CyclicPlotWidget,
        accgraph.StaticPlotWidget,
    ],
)
def test_layer_dialog_tmp_data_plot_with_additional_standard_layer(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("my new layer")
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # check if all default layers are there
    table_values = dialog.layer_table_model._tmp
    assert set(table_values.layer_ids) == {"my new layer"}
    assert table_values.axis_labels == {"bottom": "",
                                        "top": "",
                                        "left": "",
                                        "right": "",
                                        "my new layer": ""}
    assert table_values.axis_ranges == {"x": "auto",
                                        "y": "auto",
                                        "my new layer": "auto"}


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_tmp_data_plot_with_additional_altered_layer(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("l1")
    plot.setLabel(axis="l1", text="some label text")
    plot.setRange(l1=(-100, 100), padding=0.0)
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # check if all default layers are there
    table_values = dialog.layer_table_model._tmp
    assert set(table_values.layer_ids) == {"l1"}
    assert table_values.axis_labels == {"bottom": "",
                                        "top": "",
                                        "left": "",
                                        "right": "",
                                        "l1": "some label text"}
    assert table_values.axis_ranges == {"x": "auto",
                                        "y": "auto",
                                        "l1": [-100, 100]}


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_table_view(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("l1")
    plot.setLabels(bottom="x-axis",
                   left="y-axis",
                   l1="some label text")
    plot.setRange(yRange=(-10, 0),
                  l1=(-100, 100),
                  padding=0.0)
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    model = dialog.layer_table_model
    expected = [
        ["x", "x-axis", True, 0, 1],
        ["y", "y-axis", False, -10, 0],
        ["l1", "some label text", False, -100, 100],
    ]
    for i, row in enumerate(expected):
        for j, cell in enumerate(row):
            assert model.data(index=model.index(i, j)) == cell


# ~~~~~ Update Plot using the Layer Dialog ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


_COLUMN_LAYER_ID = 0
_COLUMN_LABEL_TEXT = 1
_COLUMN_AUTO_RANGE = 2
_COLUMN_RANGE_MIN = 3
_COLUMN_RANGE_MAX = 4


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_set_view_ranges(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # Change settings for the default x axis
    model = dialog.layer_table_model
    model.setData(index=model.index(0, _COLUMN_LABEL_TEXT), value="New X Label")
    model.setData(index=model.index(0, _COLUMN_AUTO_RANGE), value=False)
    model.setData(index=model.index(0, _COLUMN_RANGE_MIN), value=-123)
    model.setData(index=model.index(0, _COLUMN_RANGE_MAX), value=456)
    # Change settings for the default y-axis
    model.setData(index=model.index(1, _COLUMN_LABEL_TEXT), value="New Y Label")
    model.setData(index=model.index(1, _COLUMN_AUTO_RANGE), value=False)
    model.setData(index=model.index(1, _COLUMN_RANGE_MIN), value=-1)
    model.setData(index=model.index(1, _COLUMN_RANGE_MAX), value=1)
    dialog.button_box.button(QDialogButtonBox.Apply).click()
    assert plot.getAxis("left").label.toPlainText().strip() == "New Y Label"
    assert plot.getAxis("bottom").label.toPlainText().strip() == "New X Label"
    assert not any(plot.getViewBox().autoRangeEnabled())
    assert np.allclose(plot.getViewBox().targetRange()[0], [-123, 456])
    assert np.allclose(plot.getViewBox().targetRange()[1], [-1, 1])


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_add_layer(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # Add a layer through the dialog and change it
    model = dialog.layer_table_model
    dialog.add_button.click()
    model.setData(index=model.index(2, _COLUMN_LABEL_TEXT), value="layer")
    model.setData(index=model.index(2, _COLUMN_AUTO_RANGE), value=False)
    model.setData(index=model.index(2, _COLUMN_RANGE_MIN), value=-12)
    model.setData(index=model.index(2, _COLUMN_RANGE_MAX), value=8)
    dialog.button_box.button(QDialogButtonBox.Apply).click()
    # Check if new layer is there
    assert len(plot.plotItem.layers) == 2
    lid = plot.plotItem.layers[1].id
    assert plot.getAxis(lid).label.toPlainText().strip() == "layer"
    assert not plot.getViewBox(lid).autoRangeEnabled()[1]
    assert np.allclose(plot.getViewBox(lid).targetRange()[1], [-12, 8])


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_remove_layer(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("remove_me")
    assert len(plot.plotItem.layers) == 2
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # Remove layer by selecting it and pressing the deleted button
    dialog.layer_table_view.selectRow(2)
    dialog.remove_button.click()
    dialog.button_box.button(QDialogButtonBox.Apply).click()
    # Check if new layer is there
    assert len(plot.plotItem.layers) == 1


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_rename_layer(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("rename_me")
    plot.setRange(rename_me=(-12, 34), padding=0)
    plot.setLabels(rename_me="my label")
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # Remove layer by selecting it and pressing the deleted button
    model = dialog.layer_table_model
    model.setData(index=model.index(2, 0), value="renamed")
    dialog.button_box.button(QDialogButtonBox.Apply).click()
    # Check if new layer is there
    assert len(plot.plotItem.layers) == 2
    assert plot.plotItem.layers[1].id == "renamed"
    assert np.allclose(plot.getViewBox("renamed").targetRange()[1], [-12, 34])
    assert plot.getAxis("renamed").label.toPlainText().strip() == "my label"


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_layer_dialog_press_cancel_button(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("l1")
    plot.setRange(xRange=(-5, 5),
                  yRange=(-2, 8),
                  l1=(-10, 100),
                  padding=0.0)
    plot.setLabels(bottom="x", top="x", left="y", right="y", l1="l1")
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # Plot is configured as we want
    assert len(plot.plotItem.layers) == 2  # do not forget the default one
    assert plot.getAxis("left").label.toPlainText().strip() == "y"
    assert plot.getAxis("bottom").label.toPlainText().strip() == "x"
    assert plot.getAxis("l1").label.toPlainText().strip() == "l1"
    assert not any(plot.getViewBox().autoRangeEnabled())
    assert np.allclose(plot.getViewBox().targetRange()[0], [-5, 5])
    assert np.allclose(plot.getViewBox().targetRange()[1], [-2, 8])
    assert np.allclose(plot.getViewBox("l1").targetRange()[1], [-10, 100])
    # Lets change some stuff in the dialog
    model = dialog.layer_table_model
    model.setData(index=model.index(0, _COLUMN_LABEL_TEXT), value="New X Label")
    model.setData(index=model.index(0, _COLUMN_AUTO_RANGE), value=True)
    model.setData(index=model.index(1, _COLUMN_LABEL_TEXT), value="New Y Label")
    model.setData(index=model.index(1, _COLUMN_AUTO_RANGE), value=True)
    model.setData(index=model.index(2, _COLUMN_LABEL_TEXT), value="Layer")
    model.setData(index=model.index(2, _COLUMN_AUTO_RANGE), value=True)
    dialog.add_button.click()
    model.setData(index=model.index(3, _COLUMN_LABEL_TEXT), value="Added")
    model.setData(index=model.index(3, _COLUMN_AUTO_RANGE), value=False)
    model.setData(index=model.index(3, _COLUMN_RANGE_MIN), value=-100)
    model.setData(index=model.index(3, _COLUMN_RANGE_MAX), value=100)
    # CANCEL
    dialog.button_box.button(QDialogButtonBox.Cancel).click()
    # Plot should not have changed
    assert len(plot.plotItem.layers) == 2  # do not forget the default one
    assert plot.getAxis("left").label.toPlainText().strip() == "y"
    assert plot.getAxis("bottom").label.toPlainText().strip() == "x"
    assert plot.getAxis("l1").label.toPlainText().strip() == "l1"
    assert not any(plot.getViewBox().autoRangeEnabled())
    assert np.allclose(plot.getViewBox().targetRange()[0], [-5, 5])
    assert np.allclose(plot.getViewBox().targetRange()[1], [-2, 8])
    assert np.allclose(plot.getViewBox("l1").targetRange()[1], [-10, 100])


# ~~~~~~~~~~~~~ Test change layers that contain items ~~~~~~~~~~~~~~~~~~~~~~~~

# These tests are especially interesting for ComRAD, since there the plot can
# already contain items.


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_modify_non_empty_layer(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("l1")
    default_item = plot.plotItem.addCurve(data_source=accgraph.UpdateSource())
    layer_item = plot.plotItem.addCurve(data_source=accgraph.UpdateSource(),
                                        layer="l1")
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # Check current situation
    assert len(plot.plotItem.layers) == 2
    assert len(plot.getViewBox().addedItems) == 1
    assert default_item in plot.getViewBox().addedItems
    assert len(plot.getViewBox("l1").addedItems) == 1
    assert layer_item in plot.getViewBox("l1").addedItems
    # Lets modify the layer in the dialog
    model = dialog.layer_table_model
    model.setData(index=model.index(2, _COLUMN_LAYER_ID), value="new_id")
    # Apply
    dialog.button_box.button(QDialogButtonBox.Apply).click()
    # Plot should not have changed
    with pytest.raises(KeyError):
        plot.plotItem.getViewBox("l1")
    assert len(plot.plotItem.layers) == 2
    assert len(plot.getViewBox().addedItems) == 1
    assert default_item in plot.getViewBox().addedItems
    assert len(plot.getViewBox("new_id").addedItems) == 1
    assert layer_item in plot.getViewBox("new_id").addedItems


@pytest.mark.parametrize("plot_type", _PLOT_TYPES)
def test_remove_non_empty_layer(
    qtbot,
    empty_testing_window: MinimalTestWindow,
    plot_type: Type[accgraph.ExPlotWidget],
):
    plot = plot_type()
    plot.add_layer("l1")
    default_item = plot.plotItem.addCurve(data_source=accgraph.UpdateSource())
    layer_item = plot.plotItem.addCurve(data_source=accgraph.UpdateSource(),
                                        layer="l1")
    empty_testing_window.setCentralWidget(plot)
    dialog = PlotLayerEditingDialog(plot=plot)
    qtbot.addWidget(dialog)
    qtbot.addWidget(empty_testing_window)
    dialog.show()
    # Check current situation
    assert len(plot.plotItem.layers) == 2
    assert len(plot.getViewBox().addedItems) == 1
    assert default_item in plot.getViewBox().addedItems
    assert len(plot.getViewBox("l1").addedItems) == 1
    assert layer_item in plot.getViewBox("l1").addedItems
    # Remove extra layer
    dialog.layer_table_view.selectRow(2)
    dialog.remove_button.click()
    dialog.button_box.button(QDialogButtonBox.Apply).click()
    # Plot should not have changed
    with pytest.raises(KeyError):
        plot.plotItem.getViewBox("l1")
    assert len(plot.plotItem.layers) == 1
    assert len(plot.getViewBox().addedItems) == 2
    assert set(plot.getViewBox().addedItems) == {default_item, layer_item}
