"""
Data buffers for the data model for different items
that are able to safe different types and amount of data
"""

import abc
import math
import logging
from typing import List, Optional, Tuple

import numpy as np

from accsoft_gui_pyqt_widgets.graph.datamodel.datamodelclipping import *
from accsoft_gui_pyqt_widgets.graph.widgets.datastructures import PointData

DEFAULT_BUFFER_SIZE: int = 100000

_LOGGER = logging.getLogger(__name__)


class BaseSortedDataBuffer(metaclass=abc.ABCMeta):
    """
    Baseclass for different data buffers.

    Buffer for multiple arrays with data of different types.
    The buffer is containing one array of primary values which
    all values are sorted by. The n arrays of secondary values
    are the values that are belonging to the x axis with the same
    index. For better understanding here a few simple examples:

    For a curve this could look like this:
        primary value:      x position

        secondary value:    y position

    For a bar chart this could look like this:
        primary value:      x position

        secondary value:    y position, height
    """

    def __init__(self, size: int = DEFAULT_BUFFER_SIZE):
        """
        Subclasses should initialize the primary and secondary values
        according to the values they want to save. A convenient way is to
        implement the preparation of primary and secondary values in the
        clear() function.

        Args:
            size: Amount of entries fitting in the buffer
        """
        size = size or DEFAULT_BUFFER_SIZE
        if size < 3:
            size = DEFAULT_BUFFER_SIZE
            _LOGGER.warning(
                f"The requested data-buffer size is too small. As size the default "
                f"{DEFAULT_BUFFER_SIZE} entries will be used"
            )
        self._size = size
        self._primary_values: np.ndarray = np.array([])
        self._secondary_values_lists: List[np.ndarray] = []
        self._space_left: int
        self._smallest_distance_between_two_primary_values: float
        self._next_free_slot: int
        self._is_empty: bool
        # This is needed for initialization
        self.reset()

    def reset(self) -> None:
        """ Clear all saved fields and intialize them again

        Clear the buffer by initializing primary and secondary values again.
        Since different databuffers can hold different types and amounts of secondary
        values, initializing the list of secondary values has to be done in each
        subclass.
        """
        self._primary_values = np.array([])
        self._secondary_values_lists = []
        self._space_left = self._size
        self._smallest_distance_between_two_primary_values = np.inf
        self._next_free_slot = 0
        self._is_empty = True

    # ~~~~~ Properties for buffer important buffer information ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @property
    def space_left(self) -> int:
        """Free spaces left in the buffer"""
        self._update_space_left()
        return self._space_left

    @property
    def count_occupied_entries(self) -> int:
        """Next free index location (== amount of occupied indices)"""
        return self._size - self.space_left

    @property
    def full_size(self) -> int:
        """Buffer size"""
        return self._primary_values.size

    @property
    def index_of_last_primary_value_not_nan(self) -> int:
        """Search fo the newest primary value (f.e. x value) that is a number"""
        next_free_index = self.count_occupied_entries
        last_non_free_and_not_none_index = next_free_index - 1
        while last_non_free_and_not_none_index > 0 and np.isnan(
            self._primary_values[last_non_free_and_not_none_index]
        ):
            last_non_free_and_not_none_index -= 1
        return last_non_free_and_not_none_index

    @property
    def smallest_distance_between_primary_values(self) -> float:
        """Get the smallest distance between two primary values in the buffer"""
        return self._smallest_distance_between_two_primary_values

    def is_empty(self) -> bool:
        """Check if the buffer is still empty"""
        return self._is_empty

    def as_np_array(self) -> Tuple[np.ndarray, ...]:
        """ Return Buffer as Tuple of Numpy arrays

        Gets the buffers written values (empty fields are cut) as numpy
        arrays packaged in a tuple with the first one being the primary values
        and the followings being the secondary values in the same order as they
        are saved in the Buffer's secondary values list.
        """
        i = self.count_occupied_entries
        values: List[np.ndarray] = [self._primary_values[:i]]
        for secondary_values in self._secondary_values_lists:
            values.append(secondary_values[:i])
        return tuple(values)

    @abc.abstractmethod
    def get_subset(self, start: float, end: float) -> Tuple[np.ndarray, ...]:
        """ Get Subset of a specific start and end point

        Args:
            start: start boundary for primary values of elements that should be included in the subset
            end: end boundary for primary values of elements that should be included in the subset

        Returns:
            Primary and Secondary Values of the subset in a tuple of the form (p_vals, s_vals_1, s_vals_2, ...)
        """
        pass

    # ~~~~~ Add new entries to buffer ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add_values_to_buffer(
        self, primary_value: float, secondary_values: List[float]
    ) -> None:
        """Append a new entry to the buffer

        Add a single entry into the buffer and sort it in at the right position
        """
        if primary_value is None or secondary_values is None:
            raise ValueError("Passed keyword arguments do not match the expected ones.")
        svl = [np.array([secondary_value]) for secondary_value in secondary_values]
        primary_values, secondary_values_list = self._prepare_buffer_and_values(
            primary_values=np.array([primary_value]), secondary_values_list=svl
        )
        if primary_values.size > 0 and False not in [
            value.size > 0 for value in secondary_values_list
        ]:
            self._sort_in_point(
                primary_value=primary_value, secondary_values=secondary_values
            )

    def add_list_of_values_to_buffer(
        self, primary_values: np.ndarray, secondary_values_list: List[np.ndarray]
    ) -> None:
        """Append a list of entries

        Entries that are passed will be ordered according to their primary value.
        NaN values are sorted according to numpy.sort, which means they will
        be moved to the end of the array. To make sure NaN is appended at the
        right position, it should be passed as a single point (add_point()).

        Params:
            **kwargs: primary secondary values, see subtype implementations for
                      more specific information of the params for each buffer type
        """
        if primary_values is None or secondary_values_list is None:
            raise ValueError("Passed keyword arguments do not match the expected ones.")
        primary_values, secondary_values_list = self._prepare_buffer_and_values(
            primary_values=primary_values, secondary_values_list=secondary_values_list
        )
        for index, p_val in enumerate(primary_values):
            sec_values = []
            for secondary_values_entry in secondary_values_list:
                sec_values.append(secondary_values_entry[index])
            self._sort_in_point(primary_value=p_val, secondary_values=sec_values)

    # ~~~~~ Preparation and Sorting in of new data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _sort_in_point(
        self, primary_value: float, secondary_values: List[float]
    ) -> None:
        """ Sort in a single point by its primary value

        This function does not prepare anything for storing the points.
        F.e. id does not check if the point is in the currently saved range
        or earlier as well as it does not check, if enough space is left to add.
        For making sure the buffer is prepared for the addition of a new point,
        use the public functions add_point and add_list_of_points.

        If possible, primary values will always be sorted in after nan values,
        except this would destroy the order. The corresponding secondary values
        will be sorted in at the same index as the primary value regardless of
        their value.

        Example:
            [2.0] into [1.0, nan, 3.0] -> [1.0, nan, 2.0, 3.0] \n
            [0.0] into [1.0, nan, 3.0] -> [0.0, 1.0, nan, 2.0, 3.0]

        Args:
            primary_value: Primary value of the new entry
            secondary_values: Secondary values of the new entry

        Returns:
            None
        """
        next_free_index = self.count_occupied_entries
        last_non_free_and_not_none_index = self.index_of_last_primary_value_not_nan
        if self._is_new_value_greater_than_all_others(
            primary_value, last_non_free_and_not_none_index
        ):
            self._primary_values[next_free_index] = primary_value
            for index, entry in enumerate(self._secondary_values_lists):
                entry[next_free_index] = secondary_values[index]
                self._secondary_values_lists[index] = entry
            try:
                distance = primary_value - self._primary_values[next_free_index - 1]
            except IndexError:
                distance = np.inf
        else:
            i = self.count_occupied_entries
            write_index = self.searchsorted_with_nans(
                array=self._primary_values[:i], value=primary_value, side="right"
            )
            self._primary_values = np.insert(
                self._primary_values, write_index, primary_value
            )
            # inserting lengthens the array -> cut last value
            self._primary_values = self._primary_values[:-1]
            for index, entry in enumerate(self._secondary_values_lists):
                entry = np.insert(entry, write_index, secondary_values[index])
                # inserting lengthens the array -> cut last value
                entry = entry[:-1]
                self._secondary_values_lists[index] = entry
            try:
                distance_front = primary_value - self._primary_values[write_index - 1]
                distance_after = self._primary_values[write_index + 1] - primary_value
                distance = (
                    distance_front
                    if distance_front < distance_after
                    else distance_after
                )
            except IndexError:
                distance = np.inf
        self._next_free_slot += 1
        self._is_empty = False
        if self._smallest_distance_between_two_primary_values > distance:
            self._smallest_distance_between_two_primary_values = distance

    def _prepare_buffer_and_values(
        self, primary_values: np.ndarray, secondary_values_list: List[np.ndarray]
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """ Prepare the buffer as well as the new entries

        Prepare the inner numpy arrays for appending points by
        making sure that enough free spaces are left for appending.
        An array of length 1 with the value nan as its content will be
        returned empty, if the latest entry in the buffer is nan as well.
        Either all values of one entry or none are removed. The prepared
        arrays that are returned will have the same length.

        Params:
            primary_values: Sorted Primary values that are supposed to be added
            secondary_values: Sorted Secondary values that are supposed to be added

        Return:
            Primary and Secondary Values without the values that are not in the
            buffers range.
        """
        if self._are_primary_and_secondary_value_arrays_empty(
            primary_values=primary_values, secondary_values_list=secondary_values_list
        ):
            return primary_values, secondary_values_list
        if self._is_double_nan_append(
            primary_values=primary_values, secondary_values_list=secondary_values_list
        ):
            return (
                np.array([]),
                [np.array([])],
            )
        primary_values, secondary_values_list = self.sorted_data_arrays(
            primary_values, secondary_values_list
        )
        if primary_values.size > self.space_left:
            primary_values, secondary_values_list = self._shift_buffer_and_cut_input(
                primary_values=primary_values,
                secondary_values_list=secondary_values_list
            )
        return primary_values, secondary_values_list

    def _shift_buffer_and_cut_input(
        self,
        primary_values: np.ndarray,
        secondary_values_list: List[np.ndarray]
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Shift the buffer to make room for the new values provided with
        the input and cut the input if there are any values that are
        not in the buffer range anymore after the shift.

        Args:
            primary_values: primary values from the given input
            secondary_values_list: list of secondary values from the given input

        Returns:
            Primary and Secondary Values after the possible shift
        """
        free_spaces_after_input = math.ceil(self._size / 3)
        spaces_to_shift: int = free_spaces_after_input + primary_values.size
        if spaces_to_shift > self.count_occupied_entries:
            spaces_to_shift = self.count_occupied_entries
        input_cut: int
        input_cut, spaces_to_shift = self._find_removable_part_from_input(
            free_spaces_after_input=free_spaces_after_input,
            spaces_to_shift=spaces_to_shift,
            primary_values=primary_values
        )
        self._shift_buffer_to_the_left(spaces_to_shift=spaces_to_shift)
        # Cut data from input that is out of range after shift
        primary_values = primary_values[input_cut:]
        for index, secondary_values in enumerate(secondary_values_list):
            secondary_values = secondary_values[input_cut:]
            secondary_values_list[index] = secondary_values
        return primary_values, secondary_values_list

    def _find_removable_part_from_input(
        self,
        free_spaces_after_input: int,
        spaces_to_shift: int,
        primary_values: np.ndarray
    ) -> Tuple[int, int]:
        """Find the first n primary values from the input that are not needed.

        This can be the case if length of the input is longer as the overall
        length of the buffer or the values are smaller than others that are
        removed by shifting the buffer to make room for the new values.
        The passed values are not changed.

        Args:
            free_spaces_after_input: count spaces that should be free after inserting the new data
            primary_values: primary values from the input

        Returns:
            Count of elements in the front that can be cut from the input
        """
        if spaces_to_shift < self._size:
            new_oldest_primary_value = self._primary_values[spaces_to_shift]
        else:
            new_oldest_primary_value = np.nan
        count_points_that_have_to_be_cut_from_the_front: int = 0
        if primary_values.size > self._size:
            count_points_that_have_to_be_cut_from_the_front += (
                    primary_values.size - self._size + free_spaces_after_input
            )
        if not np.isnan(new_oldest_primary_value) and new_oldest_primary_value >= primary_values[0]:
            while (
                    count_points_that_have_to_be_cut_from_the_front < primary_values.size
                    and new_oldest_primary_value > primary_values[count_points_that_have_to_be_cut_from_the_front]
                    and spaces_to_shift > 0
                    and primary_values.size > 0
            ):
                spaces_to_shift -= 1
                if not np.isnan(self._primary_values[spaces_to_shift]):
                    new_oldest_primary_value = self._primary_values[spaces_to_shift]
                count_points_that_have_to_be_cut_from_the_front += 1
        return count_points_that_have_to_be_cut_from_the_front, spaces_to_shift

    def _shift_buffer_to_the_left(self, spaces_to_shift: int) -> None:
        """Shift the buffer by a given number of places to the left."""
        self._primary_values = np.pad(
            self._primary_values[spaces_to_shift:],
            (0, spaces_to_shift),
            "constant",
            constant_values=(np.nan, np.nan),
        )
        for index, secondary_values in enumerate(self._secondary_values_lists):
            secondary_values = np.pad(
                secondary_values[spaces_to_shift:],
                (0, spaces_to_shift),
                "constant",
                constant_values=(np.nan, np.nan),
            )
            self._secondary_values_lists[index] = secondary_values
        self._next_free_slot -= spaces_to_shift

    # ~~~~~~ Helper functions for more readable conditions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _is_double_nan_append(
        self, primary_values: np.ndarray, secondary_values_list: List[np.ndarray]
    ) -> bool:
        """function for checking if array would lead to a double nan in the buffer"""
        arrays_of_length_one = primary_values.size == 1
        last_value_in_buffer_is_nan = self._next_free_slot > 0 and np.isnan(
            self._primary_values[self._next_free_slot - 1]
        )
        next_value_to_add_is_nan = self._next_free_slot > 0 and np.isnan(
            primary_values[0]
        )
        if self._next_free_slot > 0:
            for secondary_values in secondary_values_list:
                arrays_of_length_one = (
                    arrays_of_length_one and secondary_values.size == 1
                )
                for self_secondary_values in self._secondary_values_lists:
                    if not isinstance(
                        self_secondary_values[self._next_free_slot - 1], str
                    ):
                        last_value_in_buffer_is_nan = (
                            last_value_in_buffer_is_nan
                            and np.isnan(
                                self_secondary_values[self._next_free_slot - 1]
                            )
                        )
                if not isinstance(secondary_values[0], str):
                    next_value_to_add_is_nan = next_value_to_add_is_nan and np.isnan(
                        secondary_values[0]
                    )
        return (
            arrays_of_length_one
            and next_value_to_add_is_nan
            and last_value_in_buffer_is_nan
        )

    def _is_new_value_greater_than_all_others(
        self, primary_value: float, last_non_free_and_not_none_index: int
    ) -> bool:
        """Check if the new primary value is greater than the ones in the buffer"""
        return (
            last_non_free_and_not_none_index < 0
            or np.isnan(primary_value)
            or primary_value >= self._primary_values[last_non_free_and_not_none_index]
            or np.isnan(self._primary_values[last_non_free_and_not_none_index])
        )

    def _update_space_left(self) -> None:
        """Update the space that is left in this buffer"""
        self._space_left = self._size - self._next_free_slot

    # ~~~~~~ Static functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @staticmethod
    def _get_indices_for_cutting_leading_and_trailing_nans(
        primary_values: np.ndarray,
        secondary_values_list: List[np.ndarray],
        start_index: int,
        end_index: int,
    ) -> Tuple[int, int]:
        """Cut trailing and leading nans

        Move start and end index to cut leading and trailing nans. Nans in surrounded
        by non nan values are not affected by this. The passed arrays won't be changed
        in any way.

        Return:
            start and end index that can be used to cut leading and trailing nans
        """
        if 0 < end_index <= primary_values.size:
            last_value_in_all_arrays_nan = np.isnan(primary_values[end_index - 1])
            for secondary_values in secondary_values_list:
                if isinstance(secondary_values[end_index - 1], float):
                    last_value_in_this_array_nan = secondary_values[
                        end_index - 1
                    ] is None or np.isnan(secondary_values[end_index - 1])
                    last_value_in_all_arrays_nan = (
                        last_value_in_all_arrays_nan and last_value_in_this_array_nan
                    )
            if last_value_in_all_arrays_nan and end_index > start_index:
                end_index -= 1
        if 0 <= start_index < primary_values.size:
            start_value_in_all_arrays_nan = np.isnan(primary_values[start_index])
            for secondary_values in secondary_values_list:
                if isinstance(secondary_values[start_index], float):
                    start_value_in_this_array_nan = secondary_values[
                        start_index
                    ] is None or np.isnan(secondary_values[start_index])
                    start_value_in_all_arrays_nan = (
                        start_value_in_all_arrays_nan and start_value_in_this_array_nan
                    )
            if start_value_in_all_arrays_nan and start_index < end_index:
                start_index += 1
        return start_index, end_index

    @staticmethod
    def _are_primary_and_secondary_value_arrays_empty(
        primary_values: np.ndarray, secondary_values_list: List[np.ndarray]
    ) -> bool:
        """function for checking if the passed numpy arrays are empty"""
        if primary_values.size != 0:
            return False
        return any(secondary_values.size for secondary_values in secondary_values_list)

    @staticmethod
    def sorted_data_arrays(
        primary_values: np.ndarray, secondary_values_list: List[np.ndarray]
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """ Sort Primary and Secondary Values

        Sort the passed primary and secondary values by the primary one.
        Nan Values will be sorted to the end. The original arrays are not
        mutated, returned are sorted copies of the original passed data.
        """
        if not SortedCurveDataBuffer.data_arrays_are_compatible(primary_values, secondary_values_list):
            raise ValueError("The passed arrays must have the same length.")
        sorted_primary_values_indices = np.argsort(primary_values)
        sorted_primary_values = primary_values[sorted_primary_values_indices]
        secondary_values_list_sorted: List[np.ndarray] = []
        for secondary_values in secondary_values_list:
            sorted_secondary_values = secondary_values[
                sorted_primary_values_indices
            ][:]
            secondary_values_list_sorted.append(sorted_secondary_values)
        return sorted_primary_values, secondary_values_list_sorted

    @staticmethod
    def data_arrays_are_compatible(
        primary_values: np.ndarray, secondary_values_list: List[np.ndarray]
    ) -> bool:
        """Check if both arrays have the same shape and length and the correct type"""
        arrays_are_not_none = primary_values is not None
        arrays_correct_type = isinstance(primary_values, np.ndarray)
        arrays_right_shape = True
        arrays_right_size = True
        for secondary_values in secondary_values_list:
            arrays_are_not_none = arrays_are_not_none and secondary_values is not None
            arrays_correct_type = isinstance(secondary_values, np.ndarray)
            arrays_right_shape = arrays_right_shape and np.shape(primary_values) == np.shape(secondary_values)
            arrays_right_size = (
                arrays_right_size and primary_values.size == secondary_values.size
            )
        return (
            arrays_are_not_none
            and arrays_correct_type
            and arrays_right_shape
            and arrays_right_size
        )

    @staticmethod
    def searchsorted_with_nans(array: np.ndarray, value: float, side: str) -> int:
        """np.searchsorted with nan support"""
        sorting_indices = np.argsort(array)
        index = np.searchsorted(array, value, side=side, sorter=sorting_indices)
        if index <= 0:
            return index
        count_nan_values = np.count_nonzero(~np.isnan(array))
        if index >= count_nan_values:
            return array.size
        return sorting_indices[index]


class SortedCurveDataBuffer(BaseSortedDataBuffer):

    """Sorted Buffer for a Line Graph

    Content
        Primary Value =     X Value

        Secondary Values =  Y Value
    """

    def reset(self) -> None:
        """ Reset the buffer"""
        super().reset()
        # X Value
        self._primary_values = np.empty(self._size)
        self._primary_values.fill(np.nan)
        # Y Value
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[0].fill(np.nan)

    def add_entry(self, x_value: float, y_value: float) -> None:
        """Append a single point to the buffer"""
        super().add_values_to_buffer(primary_value=x_value, secondary_values=[y_value])

    def add_list_of_entries(self, x_values: np.ndarray, y_values: np.ndarray) -> None:
        """Append a list of points to the buffer"""
        super().add_list_of_values_to_buffer(
            primary_values=x_values, secondary_values_list=[y_values]
        )

    def get_subset(
        self, start: float, end: float, clip_at_boundaries: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Get Subset of the data

        Additional to the baseclass it is possible to clip the curve at the
        start and end, so the curve fills the whole area. The subset then
        contains points that are calculated by intersecting the curve with
        the given boundaries and adding these points to the end of the curve.
        The interpolated points will not be added permanently to the data-buffer
        and are only included in the returned subset.

        Args:
            start: start boundary for primary values of elements that should be included in the subset
            end: end boundary for primary values of elements that should be included in the subset
            clip_at_boundaries: If true the curve will be interpolated at the edges and the two
                                new points at the edge will be contained in the subset

        Returns:
            X and Y Values of the subset in a tuple of the form (x_values, y_values)
        """
        i = self.count_occupied_entries
        x_values: np.ndarray = self._primary_values[:i]
        y_values: np.ndarray = self._secondary_values_lists[0][:i]
        start_index = self.searchsorted_with_nans(
            array=x_values, value=start, side="left"
        )
        end_index = self.searchsorted_with_nans(array=x_values, value=end, side="right")
        if clip_at_boundaries:
            return self._clip_at_boundaries_if_possible(
                x_values=x_values,
                y_values=y_values,
                start_index=start_index,
                end_index=end_index,
                start_boundary=start,
                end_boundary=end,
            )
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x_values,
            secondary_values_list=[y_values],
            start_index=start_index,
            end_index=end_index,
        )
        return x_values[start_index:end_index], y_values[start_index:end_index]

    @staticmethod
    def _clip_at_boundaries_if_possible(
        x_values, y_values, start_index, end_index, start_boundary, end_boundary
    ) -> Tuple[np.ndarray, np.ndarray]:
        """ Create subset with clipped ends

        Args:
            x_values: Array of x values to create the subset from
            y_values: Array of y values to create the subset from
            start_index: Index of the first point after the starting boundary
            end_index: Index of the last point before the end boundary
            start_boundary: Min X value, so the point will be added to the subset
            end_boundary: Max X value, so the point will be added to the subset

        Returns:
            Subset with clipping points, if necessary
        """
        start_clipping_point: Optional[PointData] = None
        end_clipping_point: Optional[PointData] = None
        start_index, end_index = SortedCurveDataBuffer._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x_values,
            secondary_values_list=[y_values],
            start_index=start_index,
            end_index=end_index,
        )
        # Clip with start boundary, if points are available in the front
        if 0 < start_index < x_values.size and x_values[start_index] != start_boundary:
            point_after_boundary = PointData(
                x_value=x_values[start_index], y_value=y_values[start_index]
            )
            point_in_front_of_boundary = PointData(
                x_value=x_values[start_index - 1], y_value=y_values[start_index - 1]
            )
            if (
                not point_in_front_of_boundary.contains_nan()
                and not point_after_boundary.contains_nan()
            ):
                start_clipping_point = calc_intersection(
                    point_in_front_of_boundary, point_after_boundary, start_boundary
                )
        # Clip with end boundary
        if (
            0 < end_index < x_values.size
            and end_index < y_values.size
            and x_values[end_index - 1] != end_boundary
        ):
            point_after_boundary = PointData(
                x_value=x_values[end_index], y_value=y_values[end_index]
            )
            point_in_front_of_boundary = PointData(
                x_value=x_values[end_index - 1], y_value=y_values[end_index - 1]
            )
            if (
                not point_in_front_of_boundary.contains_nan()
                and not point_after_boundary.contains_nan()
            ):
                end_clipping_point = calc_intersection(
                    point_in_front_of_boundary, point_after_boundary, end_boundary
                )
        # Connect
        return_x: np.ndarray = x_values[start_index:end_index]
        return_y: np.ndarray = y_values[start_index:end_index]
        if start_clipping_point:
            return_x = np.concatenate(
                (np.array([start_clipping_point.x_value]), return_x)
            )
            return_y = np.concatenate(
                (np.array([start_clipping_point.y_value]), return_y)
            )
        if end_clipping_point:
            return_x = np.concatenate(
                (return_x, np.array([end_clipping_point.x_value]))
            )
            return_y = np.concatenate(
                (return_y, np.array([end_clipping_point.y_value]))
            )
        return return_x, return_y


