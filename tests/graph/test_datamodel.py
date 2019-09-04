"""Tests for the datamodel

Test for appending data to different datamodels, all tests are executed with
different datamodels. The right values for each datamodel are created with
the functions in datamodel_generalization_util.py
"""

from typing import Type

import numpy as np
import pytest

import accsoft_gui_pyqt_widgets.graph as accgraph

from .mock_utils import datamodel_generalization_util as dm_util
from .mock_utils.mock_data_source import MockDataSource

datamodels_to_test = [
    accgraph.CurveDataModel,
    accgraph.BarGraphDataModel,
    accgraph.InjectionBarDataModel,
    accgraph.TimestampMarkerDataModel
]

# ~~~~~ Simple ordering for different datamodels ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_datamodel_is_empty(model_type: Type[accgraph.BaseDataModel]):
    """ Check if datamodel is empty is correct """
    data_source: MockDataSource = MockDataSource()
    datamodel: accgraph.BarGraphDataModel = model_type(data_source=data_source, buffer_size=5)
    assert datamodel.is_empty()
    data_source.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert not datamodel.is_empty()
    data_source.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [2.0, 3.0, 4.0, 5.0]))
    assert not datamodel.is_empty()
    data_source.emit_new_object(dm_util.create_fitting_object(datamodel, 6.0))
    assert not datamodel.is_empty()


@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_data_source_replacement(model_type: Type[accgraph.BaseDataModel]):
    """Check replacement of data source with and without buffer clearing"""
    data_source_1: MockDataSource = MockDataSource()
    data_source_2: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    assert datamodel.get_data_source() is data_source_1
    assert datamodel.is_empty()
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert not datamodel.is_empty()
    assert dm_util.check_datamodel(datamodel, 5, [1.0])
    datamodel.replace_data_source(data_source_2, clear_buffer=False)
    assert datamodel.get_data_source() is data_source_2
    assert not datamodel.is_empty()
    assert dm_util.check_datamodel(datamodel, 5, [1.0])
    datamodel.replace_data_source(data_source_1, clear_buffer=True)
    assert datamodel.get_data_source() is data_source_1
    assert datamodel.is_empty()
    assert dm_util.check_datamodel(datamodel, 5, [])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert not datamodel.is_empty()


# ~~~~~ Databuffer tests ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_append_long_list_of_simple_values(model_type: Type[accgraph.BaseDataModel]):
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=0.0, stop=101.0)))
    assert dm_util.check_datamodel(datamodel, 5, [98.0, 99.0, 100.0])


@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_append_list_of_points_longer_than_size_into_non_empty_buffer(model_type: Type[accgraph.BaseDataModel]):
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=5.0, stop=10.0)))
    assert dm_util.check_datamodel(datamodel, 5, [5.0, 6.0, 7.0, 8.0, 9.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=10.0, stop=101.0)))
    assert dm_util.check_datamodel(datamodel, 5, [98.0, 99.0, 100.0])


@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_append_list_of_points_longer_than_size_into_half_filled_buffer(model_type: Type[accgraph.BaseDataModel]):
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=7.0, stop=10.0)))
    assert dm_util.check_datamodel(datamodel, 5, [7.0, 8.0, 9.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=10.0, stop=101.0)))
    assert dm_util.check_datamodel(datamodel, 5, [98.0, 99.0, 100.0])


@pytest.mark.parametrize("model_type", [accgraph.CurveDataModel])
def test_append_nan_point_for_line_splitting(model_type: Type[accgraph.BaseDataModel]):
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert dm_util.check_datamodel(datamodel, 5, [1.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    assert dm_util.check_datamodel(datamodel, 5, [1.0, np.nan])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 2.0))
    assert dm_util.check_datamodel(datamodel, 5, [1.0, np.nan, 2.0])


