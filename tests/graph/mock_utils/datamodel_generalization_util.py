"""
Functions for writing tests for different data-models without writing code specific for them.
This allows running the same tests on different data-models without having to rewrite datamodel
specific code for each model.

A simple example for the usage could look like this:
Example:
    @pytest.mark.parametrize("model_type", [<datamodels you want to test>])
    def test_template(model_type: Type[accs_graph.BaseDataModel]):
        data_source: MockDataSource = MockDataSource()
        datamodel = model_type(data_source=data_source, buffer_size=5)
        data_source.emit_new_object(dm_utils.create_fitting_object(datamodel, 1.0))
        assert dm_utils.check_datamodel(datamodel, [1.0])
        data_source.emit_new_object(dm_utils.create_fitting_object_collection(datamodel, np.arange(start=2.0, stop=4.0)))
        assert dm_utils.check_datamodel(datamodel, [1.0, 2.0, 3.0])
"""

from typing import List, Tuple, Union

import numpy as np

import accsoft_gui_pyqt_widgets.graph as accgraph

# ~~~~~ Creation of values the datamodel can emit ~~~~~~~~~~~~~~~~~~~~~~


def check_datamodel(data_model: accgraph.BaseDataModel, buffer_size: int, primary_values: List[float]):
    """
    Check the content of the datamodels buffer with expected secondary values created
    with the same logic as the for the datasource created objects.
    This allows to write generic check without having to know the actual how
    many and which fields the datamodel saves the datamodel is saving.
    """
    actual: Tuple[np.ndarray, ...] = data_model.get_full_data_buffer()
    return _check_data_model(data_model, buffer_size, actual, primary_values)


def check_datamodel_subset(data_model: accgraph.BaseDataModel, buffer_size: int, expected: List[float], start: float, end: float):
    """
    Check a specific subset of the datamodels buffer with expected secondary values created
    with the same logic as the for the datasource created objects.
    This allows to write generic check without having to know the actual how
    many and which fields the datamodel saves the datamodel is saving.
    """
    actual: Tuple[np.ndarray, ...] = data_model.get_subset(start, end)
    return _check_data_model(data_model, buffer_size, actual, expected)


def _check_data_model(data_model: accgraph.BaseDataModel, buffer_size: int, actual: Tuple[np.ndarray, ...], primary_values: List[float]):
    """Create expected data by the given primary values"""
    if data_model.get_data_buffer_size() != buffer_size:
        return False
    expected: Tuple[np.ndarray, ...]
    if isinstance(data_model, accgraph.CurveDataModel):
        expected = _create_curve_data_model_expected_content(x_values=primary_values)
    elif isinstance(data_model, accgraph.BarGraphDataModel):
        expected = _create_bar_graph_data_model_expected_content(x_values=primary_values)
    elif isinstance(data_model, accgraph.InjectionBarDataModel):
        expected = _create_injection_bar_data_model_expected_content(x_values=primary_values)
    elif isinstance(data_model, accgraph.TimestampMarkerDataModel):
        expected = _create_infinite_line_data_model_expected_content(x_values=primary_values)
    else:
        raise ValueError("Can not handle DataModel of type", data_model.__class__)
    return compare_tuple_of_numpy_arrays(actual, expected)


def compare_tuple_of_numpy_arrays(tuple_1: Tuple[np.ndarray, ...], tuple_2: Tuple[np.ndarray, ...]):
    """Go through two tuples containing numpy arrays and compare them"""
    for array_1, array_2 in zip(list(tuple_1), list(tuple_2)):
        if len(array_1) != len(array_2):
            return False
        if len(array_1) == len(array_2) == 0:
            return True
        if isinstance(array_1[0], str):
            for e_1, e_2 in zip(array_1, array_2):
                if e_1 != e_2:
                    return False
        if isinstance(array_1[0], float) and not np.allclose(array_1, array_2, equal_nan=True):
            return False
    return True


def get_fitting_color(x_value: float) -> str:
    """return a char representing a color by an given x value"""
    if np.isnan(x_value):
        return "nan"
    colors = [
        "b",
        "g",
        "r",
        "c",
        "m",
        "k",
        "w"
    ]
    return colors[int(x_value) % (len(colors) - 1)]


def create_fitting_object(data_model: accgraph.BaseDataModel, x_value: float):
    """Create an object fitting to the specified data model"""
    if isinstance(data_model, accgraph.CurveDataModel):
        return _create_point_data(value=x_value)
    elif isinstance(data_model, accgraph.BarGraphDataModel):
        return _create_bar_data(value=x_value)
    elif isinstance(data_model, accgraph.InjectionBarDataModel):
        return _create_injection_bar_data(value=x_value)
    elif isinstance(data_model, accgraph.TimestampMarkerDataModel):
        return _create_infinite_line(
            value=x_value,
            color=get_fitting_color(x_value)
        )