class SortedBarGraphDataBuffer(BaseSortedDataBuffer):

    """Sorted Buffer for a Bar Graph

    Content:
        Primary Value =     X Value

        Secondary Values =  Y Value, Height
    """

    def reset(self) -> None:
        """Reset the buffer"""
        super().reset()
        # X Value
        self._primary_values = np.empty(self._size)
        self._primary_values.fill(np.nan)
        # Y Value
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[0].fill(np.nan)
        # Height
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[1].fill(np.nan)

    def add_entry(self, x_value: float, y_value: float, height: float) -> None:
        """Append a single bar to the buffer"""
        super().add_values_to_buffer(
            primary_value=x_value, secondary_values=[y_value, height]
        )

    def add_list_of_entries(
        self, x_values: np.ndarray, y_values: np.ndarray, height: np.ndarray
    ) -> None:
        """Append a list of bars to the buffer"""
        super().add_list_of_values_to_buffer(
            primary_values=x_values, secondary_values_list=[y_values, height]
        )

    def get_subset(
        self, start: float, end: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """ Get Subset of a specific start and end point

        Args:
            start: start boundary for primary values of elements that should be included in the subset
            end: end boundary for primary values of elements that should be included in the subset

        Returns:
            Primary and Secondary Values of the subset in a tuple of the form (x_values, y_values, height_values)
        """
        i = self.count_occupied_entries
        x_values: np.ndarray = self._primary_values[:i]
        y_values: np.ndarray = self._secondary_values_lists[0][:i]
        height: np.ndarray = self._secondary_values_lists[1][:i]
        start_index = self.searchsorted_with_nans(
            array=x_values, value=start, side="left"
        )
        end_index = self.searchsorted_with_nans(array=x_values, value=end, side="right")
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x_values,
            secondary_values_list=[y_values],
            start_index=start_index,
            end_index=end_index,
        )
        return (
            x_values[start_index:end_index],
            y_values[start_index:end_index],
            height[start_index:end_index],
        )


