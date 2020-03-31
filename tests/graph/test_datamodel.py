"""Tests for the datamodel

Test for appending data to different datamodels, all tests are executed with
different datamodels. The right values for each datamodel are created with
the functions in datamodel_generalization_util.py
"""

from typing import Type, Optional

import numpy as np
import pytest
from unittest.mock import patch

from accwidgets import graph as accgraph

from .mock_utils import datamodel_generalization_util as dm_util
from .mock_utils.mock_data_source import MockDataSource

DATAMODELS_TO_TEST = [
    accgraph.LiveCurveDataModel,
    accgraph.LiveBarGraphDataModel,
    accgraph.LiveInjectionBarDataModel,
    accgraph.LiveTimestampMarkerDataModel,
]

# For matching warning messages we capture
_INVALID_DATA_STRUCTURE_WARNING_MSG = r"is not valid and can't be drawn for " \
                                      r"the following reasons:"

# ~~~~~ Simple ordering for different datamodels ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("model_type", DATAMODELS_TO_TEST)
def test_datamodel_is_empty(model_type: Type[accgraph.AbstractLiveDataModel]):
    """ Check if datamodel is empty is correct """
    data_source: MockDataSource = MockDataSource()
    datamodel: accgraph.LiveBarGraphDataModel = model_type(data_source=data_source, buffer_size=5)
    assert datamodel.is_empty
    data_source.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert not datamodel.is_empty
    data_source.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [2.0, 3.0, 4.0, 5.0]))
    assert not datamodel.is_empty
    data_source.emit_new_object(dm_util.create_fitting_object(datamodel, 6.0))
    assert not datamodel.is_empty


@pytest.mark.parametrize("model_type", DATAMODELS_TO_TEST)
def test_data_source_replacement(model_type: Type[accgraph.AbstractLiveDataModel]):
    """Check replacement of data source with and without buffer clearing"""
    data_source_1: MockDataSource = MockDataSource()
    data_source_2: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    assert datamodel.data_source is data_source_1
    assert datamodel.is_empty
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert not datamodel.is_empty
    assert dm_util.check_datamodel(datamodel, 5, [1.0])
    datamodel.replace_data_source(data_source_2, clear_buffer=False)
    assert datamodel.data_source is data_source_2
    assert not datamodel.is_empty
    assert dm_util.check_datamodel(datamodel, 5, [1.0])
    datamodel.replace_data_source(data_source_1, clear_buffer=True)
    assert datamodel.data_source is data_source_1
    assert datamodel.is_empty
    assert dm_util.check_datamodel(datamodel, 5, [])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert not datamodel.is_empty


# ~~~~~ Databuffer tests ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@pytest.mark.parametrize("model_type", DATAMODELS_TO_TEST)
def test_append_long_list_of_simple_values(model_type: Type[accgraph.AbstractLiveDataModel]):
    """Append a long list of simple values"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=0.0, stop=101.0)))
    assert dm_util.check_datamodel(datamodel, 5, [98.0, 99.0, 100.0])


@pytest.mark.parametrize("model_type", DATAMODELS_TO_TEST)
def test_append_list_of_points_longer_than_size_into_non_empty_buffer(model_type: Type[accgraph.AbstractLiveDataModel]):
    """Append a long list that is longer than the buffers overall size"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=5.0, stop=10.0)))
    assert dm_util.check_datamodel(datamodel, 5, [5.0, 6.0, 7.0, 8.0, 9.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=10.0, stop=101.0)))
    assert dm_util.check_datamodel(datamodel, 5, [98.0, 99.0, 100.0])


@pytest.mark.parametrize("model_type", DATAMODELS_TO_TEST)
def test_append_list_of_points_longer_than_size_into_half_filled_buffer(model_type: Type[accgraph.AbstractLiveDataModel]):
    """Append a long list that is longer than the buffers overall size while the buffer is already filled to a part"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=7.0, stop=10.0)))
    assert dm_util.check_datamodel(datamodel, 5, [7.0, 8.0, 9.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, np.arange(start=10.0, stop=101.0)))
    assert dm_util.check_datamodel(datamodel, 5, [98.0, 99.0, 100.0])


@pytest.mark.parametrize("model_type", [accgraph.LiveCurveDataModel])
def test_append_nan_point_for_line_splitting(model_type: Type[accgraph.AbstractLiveDataModel]):
    """Append a nan value to represent a split in a line"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    assert dm_util.check_datamodel(datamodel, 5, [1.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    assert dm_util.check_datamodel(datamodel, 5, [1.0, np.nan])
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 2.0))
    assert dm_util.check_datamodel(datamodel, 5, [1.0, np.nan, 2.0])