def create_fitting_object_collection(data_model: accgraph.BaseDataModel, x_values: Union[List[float], np.ndarray]):
    """Create an object fitting to the specified data model"""
    if not isinstance(x_values, np.ndarray):
        x_values = np.array(x_values)
    if isinstance(data_model, accgraph.CurveDataModel):
        return _create_curve_data(values=x_values)
    elif isinstance(data_model, accgraph.BarGraphDataModel):
        return _create_bar_data_collection(values=x_values)
    elif isinstance(data_model, accgraph.InjectionBarDataModel):
        return _create_injection_bar_data_collection(values=x_values)
    elif isinstance(data_model, accgraph.TimestampMarkerDataModel):
        return _create_infinite_line_collection(
            values=x_values,
            colors=np.array([get_fitting_color(x_value) for x_value in x_values])
        )


def _create_point_data(value: float) -> accgraph.PointData:
    """Create PointData"""
    return accgraph.PointData(
        x_value=value,
        y_value=value + 0.1
    )


def _create_curve_data(values: np.ndarray) -> accgraph.CurveData:
    """Create PointData"""
    return accgraph.CurveData(
        x_values=values,
        y_values=values + 0.1
    )


def _create_curve_data_model_expected_content(x_values: List[float]) -> Tuple[np.ndarray, ...]:
    return (
        np.array(x_values),  # x_values
        np.array([x_value + 0.1 for x_value in x_values]),  # y_values
    )


def _create_bar_data(value: float) -> accgraph.BarData:
    """Create BarData, To save some lines of code"""
    return accgraph.BarData(
        x_value=value,
        y_value=value + 0.1,
        height=value + 0.2,
    )


def _create_bar_data_collection(values: np.ndarray) -> accgraph.BarCollectionData:
    """Create BarData, To save some lines of code"""
    return accgraph.BarCollectionData(
        x_values=values,
        y_values=values + 0.1,
        heights=values + 0.2,
    )


def _create_bar_graph_data_model_expected_content(x_values: List[float]) -> Tuple[np.ndarray, ...]:
    return (
        np.array(x_values),  # x_values
        np.array([x_value + 0.1 for x_value in x_values]),  # y_values
        np.array([x_value + 0.2 for x_value in x_values]),  # height
    )


def _create_injection_bar_data(value: float) -> accgraph.InjectionBarData:
    """Create InjectionBarData, To save some lines of code"""
    return accgraph.InjectionBarData(
        x_value=value,
        y_value=value + 0.1,
        height=value + 0.2,
        width=value + 0.3,
        label=str(value + 0.4),
    )


def _create_injection_bar_data_collection(values: np.ndarray) -> accgraph.InjectionBarCollectionData:
    """Create InjectionBarData, To save some lines of code"""
    return accgraph.InjectionBarCollectionData(
        x_values=values,
        y_values=values + 0.1,
        heights=values + 0.2,
        widths=values + 0.3,
        labels=np.array([str(value + 0.4) for value in values]),
    )


def _create_injection_bar_data_model_expected_content(x_values: List[float]) -> Tuple[np.ndarray, ...]:
    return (
        np.array(x_values),  # x_values
        np.array([x_value + 0.1 for x_value in x_values]),  # y_values
        np.array([((x_value + 0.2) if not np.isnan(x_value) else 0.0) for x_value in x_values]),  # height
        np.array([((x_value + 0.3) if not np.isnan(x_value) else 0.0) for x_value in x_values]),  # width
        np.array([str(x_value + 0.4) for x_value in x_values], dtype="<U100"),  # label
    )


def _create_infinite_line(value: float, color: str) -> accgraph.TimestampMarkerData:
    """Create Timestamp Marker Data, To save some lines of code"""
    return accgraph.TimestampMarkerData(
        x_value=value,
        color=color,
        label=str(value + 0.1),
    )


def _create_infinite_line_collection(values: np.ndarray, colors: np.ndarray) -> accgraph.TimestampMarkerCollectionData:
    """Create Timestamp Marker Data, To save some lines of code"""
    return accgraph.TimestampMarkerCollectionData(
        x_values=values,
        colors=colors,
        labels=np.array([str(value + 0.1) for value in values]),
    )


def _create_infinite_line_data_model_expected_content(x_values: List[float]) -> Tuple[np.ndarray, ...]:
    return (
        np.array(x_values),  # x_values
        np.array([get_fitting_color(x_value) for x_value in x_values]),  # color
        np.array([str(x_value + 0.1) for x_value in x_values], dtype="<U100"),  # label
    )