@pytest.mark.parametrize("model_type", [accgraph.CurveDataModel])
def test_sort_values_around_nan_value(model_type: Type[accgraph.BaseDataModel]):
    """Test sorting values right next to a NaN value"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 3.0))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 2.0))
    assert dm_util.check_datamodel(datamodel, 5, [1.0, np.nan, 2.0, 3.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 0.0))
    assert dm_util.check_datamodel(datamodel, 5, [0.0, 1.0, np.nan, 2.0, 3.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [0.5, 2.5]))
    assert dm_util.check_datamodel(datamodel, 5, [2.0, 2.5, 3.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [2.75, np.nan]))
    assert dm_util.check_datamodel(datamodel, 5, [2.0, 2.5, 2.75, 3.0, np.nan])


@pytest.mark.parametrize("model_type", [accgraph.CurveDataModel])
def test_append_nan_on_first_position(model_type: Type[accgraph.BaseDataModel]):
    """First value appended to the DataModel is NaN"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 2.0))
    assert dm_util.check_datamodel(datamodel, 5, [np.nan, 1.0, 2.0])


@pytest.mark.parametrize("model_type", [accgraph.CurveDataModel])
def test_nan_get_first_value_after_shift(model_type: Type[accgraph.BaseDataModel]):
    """First value after shift in databuffer is NaN"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [0.0, 1.0, 2.0]))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    assert dm_util.check_datamodel(datamodel, 5, [0.0, 1.0, 2.0, np.nan])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 3.0))
    assert dm_util.check_datamodel(datamodel, 5, [0.0, 1.0, 2.0, np.nan, 3.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 4.0))
    assert dm_util.check_datamodel(datamodel, 5, [np.nan, 3.0, 4.0])


@pytest.mark.parametrize("model_type", [accgraph.CurveDataModel])
def test_append_list_containing_nan(model_type: Type[accgraph.BaseDataModel]):
    """Append a list with values that contain a nan"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [2.0, 3.0, 4.0]))
    assert dm_util.check_datamodel(datamodel, 5, [2.0, 3.0, 4.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [3.75, np.nan]))
    assert dm_util.check_datamodel(datamodel, 5, [2.0, 3.0, 3.75, 4.0, np.nan])


# ~~~~~ Data Model Subset tesing without clipping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("length_for_buffer", [10, 14])
@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_subset_creation_of_data_model_without_nan_values(model_type: Type[accgraph.BaseDataModel], length_for_buffer: int):
    """Test subset creation from datamodel that does not contain any nan values"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=length_for_buffer)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=1.0, stop=11.0)))
    # Start in front of first value, End in between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], start=-4.4, end=7.9)
    # Start in front of first value, End exactly on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], start=0.0, end=8.0)
    # Start in front of first value, End after last values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], start=0.0, end=11.6)
    # Start on value, End in between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, 4.0, 5.0, 6.0, 7.0], start=2.0, end=7.9)
    # Start on value, End on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], start=2.0, end=8.0)
    # Start on value, End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], start=2.0, end=12.3)
    # Start between values, End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], start=2.3, end=11.2)
    # Start between values, End on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, 4.0, 5.0, 6.0, 7.0, 8.0], start=2.3, end=8.0)
    # Start between values, End between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, 4.0, 5.0, 6.0, 7.0, 8.0], start=2.3, end=8.9)
    # Start in front of first value and End in front of first value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[], start=-15.3, end=0.6)
    # Start after last value and End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[], start=15.3, end=24.6)
    # Exactly one value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[5.0], start=5.0, end=5.0)


@pytest.mark.parametrize("length_for_buffer", [10, 14])
@pytest.mark.parametrize("model_type", [accgraph.CurveDataModel])
def test_subset_creation_of_data_model_with_multiple_nan_values(model_type: Type[accgraph.BaseDataModel], length_for_buffer: int):
    """Test subset creation from datamodel that does contain any nan values"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=length_for_buffer)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=1.0, stop=4.0)))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=4.0, stop=6.0)))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=6.0, stop=9.0)))
    # Start in front of first value, End in between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=0.0, end=7.9)
    # Start in front of first value, End exactly on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=0.0, end=7.0)
    # Start in front of first value, End after last values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0, 8.0], start=1.0, end=8.9)
    # Start on value, End in between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=2.0, end=7.9)
    # Start on value, End on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=2.0, end=7.9)
    # Start on value, End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0, 8.0], start=2.0, end=14.3)
    # Start on value, End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0, 8.0], start=2.0, end=14.3)
    # Start between values, End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0, 8.0], start=2.3, end=8.9)
    # Start between values, End on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0, 8.0], start=2.3, end=8.0)
    # Start between values, End between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=2.3, end=7.9)
    # Start in front of first value and End in front of first value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[], start=-14.5, end=0.9)
    # Start after last value and End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[], start=8.1, end=14.5)
    # Exactly one value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[5.0], start=5.0, end=5.0)