class SortedInjectionBarsDataBuffer(BaseSortedDataBuffer):

    """Sorted Buffer for a Injection Bar Graph

    Content
        Primary Value =     X Value

        Secondary Values =  Y Value, Height, Width, Top, Bottom, Label
    """

    def reset(self) -> None:
        """Reset the buffer"""
        super().reset()
        # X Value
        self._primary_values = np.empty(self._size)
        self._primary_values.fill(np.nan)
        # Y Value
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[0].fill(np.nan)
        # Height
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[1].fill(np.nan)
        # Width
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[2].fill(np.nan)
        # Top
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[3].fill(np.nan)
        # Bottom
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[4].fill(np.nan)
        # Label
        self._secondary_values_lists.append(np.empty(self._size, dtype="<U100"))

    def add_entry(
        self,
        x_value: float,
        y_value: float,
        height: float,
        width: float,
        top: float,
        bottom: float,
        label: str,
    ) -> None:
        """Append an injectionbar to the buffer"""
        super().add_values_to_buffer(
            primary_value=x_value,
            secondary_values=[y_value, height, width, top, bottom, label],
        )

    def add_list_of_entries(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray,
        heights: np.ndarray,
        widths: np.ndarray,
        tops: np.ndarray,
        bottoms: np.ndarray,
        labels: np.ndarray,
    ) -> None:
        """Append a list of injectionbars to the buffer"""
        super().add_list_of_values_to_buffer(
            primary_values=x_values,
            secondary_values_list=[y_values, heights, widths, tops, bottoms, labels],
        )

    def get_subset(
        self, start: float, end: float
    ) -> Tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """ Get Subset of a specific start and end point

        Args:
            start: start boundary for primary values of elements that should be included in the subset
            end: end boundary for primary values of elements that should be included in the subset

        Returns:
            Primary and Secondary Values of the subset in a tuple of the form
            (x_values, y_values, height_values, width_values, top_values, bottom_values, labels)
        """
        i = self.count_occupied_entries
        x_values: np.ndarray = self._primary_values[:i]
        y_values: np.ndarray = self._secondary_values_lists[0][:i]
        heights: np.ndarray = self._secondary_values_lists[1][:i]
        widths: np.ndarray = self._secondary_values_lists[2][:i]
        tops: np.ndarray = self._secondary_values_lists[3][:i]
        bottoms: np.ndarray = self._secondary_values_lists[4][:i]
        labels: np.ndarray = self._secondary_values_lists[5][:i]
        start_index = self.searchsorted_with_nans(
            array=x_values, value=start, side="left"
        )
        end_index = self.searchsorted_with_nans(array=x_values, value=end, side="right")
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x_values,
            secondary_values_list=[y_values, heights, widths, tops, bottoms, labels],
            start_index=start_index,
            end_index=end_index,
        )
        return (
            x_values[start_index:end_index],
            y_values[start_index:end_index],
            heights[start_index:end_index],
            widths[start_index:end_index],
            tops[start_index:end_index],
            bottoms[start_index:end_index],
            labels[start_index:end_index],
        )