@pytest.mark.parametrize("model_type", [accgraph.LiveCurveDataModel])
def test_sort_values_around_nan_value(model_type: Type[accgraph.AbstractLiveDataModel]):
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


@pytest.mark.parametrize("model_type", [accgraph.LiveCurveDataModel])
def test_append_nan_on_first_position(model_type: Type[accgraph.AbstractLiveDataModel]):
    """First value appended to the DataModel is NaN"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, np.nan))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 1.0))
    data_source_1.emit_new_object(dm_util.create_fitting_object(datamodel, 2.0))
    assert dm_util.check_datamodel(datamodel, 5, [np.nan, 1.0, 2.0])


@pytest.mark.parametrize("model_type", [accgraph.LiveCurveDataModel])
def test_nan_get_first_value_after_shift(model_type: Type[accgraph.AbstractLiveDataModel]):
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


@pytest.mark.parametrize("model_type", [accgraph.LiveCurveDataModel])
def test_append_list_containing_nan(model_type: Type[accgraph.AbstractLiveDataModel]):
    """Append a list with values that contain a nan"""
    data_source_1: MockDataSource = MockDataSource()
    datamodel = model_type(data_source=data_source_1, buffer_size=5)
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [2.0, 3.0, 4.0]))
    assert dm_util.check_datamodel(datamodel, 5, [2.0, 3.0, 4.0])
    data_source_1.emit_new_object(dm_util.create_fitting_object_collection(datamodel, [3.75, np.nan]))
    assert dm_util.check_datamodel(datamodel, 5, [2.0, 3.0, 3.75, 4.0, np.nan])


# ~~~~~ Data Model Subset tesing without clipping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@pytest.mark.parametrize("length_for_buffer", [10, 14])
@pytest.mark.parametrize("model_type", DATAMODELS_TO_TEST)
def test_subset_creation_of_data_model_without_nan_values(model_type: Type[accgraph.AbstractLiveDataModel], length_for_buffer: int):
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
@pytest.mark.parametrize("model_type", [accgraph.LiveCurveDataModel])
def test_subset_creation_of_data_model_with_multiple_nan_values(model_type: Type[accgraph.AbstractLiveDataModel], length_for_buffer: int):
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
@pytest.mark.parametrize("model_type", [accgraph.LiveCurveDataModel])
def test_subset_creation_of_data_model_with_multiple_nan_values_and_nan_as_last_value(model_type: Type[accgraph.AbstractLiveDataModel], length_for_buffer: int):
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


@pytest.mark.parametrize("model_type", DATAMODELS_TO_TEST)
def test_smallest_distance_between_primary_values(model_type: Type[accgraph.AbstractLiveDataModel]):
    """Test subset creation from datamodel that does contain any nan values"""
    data_source: MockDataSource = MockDataSource()
    data_model = model_type(data_source=data_source, buffer_size=5)
    assert data_model.min_dx == np.inf
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 1.0))
    assert data_model.min_dx == np.inf
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 3.2))
    assert data_model.min_dx == 3.2 - 1.0
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 2.0))
    assert data_model.min_dx == 2.0 - 1.0
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 4.0))
    assert data_model.min_dx == 4.0 - 3.2


@pytest.mark.parametrize("model_type, nan_warning", [
    (accgraph.LiveCurveDataModel, None),
    (accgraph.LiveBarGraphDataModel, accgraph.InvalidDataStructureWarning),
    (accgraph.LiveInjectionBarDataModel, accgraph.InvalidDataStructureWarning),
    (accgraph.LiveTimestampMarkerDataModel, accgraph.InvalidDataStructureWarning),
])
def test_get_highest_primary_value(model_type: Type[accgraph.AbstractLiveDataModel],
                                   nan_warning: Optional[Type[UserWarning]]):
    """Test subset creation from datamodel that does contain any nan values"""
    data_source: MockDataSource = MockDataSource()
    data_model = model_type(data_source=data_source, buffer_size=5)
    assert data_model.max_primary_val is None
    if nan_warning is not None:
        with pytest.warns(nan_warning, match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
            data_source.emit_new_object(dm_util.create_fitting_object(data_model, np.nan))
    else:
        data_source.emit_new_object(dm_util.create_fitting_object(data_model, np.nan))
    assert data_model.max_primary_val is None
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 1.0))
    assert data_model.max_primary_val == 1.0
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 3.2))
    assert data_model.max_primary_val == 3.2
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 2.0))
    assert data_model.max_primary_val == 3.2
    data_source.emit_new_object(dm_util.create_fitting_object(data_model, 4.0))
    assert data_model.max_primary_val == 4.0
    if nan_warning is not None:
        with pytest.warns(nan_warning, match=_INVALID_DATA_STRUCTURE_WARNING_MSG):
            data_source.emit_new_object(dm_util.create_fitting_object(data_model, np.nan))
    else:
        data_source.emit_new_object(dm_util.create_fitting_object(data_model, np.nan))
    assert data_model.max_primary_val == 4.0


# ~~~~~~~~~~~~ Test data model when editing ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@patch.object(accgraph.UpdateSource, "handle_data_model_edit")
def test_editable_curve_datamodel_notifying(mock_handler):
    """Tests, that editing is properly propagated to the update source"""
    data_source = accgraph.UpdateSource()
    data_model = accgraph.EditableCurveDataModel(data_source=data_source)
    # Initial update from the update source
    source_data = accgraph.CurveData(x=[0, 1, 2, 3, 4],
                                     y=[0, 1, 2, 3, 4])
    data_source.send_data(source_data)
    data_source.handle_data_model_edit.assert_not_called()
    # Another update from the source
    source_data = accgraph.CurveData(x=[0, 1, 2, 3, 4],
                                     y=[0, 1, 2, 1, 0])
    data_source.send_data(source_data)
    data_source.handle_data_model_edit.assert_not_called()
    edited_data = accgraph.CurveData(x=[0, 1, 2, 3, 4],
                                     y=[4, 3, 2, 1, 0])
    data_model.handle_editing(edited_data)
    mock_handler.assert_not_called()
    data_model.send_current_state()
    mock_handler.assert_called_with(edited_data)


def test_editable_curve_datamodel():
    """Tests, that editing is properly propagated to the update source"""
    def to_curve_data(array):
        return accgraph.CurveData(array[0], array[1])
    data_source = accgraph.UpdateSource()
    data_model = accgraph.EditableCurveDataModel(data_source=data_source)
    # Initial update from the update source
    source_data = accgraph.CurveData(x=[0, 1, 2, 3, 4],
                                     y=[0, 1, 2, 3, 4])
    data_source.send_data(source_data)
    assert to_curve_data(data_model.full_data_buffer) == source_data
    # Another update from the source
    source_data = accgraph.CurveData(x=[0, 1, 2, 3, 4],
                                     y=[0, 1, 2, 1, 0])
    data_source.send_data(source_data)
    assert to_curve_data(data_model.full_data_buffer) == source_data
    edited_data = accgraph.CurveData(x=[0, 1, 2, 3, 4],
                                     y=[4, 3, 2, 1, 0])
    data_model.handle_editing(edited_data)
    assert to_curve_data(data_model.full_data_buffer) == edited_data


@pytest.mark.parametrize("original, selected_indices, replacement, result", [
    # All empty
    ([[], []], [], [[], []], [[], []]),
    # Change nothing
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [], [[], []], [[0, 1, 2, 3], [2, 1, 0, 3]]),
    # Change with same data
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [1, 2], [[1, 2], [1, 0]], [[0, 1, 2, 3], [2, 1, 0, 3]]),
    # Change with data with different y with same amount
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [1, 2], [[1, 2], [24, 25]], [[0, 1, 2, 3], [2, 24, 25, 3]]),
    # Change with data with different x with same amount
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [1, 2], [[-2, -1], [1, 0]], [[-2, -1, 0, 3], [1, 0, 2, 3]]),
    # Change with data with different x & y with same amount
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [1, 2], [[-2, -1], [24, 25]], [[-2, -1, 0, 3], [24, 25, 2, 3]]),
    # Change with data with different x & y with smaller amount
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [1, 2], [[-1], [25]], [[-1, 0, 3], [25, 2, 3]]),
    # Change with data with different x & y with larger amount
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [1, 2], [[-1, 1.5, 4], [21, 22, 23]], [[-1, 0, 1.5, 3, 4], [21, 2, 22, 3, 23]]),
    # Add points
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [], [[-1, 1.5, 5], [-2, 1.75, 6]], [[-1, 0, 1, 1.5, 2, 3, 5], [-2, 2, 1, 1.75, 0, 3, 6]]),
    # Delete points
    ([[0, 1, 2, 3], [2, 1, 0, 3]], [0, 2], [[], []], [[1, 3], [1, 3]]),
])
def test_replace_selection_in_editable_data_model(original,
                                                  selected_indices,
                                                  replacement,
                                                  result):
    """
    When applying functions to a selection, the selection will be replaced
    with the return value of the function.
    """
    def to_curve_data(array):
        return accgraph.CurveData(array[0], array[1])
    data_source = accgraph.UpdateSource()
    data_model = accgraph.EditableCurveDataModel(data_source=data_source)

    original_cd = to_curve_data(original)
    replacement_cd = to_curve_data(replacement)
    result_cd = to_curve_data(result)

    data_source.send_data(original_cd)
    assert to_curve_data(data_model.full_data_buffer) == original_cd
    data_model.replace_selection(selected_indices, replacement_cd)
    assert to_curve_data(data_model.full_data_buffer) == result_cd


@pytest.mark.parametrize("ops, undoable, redoable", [
    ([], False, False),  # Start

    ([[0, 1],  # Select
      accgraph.CurveData([0, 1], [4, 3])],  # Replace
     True, False),

    ([accgraph.CurveData([-2, -1], [4, 3])],  # Add Points
     True, False),

    ([[0, 1],  # Select
      accgraph.CurveData([], [])],  # Delete
     True, False),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      "UNDO"],
     False, True),


    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      accgraph.CurveData([0, 1], [2, 3]),
      "UNDO"],
     True, True),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      [1, 2],
      accgraph.CurveData([1, 2], [2, 3])],
     True, False),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      [1, 2],
      accgraph.CurveData([1, 2], [2, 3]),
      "UNDO"],
     True, True),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      [1, 2],
      accgraph.CurveData([1, 2], [2, 3]),
      "UNDO",
      "UNDO"],
     False, True),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      accgraph.CurveData([0, 1], [2, 3]),
      "UNDO",
      "UNDO"],
     False, True),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      accgraph.CurveData([0, 1], [2, 3]),
      "UNDO",
      "UNDO",
      "REDO"],
     True, True),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      "UNDO",
      "REDO"],
     True, False),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      "UNDO",
      "REDO",
      "UNDO"],
     False, True),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      "UNDO",
      accgraph.CurveData([0, 1], [3, 2])],
     True, False),

    ([[0, 1],
      accgraph.CurveData([0, 1], [2, 3]),
      "SEND"],
     True, False),

    ([[0, 1],
      accgraph.CurveData([0, 1], [2, 3]),
      "UNDO",
      "REDO",
      "SEND"],
     True, False),

    ([[0, 1],
      accgraph.CurveData([0, 1], [2, 3]),
      accgraph.CurveData([0, 1], [4, 3]),
      "SEND"],
     True, False),

    ([[0, 1],
      accgraph.CurveData([0, 1], [4, 3]),
      "UNDO",
      accgraph.CurveData([0, 1], [3, 2]),
      "SEND"],
     True, False),
])
def test_data_model_undoable_redoable(ops, undoable, redoable):
    """Test if undo /redo can be called on the data model after a sequence
    of passed operations"""
    source = accgraph.UpdateSource()
    model = accgraph.EditableCurveDataModel(data_source=source)
    source.send_data(accgraph.CurveData([0, 1, 2, 3, 4], [3, 2, 1, 2, 3]))
    current_selection = []
    for op in ops:
        if isinstance(op, list):
            current_selection = op
        elif isinstance(op, accgraph.CurveData):
            model.replace_selection(current_selection, op)
        elif isinstance(op, str):
            if op == "UNDO":
                model.undo()
            elif op == "REDO":
                model.redo()
            elif op == "SEND":
                model.send_current_state()
            else:
                raise ValueError(f'Unknown operation "{op}" in test')
        else:
            raise ValueError(f'Unknown operation "{op}" in test')
    # The current state should always be sendable
    assert model.sendable_state_exists
    assert model.undoable == undoable
    assert model.redoable == redoable