@pytest.mark.parametrize("length_for_buffer", [10, 14])
@pytest.mark.parametrize("model_type", [accgraph.CurveDataModel])
def test_subset_creation_of_data_model_with_multiple_nan_values_and_nan_as_last_value(model_type: Type[accgraph.BaseDataModel], length_for_buffer: int):
    """Test subset creation from datamodel that does contain any nan values"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=length_for_buffer)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=1.0, stop=4.0)))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=4.0, stop=6.0)))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=6.0, stop=8.0)))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    # Start in front of first value, End in between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=0.0, end=7.9)
    # Start in front of first value, End exactly on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=0.0, end=7.0)
    # Start in front of first value, End after last values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[1.0, 2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=0.0, end=8.9)
    # Start on value, End in between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0], start=2.0, end=6.9)
    # Start on value, End on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0], start=2.0, end=6.0)
    # Start on value, End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[2.0, 3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=2.0, end=14.3)
    # Start between values, End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=2.3, end=8.9)
    # Start between values, End on value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, np.nan, 4.0, 5.0, np.nan, 6.0, 7.0], start=2.3, end=7.0)
    # Start between values, End between values
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[3.0, np.nan, 4.0, 5.0, np.nan, 6.0], start=2.3, end=6.9)
    # Start in front of first value and End in front of first value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[], start=-14.5, end=0.9)
    # Start after last value and End after last value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[], start=8.1, end=14.5)
    # Exactly one value
    assert dm_util.check_datamodel_subset(data_model=datamodel, buffer_size=length_for_buffer, expected=[5.0], start=5.0, end=5.0)


# ~~~~~ Other datamodel related tests ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~+


@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_smallest_distance_between_primary_values(model_type: Type[accgraph.BaseDataModel]):
    """Test subset creation from datamodel that does contain any nan values"""
    ds: MockDataSource = MockDataSource()
    dm = model_type(data_source=ds, buffer_size=5)
    assert dm.get_smallest_distance_between_x_values() == np.inf
    ds.emit_new_object(dm_util.create_fitting_object(dm, 1.0))
    assert dm.get_smallest_distance_between_x_values() == np.inf
    ds.emit_new_object(dm_util.create_fitting_object(dm, 3.2))
    assert dm.get_smallest_distance_between_x_values() == 3.2 - 1.0
    ds.emit_new_object(dm_util.create_fitting_object(dm, 2.0))
    assert dm.get_smallest_distance_between_x_values() == 2.0 - 1.0
    ds.emit_new_object(dm_util.create_fitting_object(dm, 4.0))
    assert dm.get_smallest_distance_between_x_values() == 4.0 - 3.2


@pytest.mark.parametrize("model_type", datamodels_to_test)
def test_get_highest_primary_value(model_type: Type[accgraph.BaseDataModel]):
    """Test subset creation from datamodel that does contain any nan values"""
    ds: MockDataSource = MockDataSource()
    dm = model_type(data_source=ds, buffer_size=5)
    assert dm.get_highest_primary_value() is None
    ds.emit_new_object(dm_util.create_fitting_object(dm, np.nan))
    assert dm.get_highest_primary_value() is None
    ds.emit_new_object(dm_util.create_fitting_object(dm, 1.0))
    assert dm.get_highest_primary_value() == 1.0
    ds.emit_new_object(dm_util.create_fitting_object(dm, 3.2))
    assert dm.get_highest_primary_value() == 3.2
    ds.emit_new_object(dm_util.create_fitting_object(dm, 2.0))
    assert dm.get_highest_primary_value() == 3.2
    ds.emit_new_object(dm_util.create_fitting_object(dm, 4.0))
    assert dm.get_highest_primary_value() == 4.0
    ds.emit_new_object(dm_util.create_fitting_object(dm, np.nan))
    assert dm.get_highest_primary_value() == 4.0
