"""Update Source for Data for Testing purposes"""

from typing import List, Union, Type, Any

from accwidgets import graph as accgraph


class MockDataSource(accgraph.UpdateSource):
    """Data Source for Testing purposes

    Class for sending the right signals to the ExtendedPlotWidget. This
    allows precise control over updates that are sent to the widget compared to
    timer based solutions.
    """

    def create_new_value(self, timestamp: float, value: Union[float, List[float]], type_to_emit: Type = accgraph.PointData) -> None:
        """Manually emit a signal with a given new value.

        Args:
            timestamp: timestamp to emit
            value: value to emit
            type_to_emit: Type of the data that is supposed to be emitted
        """
        if type_to_emit == accgraph.PointData and isinstance(value, float):
            new_data = accgraph.PointData(x_value=timestamp, y_value=value)
            self.sig_new_data[accgraph.PointData].emit(new_data)
        elif type_to_emit == accgraph.BarData and isinstance(value, List):
            new_data = accgraph.BarData(x_value=timestamp, y_value=value[0], height=value[1])
            self.sig_new_data[accgraph.BarData].emit(new_data)

    def emit_new_object(
            self,
            object_to_emit: Any):
        """Emit already created object with the """
        self.sig_new_data[type(object_to_emit)].emit(object_to_emit)
