"""
Base class for modified PlotItems that handle data displaying in the ExtendedPlotWidget
"""

from datetime import datetime
from typing import List, Dict
import logging
from pyqtgraph import PlotItem, mkPen, PlotDataItem
from .plotitem_utils import PlotItemUtils, ExtendedPlotWidgetConfig
from .extended_axisitems import RelativeTimeAxisItem
from ..connection.connection import UpdateSource

logging.basicConfig(level=logging.WARNING)
_LOGGER = logging.getLogger(__name__)

_MAX_BUFFER_SIZE = 1000000


class ExtendedPlotItem(PlotItem):
    """Superclass for different style PlotItems

    Definition of a common interface for all extended PlotItems. Common
    functionality can be defined here and implemented in the subclasses. Shared
    functions can be handled here.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, timing_source: UpdateSource, data_source: UpdateSource, config: ExtendedPlotWidgetConfig, **kwargs):
        """Constructor

        Args:
            timing_source (UpdateSource): Source for timing updates
            data_source (UpdateSource): Source for data updates
            config (ExtendedPlotWidgetConfig): Configuration of the plotting
                decorators
            **kwargs: Keyword Arguments that will be passed to PlotItem
        """
        super().__init__(**kwargs)
        self._time_progress_line = config.time_progress_line
        self._v_draw_line = config.v_draw_line
        self._h_draw_line = config.h_draw_line
        self._draw_point = config.draw_point
        self._cycle_size = config.cycle_size
        self._last_timestamp: float = -1.0
        self._time_line = None
        self._plotting_line_v = None
        self._plotting_line_h = None
        self._plotting_line_point = None
        # Get timing updates from the Timing System, do not use local time for any time based actions!
        timing_source.timing_signal.connect(self._handle_timing_update)
        data_source.data_signal.connect(lambda dict_: self.plot_append(dict_["x"], dict_["y"]))

    def plot_append(self, x_pos, y_pos) -> None:
        """Append a new point

        Append a point with given X and Y value to the current graph. The
        actual functionality has to be implemented in each subclass.

        Args:
            x_pos: X position of the point
            y_pos: Y position of the point
        """

    def _draw_time_line_decorator(self, timestamp: float, position: float):
        """Draw a vertical line representing the current time

        Redraw the timing line according to a passed timestamp. Alternatively
        the line can also be drawn at a custom position by providing the
        position parameter, if the position is different from the provided
        timestamp (f.e. through offsets)

        Args:
            timestamp (float): Timestamp that should be displayed at the line
            position (float): Timestamp where the line should be drawn, if None
                -> position = timestamp
        """
        if self._time_line:
            if position is None:
                position = timestamp
            self._time_line.setValue(position)
            if hasattr(self._time_line, 'label'):
                self._time_line.label.setText(datetime.fromtimestamp(timestamp).strftime("%H:%M:%S"))

    def _draw_plotting_position_decorators(self, x_pos, y_pos) -> None:
        """Draw all decorator at the given position, if they have been created.

        Args:
            x_pos: X-Postion to move the decorators to
            y_pos: Y-Postion to move the decorators to
        """
        if self._plotting_line_v is not None:
            self._plotting_line_v.setValue(x_pos)
        if self._plotting_line_h is not None:
            self._plotting_line_h.setValue(y_pos)
        if self._plotting_line_point is not None:
            self._plotting_line_point.setData({"x": [x_pos], "y": [y_pos]})

    # Abstract
    def _handle_timing_update(self, timestamp: float) -> None:
        """Handle an update provided by the timing source.

        Handle initial drawing of decorators, redrawing of actual curves have
        to be implemented in the specific subclass.

        Args:
            timestamp (float): Updated timestamp provided by the timing source
        """
        if self._last_timestamp == -1:
            label_opts = {"movable": True, "position": 0.96}
            if self._time_progress_line:

                self._time_line = self.addLine(timestamp, pen=(mkPen(80, 80, 80)),
                                               label=datetime.fromtimestamp(timestamp).strftime("%H:%M:%S"),
                                               labelOpts=label_opts)
            else:
                self._time_line = self.addLine(timestamp, pen=(mkPen(80, 80, 80, 0)))
            self._plotting_line_v = self.addLine(x=timestamp) if self._v_draw_line else None
            self._plotting_line_h = self.addLine(y=0) if self._h_draw_line else None
            self._plotting_line_point = self.plot([timestamp], [0], symbol="o") if self._draw_point else None
        self._last_timestamp = timestamp

    def get_last_time_stamp(self):
        """Get the last timestamp that was emitted by the according data
        source
        """
        return self._last_timestamp


class SlidingPointerPlotItem(ExtendedPlotItem):
    """PlotItem for the Sliding Pointer Plotting Style

    Displays data as a sliding pointer widget similar to a heart rate
    monitor. The graph itself stays fixed in position and has a fixed length
    that it does not exceed. As soon as the drawing reaches the end, the graph
    gets redrawn beginning at the start. The old curve gets incrementally
    overwritten by the new values. The x-values of all lines in the graph will
    be shifted backwards according to the cycle length (like x % cycle_length)
    so the area with the visual change does not move.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, **kwargs):
        """Constructor

        Create a new SlidingPointerPlotItem.n :param cycle_size: . :param
        kwargs:

        Args:
            cycle_size (int): The cycle length in ms
            **kwargs: Keyword Arguments passed to Superclass
        """
        super().__init__(**kwargs)
        # x values not needed here
        self._full_curve_buffer: Dict[str, List[float]] = {
            "timestamps": [],
            "y": [],
        }
        self._full_curve_old: Dict[str, List[float]] = {
            "timestamps": [],
            "x": [],
            "y": [],
        }
        self._old_curve_data_item: PlotDataItem = self.plot(pen=mkPen(80, 80, 80))
        self._full_curve_new: Dict[str, List[float]] = {
            "timestamps": [],
            "x": [],
            "y": [],
        }
        # Save data passed to PlotDataItems for testing purposes
        self._data_items_data: Dict[str, List[float]] = {
            "old_curve_x": [],
            "old_curve_y": [],
            "new_curve_x": [],
            "new_curve_y": [],
        }
        self._new_curve_data_item: PlotDataItem = self.plot(pen=mkPen(255, 255, 255))
        # Get Cycle start, end etc. on first time update
        self._first_time_update = True
        self._cycle_number: float = 0.0
        self._cycle_start: float = 0.0
        self._cycle_end: float = 0.0

    # Handle Data Source Update

    def plot_append(self, x_pos, y_pos) -> None:
        """Handle addition of a new point

        A new plot is always appended to the full curve buffer dict, not to
        the new and old curve dicts. They are subsets of the full curve buffer
        and will be modified by updates from the Timing Source according to the
        current time.

        If the new point appended is not in the right order (point has lower
        time-stamp than one that is already in the full curve buffer), they will
        be added at the right position according to their timestamp. This forces
        the full curve buffer to always stay ordered no matter what order points
        are appended in.

        Args:
            x_pos: timestamp of the new point
            y_pos: value of the new point
        """
        statement = f"Number Points in new Curve X : {len(self._full_curve_new['x'])}"
        statement += f"Number Points in new Curve Y : {len(self._full_curve_new['y'])}"
        statement += f"Cycle Number:                  {self._cycle_number}"
        _LOGGER.debug(statement)
        if not self._full_curve_buffer["timestamps"] or x_pos > self._full_curve_buffer["timestamps"][-1]:
            self._full_curve_buffer["timestamps"].append(x_pos)
            self._full_curve_buffer["y"].append(y_pos)
        else:
            index = -1
            stop = -1 * len(self._full_curve_buffer["timestamps"])
            while x_pos < self._full_curve_buffer["timestamps"][index] and index > stop:
                index -= 1
            self._full_curve_buffer["timestamps"].insert(index + 1, x_pos)
            self._full_curve_buffer["y"].insert(index + 1, y_pos)
        # Update with current timestamp but with new data
        if self._last_timestamp != -1:
            self._handle_timing_update(self._last_timestamp)

    # Handle Timing Source Update

    def _handle_timing_update(self, timestamp: float) -> None:
        """Handle a new timestamp

        Handle a update in the current time triggered by the timing source
        With the new timestamp the data subset for the new and old curve are
        updated clipped and drawn. If the timestamp is older than the current
        known one, it will be ignored and interpreted as delivered as too late

        Args:
            timestamp (float): The new published timestamp
        """
        if timestamp >= self._last_timestamp:
            super()._handle_timing_update(timestamp)
            self._handle_initial_time_update()
            old_cycle_number = self._cycle_number
            self._cycle_number = (timestamp - self._cycle_start) // self._cycle_size
            if old_cycle_number < self._cycle_number:
                self._handle_new_cycle()
            # Points located at cycle start would otherwise also be added to cycle number "-1"
            if self._cycle_number > 0:
                self._update_old_curve_data()
            self._update_new_curve_data()
            self._connect_old_to_new_curve()
            self._update_new_curve_data_item()
            self._update_old_curve_data_item()
            position = self._cycle_start + ((timestamp - self._cycle_start) % self._cycle_size)
            self._draw_time_line_decorator(timestamp=timestamp, position=position)
            x_pos = self._full_curve_new["x"][-1] if self._full_curve_new["x"] else self._cycle_start
            y_pos = self._full_curve_new["y"][-1] if self._full_curve_new["y"] else 0
            self._draw_plotting_position_decorators(x_pos, y_pos)

    # New and Old Curve Subsample Functions

    def _handle_initial_time_update(self) -> None:
        """Handle the first ever timing update received from the timing source

        As soon as the first timestamp is available, cycle information like
        start and end can be set and according decorators are added.
        """
        if self._first_time_update:
            self._cycle_start = self._get_current_time_line_x_pos()
            self._cycle_end = self._cycle_start + self._cycle_size * (self._cycle_number + 1)
            # boundaries at cycle start and end
            self.addLine(x=self._cycle_start, pen=mkPen(128, 128, 128))
            self.addLine(x=self._cycle_end, pen=mkPen(128, 128, 128))
            self._first_time_update = False
            axis = self.getAxis("bottom")
            if isinstance(axis, RelativeTimeAxisItem):
                axis.set_start_time(self._cycle_start)

    def _handle_new_cycle(self):
        """Cut buffer if new cycle starts if necessary"""
        if len(self._full_curve_buffer["timestamps"]) > _MAX_BUFFER_SIZE:
            self._full_curve_buffer["timestamps"] = self._full_curve_buffer["timestamps"][_MAX_BUFFER_SIZE // 2:]
            self._full_curve_buffer["y"] = self._full_curve_buffer["y"][_MAX_BUFFER_SIZE // 2:]

    def _update_old_curve_data(self) -> None:
        """Update the displayed old curve

        Find all points in the full curve buffer that are located in the
        previous cycle
        """
        prev_cycle_start = self._get_previous_cycle_start_timestamp()
        prev_cycle_end = self._get_previous_cycle_end_timestamp()
        start = PlotItemUtils.bin_search_surrounding_points(
            self._full_curve_buffer["timestamps"], prev_cycle_start)["after"]
        end = PlotItemUtils.bin_search_surrounding_points(
            self._full_curve_buffer["timestamps"], prev_cycle_end)["before"]
        if start != -1 and end != -1:
            self._full_curve_old["timestamps"] = self._full_curve_buffer["timestamps"][start:end + 1]
            self._full_curve_old["x"] = [x - self._get_previous_cycle_offset() for x in
                                         self._full_curve_buffer["timestamps"][start:end + 1]]
            self._full_curve_old["y"] = self._full_curve_buffer["y"][start:end + 1]
        else:
            # No points old enough for an old curve yet
            self._full_curve_old["timestamps"] = []
            self._full_curve_old["x"] = []
            self._full_curve_old["y"] = []

    def _connect_old_to_new_curve(self) -> None:
        """Draw connection between old and new curve through the boundaries

        Connect the last point of the old curve and the first point of the
        new curve. For this, a point will be calculated, that represents the
        intersection between these two points and the cycle-boundaries. This
        intersection is then appended at the beginning at the end to draw a
        continuing line though the cycle boundaries.
        """
        if self._full_curve_old["timestamps"] and self._full_curve_new["timestamps"]:
            point_to_connect_from = {
                "x": self._full_curve_old["timestamps"][-1],
                "y": self._full_curve_old["y"][-1],
            }
            point_to_connect_to = {
                "x": self._full_curve_new["timestamps"][0],
                "y": self._full_curve_new["y"][0],
            }
            cycle_end = self._get_previous_cycle_end_timestamp()
            point = PlotItemUtils.calc_intersection(point_to_connect_from, point_to_connect_to, cycle_end)
            if point:
                # Don"t add duplicates if intersection is already point in curve
                if not self._full_curve_old["timestamps"] or point_to_connect_from != point:
                    self._full_curve_old["timestamps"].append(point["x"])
                    self._full_curve_old["x"].append(self._cycle_end)
                    self._full_curve_old["y"].append(point["y"])
                if not self._full_curve_new["timestamps"] or point_to_connect_to != point:
                    self._full_curve_new["timestamps"] = [point["x"]] + self._full_curve_new["timestamps"]
                    self._full_curve_new["x"] = [self._cycle_start] + self._full_curve_new["x"]
                    self._full_curve_new["y"] = [point["y"]] + self._full_curve_new["y"]

    def _update_new_curve_data(self) -> None:
        """Find points belonging to the current cycle"""
        cur_cycle_start = self._get_current_cycle_start_timestamp()
        cur_cycle_end = self._get_current_cycle_end_timestamp()
        start = PlotItemUtils.bin_search_surrounding_points(
            self._full_curve_buffer["timestamps"], cur_cycle_start)["after"]
        end = PlotItemUtils.bin_search_surrounding_points(
            self._full_curve_buffer["timestamps"], cur_cycle_end)["before"]
        if start != -1 and end != -1:
            self._full_curve_new["timestamps"] = self._full_curve_buffer["timestamps"][start:end + 1]
            self._full_curve_new["x"] = [x - self._get_current_cycle_offset() for x in
                                         self._full_curve_buffer["timestamps"][start:end + 1]]
            self._full_curve_new["y"] = self._full_curve_buffer["y"][start:end + 1]
        else:
            # No points old enough for an old curve yet
            self._full_curve_new["timestamps"] = []
            self._full_curve_new["x"] = []
            self._full_curve_new["y"] = []

    def _update_new_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        i = PlotItemUtils.intersect(self._full_curve_new, self._get_current_time_line_x_pos())
        new_curve_x = self._full_curve_new["x"][:i["last_before_index"] + 1]
        new_curve_y = self._full_curve_new["y"][:i["last_before_index"] + 1]
        if i["intersection"] and i["intersection"]["x"] != new_curve_x[-1]\
                and i["intersection"]["y"] != new_curve_y[-1]:
            new_curve_x += [i["intersection"]["x"]]
            new_curve_y += [i["intersection"]["y"]]
        self._data_items_data["new_curve_x"] = new_curve_x
        self._data_items_data["new_curve_y"] = new_curve_y
        self._new_curve_data_item.setData({"x": new_curve_x, "y": new_curve_y})

    def _update_old_curve_data_item(self) -> None:
        """Update the displayed new curve with clipping

        Updates the data displayed with the new curves data item. A temporary
        point will be added if the the new point exceeds the current time
        (because of f.e. inaccurate timestamp)
        """
        i = PlotItemUtils.intersect(self._full_curve_old, self._get_current_time_line_x_pos())
        if i["intersection"] and i["intersection"]["x"] != self._full_curve_old["x"][i["first_after_index"]]\
                and i["intersection"]["y"] != self._full_curve_old["y"][i["first_after_index"]]:
            old_curve_x = [i["intersection"]["x"]]
            old_curve_y = [i["intersection"]["y"]]
        else:
            old_curve_x = []
            old_curve_y = []
        old_curve_x += [] if i["first_after_index"] == -1 else self._full_curve_old["x"][i["first_after_index"]:]
        old_curve_y += [] if i["first_after_index"] == -1 else self._full_curve_old["y"][i["first_after_index"]:]
        self._data_items_data["old_curve_y"] = old_curve_y
        self._data_items_data["old_curve_x"] = old_curve_x
        self._old_curve_data_item.setData({"x": old_curve_x, "y": old_curve_y})

    # Cycle Timestamp Utilities

    def _get_current_cycle_start_timestamp(self):
        """Get first timestamp of the current cycle"""
        return self._cycle_start + self._cycle_number * self._cycle_size

    def _get_previous_cycle_start_timestamp(self):
        """Get first timestamp of the previous cycle"""
        return self._cycle_start + (self._cycle_number - 1) * self._cycle_size

    def _get_current_cycle_end_timestamp(self):
        """Get last timestamp of the current cycle"""
        return self._cycle_end + self._cycle_number * self._cycle_size

    def _get_previous_cycle_end_timestamp(self):
        """Get last timestamp of the previous cycle"""
        return self._cycle_end + (self._cycle_number - 1) * self._cycle_size

    def _get_current_cycle_offset(self) -> float:
        """Get first timestamp of the previous cycle"""
        return self._cycle_size * self._cycle_number

    def _get_previous_cycle_offset(self) -> float:
        """Get the time difference between the last cycle start and the first
        timestamp in the first ever cycle
        """
        return self._cycle_size * (self._cycle_number - 1)

    def _get_current_time_line_x_pos(self) -> float:
        """Get the display position of the vertical line representing the
        current time
        """
        return self._last_timestamp - self._get_current_cycle_offset()

    # Testing utilities

    def get_data_items_data(self) -> Dict[str, List[float]]:
        """Return a dictionary holding the data passed to the PlotDataItem. This
        can be used to find out, what the PlotDataItems are showing.

        Returns:
            Dictionary mapping the description where the points are displayed to
            a list of points
        """
        return self._data_items_data

    def get_full_buffer(self) -> Dict[str, List[float]]:
        """Get a list of all points saved inside this PlotItem"""
        return self._full_curve_buffer

    def get_new_curve_buffer(self) -> Dict[str, List[float]]:
        """Return a list of points that are in the current cycle"""
        return self._full_curve_new

    def get_old_curve_buffer(self) -> Dict[str, List[float]]:
        """Return a list of points that are in the previous cycle"""
        return self._full_curve_old


class ScrollingPlotItem(ExtendedPlotItem):
    """Displays data as a sliding pointer widget"""

    def __init__(self, **kwargs):
        """Constructor

        Create a new instance of ScrollingPlotItem

        Args:
            **kwargs: Passed to superclass
        """
        super().__init__(**kwargs)
        self._full_curve_buffer: Dict[str, List[float]] = {
            "x": [],
            "y": [],
        }
        self._cycle_start: float = 0.0
        self._cycle_end: float = 0.0
        self._plot_data_item: PlotDataItem = self.plot()

    def plot_append(self, x_pos, y_pos):
        """Handle a new published dataset

        Append a new plot and write it to the buffer of points. After
        appending the new point trigger a timing update to make sure the new
        point gets drawn properly

        Args:
            x_pos: Position on the horizontal axis, for example timestamp
            y_pos: Position on the vertical axis
        """
        self._full_curve_buffer["x"].append(x_pos)
        self._full_curve_buffer["y"].append(y_pos)
        if len(self._full_curve_buffer["x"]) > _MAX_BUFFER_SIZE:
            self._full_curve_buffer["x"] = self._full_curve_buffer["x"][_MAX_BUFFER_SIZE // 2:]
            self._full_curve_buffer["y"] = self._full_curve_buffer["y"][_MAX_BUFFER_SIZE // 2:]
        self._handle_timing_update(self._last_timestamp)

    def _handle_timing_update(self, timestamp: float) -> None:
        """Handle a new published timestamp

        Handle a update in the current time triggered by the timing source.
        The shown curve will be clipped on both ends according to the passed
        timestamp.

        Args:
            timestamp (float): Current time as timestamp
        """
        super()._handle_timing_update(timestamp)
        self._draw_time_line_decorator(timestamp=timestamp, position=timestamp)
        self._update_curve_data_item()
        x_pos = self._full_curve_buffer["x"][-1] if self._full_curve_buffer["x"] else timestamp
        y_pos = self._full_curve_buffer["y"][-1] if self._full_curve_buffer["y"] else 0
        self._draw_plotting_position_decorators(x_pos, y_pos)

    def _update_curve_data_item(self) -> None:
        """Update the actual drawn data

        Update the data for the inner PlotDataItem and clip the resulting
        curves at the required positions for not overdrawing boundaries.
        """
        self._update_cycle_numbers()
        # Calculate intersections with cycle start and cycle end
        intersection_start = PlotItemUtils.intersect(self._full_curve_buffer, self._cycle_start)
        intersection_end = PlotItemUtils.intersect(self._full_curve_buffer, self._cycle_end)
        curve_x = [] if not intersection_start["intersection"] else [intersection_start["intersection"]["x"]]
        curve_y = [] if not intersection_start["intersection"] else [intersection_start["intersection"]["y"]]
        if not intersection_end["intersection"]:
            # Add points from cycle start to newest appended point
            curve_x += [] if intersection_start["first_after_index"] == -1 else self._full_curve_buffer["x"][intersection_start["first_after_index"]:]
            curve_y += [] if intersection_start["first_after_index"] == -1 else self._full_curve_buffer["y"][intersection_start["first_after_index"]:]
        else:
            # Add points between cycle start and end
            curve_x += [] if intersection_start["first_after_index"] == -1 else \
                self._full_curve_buffer["x"][intersection_start["first_after_index"]:intersection_end["first_after_index"]]
            curve_y += [] if intersection_start["first_after_index"] == -1 else \
                self._full_curve_buffer["y"][intersection_start["first_after_index"]:intersection_end["first_after_index"]]
            # Add new point at cycle start created with clipping
            curve_x += [intersection_end["intersection"]["x"]]
            curve_y += [intersection_end["intersection"]["y"]]
        self._plot_data_item.setData({"x": curve_x, "y": curve_y})

    def _update_cycle_numbers(self) -> None:
        """Update the current cycle number"""
        self._cycle_start = self._last_timestamp - self._cycle_size
        self._cycle_end = self._last_timestamp

    def get_full_buffer(self):
        """Get a list of all points save inside the PlotItem"""
        return self._full_curve_buffer