class SortedTimestampMarkerDataBuffer(BaseSortedDataBuffer):

    """Sorted Buffer for Timestamp Markers

    Content
        Primary Value =     X Value

        Secondary Values =  Y Value, Height
    """

    def reset(self) -> None:
        """Reset the buffer"""
        super().reset()
        # X Value
        self._primary_values = np.empty(self._size)
        self._primary_values.fill(np.nan)
        # Color
        self._secondary_values_lists.append(np.empty(self._size, dtype="<U100"))
        # Label
        self._secondary_values_lists.append(np.empty(self._size, dtype="<U100"))

    def add_entry(self, x_value: float, color: str, label: str) -> None:
        """Append a single infinite line to the buffer"""
        super().add_values_to_buffer(
            primary_value=x_value, secondary_values=[color, label]
        )

    def add_list_of_entries(
        self, x_values: np.ndarray, colors: np.ndarray, labels: np.ndarray
    ) -> None:
        """Append a list of infinite lines"""
        super().add_list_of_values_to_buffer(
            primary_values=x_values, secondary_values_list=[colors, labels]
        )

    def get_subset(
        self, start: float, end: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """ Get Subset of a specific start and end point

        Args:
            start: start boundary for primary values of elements that should be included in the subset
            end: end boundary for primary values of elements that should be included in the subset

        Returns:
            Primary and Secondary Values of the subset in a tuple of the form
            (x_values, colors, labels)
        """
        i = self.count_occupied_entries
        x_values: np.ndarray = self._primary_values[:i]
        color: np.ndarray = self._secondary_values_lists[0][:i]
        label: np.ndarray = self._secondary_values_lists[1][:i]
        start_index = self.searchsorted_with_nans(
            array=x_values, value=start, side="left"
        )
        end_index = self.searchsorted_with_nans(array=x_values, value=end, side="right")
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x_values,
            secondary_values_list=[color, label],
            start_index=start_index,
            end_index=end_index,
        )
        return (
            x_values[start_index:end_index],
            color[start_index:end_index],
            label[start_index:end_index],
        )
