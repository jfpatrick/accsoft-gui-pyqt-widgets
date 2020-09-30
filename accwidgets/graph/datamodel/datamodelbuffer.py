"""
Data buffers store the actual visualized data that is managed by a model.
"""


import math
import warnings
import numpy as np
from typing import Optional, Tuple, List, Union
from abc import ABC, abstractmethod
from accwidgets.graph import PointData, DEFAULT_BUFFER_SIZE
from accwidgets._deprecations import deprecated_param_alias
from .datamodelclipping import calc_intersection


class BaseSortedDataBuffer(ABC):

    def __init__(self, size: int = DEFAULT_BUFFER_SIZE):
        """
        Base class for all data buffers. Internally, data is split into
        2 separate arrays of "primary" and "secondary" values respectively.
        Primary values are always a 1-dimensional array, for x-position of
        each data entry. Secondary values are a multidimensional array,
        representing the y-value and supporting information. For instance,
        a curve can be stored as:

        * **primary**: x-position; **secondary**: y-position

        while a bar graph can be recoded as:

        * **primary**: x-position; **secondary**: [y-position, height]

        Subclasses should initialize the primary and secondary arrays to
        the values that are appropriate. It is convenient, to do that in
        :meth:`clear`.

        Args:
            size: Amount of entries fitting in the buffer.
        """
        size = size or DEFAULT_BUFFER_SIZE
        if size < 3:
            size = DEFAULT_BUFFER_SIZE
            warnings.warn(f"The requested data-buffer size is too small. As size the default "
                          f"{DEFAULT_BUFFER_SIZE} entries will be used")
        self._size = size
        self._primary_values: np.ndarray = np.array([])
        self._secondary_values_lists: List[np.ndarray] = []
        self._space_left: int
        self._min_primary_value_delta: float
        self._next_free_slot: int
        self._is_empty: bool
        self._contains_nan: bool
        # This is needed for initialization
        self.reset()

    @abstractmethod
    def subset_for_primary_val_range(self, start: float, end: float) -> Tuple[np.ndarray, ...]:
        """
        Get slices of both primary and secondary arrays, ranging between the given start and end points.

        Args:
            start: Lower boundary of the subset.
            end: Upper boundary of the subset.

        Returns:
            Tuple of slices in the form *(primary_slice, secondary_slice1, secondary_slice2, ...)*,
            where amount of slices depends on the dimensions of the secondary array.
        """
        pass

    # TODO: Make protected to not pollute public API. Meant to be accessed by subclasses only.
    def add_entry_to_buffer(self, primary_value: float, secondary_values: List[Union[float, str]]):
        """
        Add a new entry to the buffer.

        This method will also sort the buffer after insertion by the primary value. You must ensure that the
        entered data is valid and can be drawn.

        Args:
            primary_value: Single primary value that should be added to the buffer.
            secondary_values: List of secondary values corresponding to the primary value.
        """
        svl = [np.array([secondary_value]) for secondary_value in secondary_values]
        primary_values, secondary_values_list = self._prepare_buffer_and_values(
            primary_values=np.array([primary_value]),
            secondary_values_list=svl,
        )
        if primary_values.size > 0 and False not in [
            value.size > 0 for value in secondary_values_list
        ]:
            self._sort_in_point(primary_value=primary_value, secondary_values=secondary_values)

    # TODO: Make protected to not pollute public API. Meant to be accessed by subclasses only.
    def add_entries_to_buffer(self, primary_values: np.ndarray, secondary_values_list: List[np.ndarray]):
        """
        Add an array new entries to the buffer.

        This method will also sort the buffer after inserting the values by the primary value.
        :obj:`~numpy.nan` are treated similarly to :func:`numpy.sort`, meaning they will be moved
        to the end of the array. If :obj:`~numpy.nan` values are to be stored at the specific
        positions, use :meth:`add_entry_to_buffer`.

        Args:
            primary_values: Array of primary values that should be added to the buffer.
            secondary_values_list: List of arrays of secondary values, where each array corresponds to the
                                   primary value of the same index.
        """
        if primary_values is None or secondary_values_list is None:
            raise ValueError("Passed keyword arguments do not match the expected ones.")
        primary_values, secondary_values_list = self._prepare_buffer_and_values(
            primary_values=primary_values,
            secondary_values_list=secondary_values_list,
        )
        for index, p_val in enumerate(primary_values):
            sec_values = []
            for secondary_values_entry in secondary_values_list:
                sec_values.append(secondary_values_entry[index])
            self._sort_in_point(primary_value=p_val, secondary_values=sec_values)

    def reset(self):
        """
        Clear internal state and reinitialize attributes to their default values.

        This method re-instantiates buffer arrays, instead of clearing them. Since every
        subclass might use a different structure for those arrays, this method must be overridden
        in subclasses to properly initialize the secondary value array(s).
        """
        self._primary_values = np.array([])
        self._secondary_values_lists = []
        self._space_left = self._size
        self._min_primary_value_delta = np.inf
        self._next_free_slot = 0
        self._is_empty = True
        self._contains_nan = False

    def as_np_array(self) -> Tuple[np.ndarray, ...]:
        """
        Return the buffer as tuple of numpy arrays.

        Returns:
            Tuple, where the first member is the primary array, followed by one or more secondary value arrays.
        """
        i = self.occupied_size
        values: List[np.ndarray] = [self._primary_values[:i]]
        for secondary_values in self._secondary_values_lists:
            values.append(secondary_values[:i])
        return tuple(values)

    # TODO: Make protected to not pollute public API (or even private function in this file). Meant to be accessed by subclasses only.
    @staticmethod
    def sorted_data_arrays(
            primary_values: np.ndarray,
            secondary_values_list: List[np.ndarray],
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Create a sorted copies of passed arrays.

        All arrays are sorted in accordance with ``primary_values``, which is also sorted.
        :obj:`~numpy.nan` values are moved to the end of the array.

        Args:
            primary_values: Array of primary values that will be sorted.
            secondary_values_list: List of arrays of secondary values, where each array corresponds to the
                                   primary value of the same index.

        Returns:
            Sorted copies of arrays.
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

    # TODO: Make protected to not pollute public API (or even private function in this file). Meant to be accessed by subclasses only.
    @staticmethod
    def data_arrays_are_compatible(primary_values: np.ndarray, secondary_values_list: List[np.ndarray]) -> bool:
        """
        Check whether both arrays have the proper type, same shape and size.

        Args:
            primary_values: Array of primary values that should be checked.
            secondary_values_list: List of arrays of secondary values, where each array corresponds to the
                                   primary value of the same index.

        Returns:
            Both arguments are compatible with each other.
        """
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

    @property
    def space_left(self) -> int:
        """Free spots left in the buffer arrays."""
        self._update_space_left()
        return self._space_left

    @property
    def occupied_size(self) -> int:
        """
        Amount of occupied spots in the buffer arrays.

        It is also equal to the next available index.
        """
        return self._size - self.space_left

    @property
    def capacity(self) -> int:
        """Maximum entry count the buffer can hold."""
        return self._primary_values.size

    @property
    def index_of_last_valid(self) -> int:
        """Index of the newest primary value (i.e. x-value) that is a number and not :obj:`~numpy.nan`."""
        next_free_index = self.occupied_size
        last_non_free_and_not_none_index = next_free_index - 1
        while last_non_free_and_not_none_index > 0 and np.isnan(self._primary_values[last_non_free_and_not_none_index]):
            last_non_free_and_not_none_index -= 1
        return last_non_free_and_not_none_index

    @property
    def min_dx(self) -> float:
        """Smallest distance between two primary values in the buffer."""
        return self._min_primary_value_delta

    @property
    def is_empty(self) -> bool:
        """Check if the buffer is still empty."""
        return self._is_empty

    # ~~~~~~~~~~ Private ~~~~~~~~~~

    def _sort_in_point(self, primary_value: float, secondary_values: List[Union[float, str]]):
        """ Sort in a single point by its primary value

        This function does not prepare anything for storing the points.
        F.e. it does not check if the point is in the currently saved range
        or earlier as well as it does not check, if enough space is left to add.
        For making sure the buffer is prepared for the addition of a new point,
        use the public functions add_values_to_buffer and add_list_of_values_to_buffer.

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
        """
        next_free_index = self.occupied_size
        last_non_free_and_not_none_index = self.index_of_last_valid
        # Improve search_sorted
        if not self._contains_nan:
            values = secondary_values + [primary_value]
            self._contains_nan = any((isinstance(i, (float, int)) and np.isnan(i) for i in values))
        if self._is_new_value_greater_than_all_others(primary_value, last_non_free_and_not_none_index):
            self._primary_values[next_free_index] = primary_value
            for index, entry in enumerate(self._secondary_values_lists):
                entry[next_free_index] = secondary_values[index]
                self._secondary_values_lists[index] = entry
            try:
                distance = primary_value - self._primary_values[next_free_index - 1]
            except IndexError:
                distance = np.inf
        else:
            i = self.occupied_size
            write_index = self._searchsorted_with_nans(
                array=self._primary_values[:i],
                value=primary_value,
                side="right",
                contains_nan=self._contains_nan,
            )
            self._primary_values = np.insert(self._primary_values, write_index, primary_value)
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
        if self._min_primary_value_delta > distance:
            self._min_primary_value_delta = distance

    def _prepare_buffer_and_values(
            self,
            primary_values: np.ndarray,
            secondary_values_list: List[np.ndarray],
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
                primary_values=primary_values,
                secondary_values_list=secondary_values_list,
        ):
            return primary_values, secondary_values_list
        primary_values, secondary_values_list = self.sorted_data_arrays(primary_values, secondary_values_list)
        if primary_values.size > self.space_left:
            primary_values, secondary_values_list = self._shift_buffer_and_cut_input(
                primary_values=primary_values,
                secondary_values_list=secondary_values_list,
            )
        return primary_values, secondary_values_list

    def _shift_buffer_and_cut_input(
        self,
        primary_values: np.ndarray,
        secondary_values_list: List[np.ndarray],
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
        if spaces_to_shift > self.occupied_size:
            spaces_to_shift = self.occupied_size
        input_cut: int
        input_cut, spaces_to_shift = self._find_removable_part_from_input(
            free_spaces_after_input=free_spaces_after_input,
            spaces_to_shift=spaces_to_shift,
            primary_values=primary_values,
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
        primary_values: np.ndarray,
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
            count_points_that_have_to_be_cut_from_the_front += (primary_values.size - self._size
                                                                + free_spaces_after_input)
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

    def _shift_buffer_to_the_left(self, spaces_to_shift: int):
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

    def _is_new_value_greater_than_all_others(
            self,
            primary_value: float,
            last_non_free_and_not_none_index: int,
    ) -> bool:
        """Check if the new primary value is greater than the ones in the buffer"""
        return (
            last_non_free_and_not_none_index < 0
            or np.isnan(primary_value)
            or primary_value >= self._primary_values[last_non_free_and_not_none_index]
            or np.isnan(self._primary_values[last_non_free_and_not_none_index])
        )

    def _update_space_left(self):
        """Update the space that is left in this buffer"""
        self._space_left = self._size - self._next_free_slot

    @staticmethod
    def _get_indices_for_cutting_leading_and_trailing_nans(
        primary_values: np.ndarray,
        start_index: int,
        end_index: int,
    ) -> Tuple[int, int]:
        """Cut trailing and leading nans

        Since we define a subset from two primary values, we don't want any leading or
        trailing entries that have NaN as a primary value, since for those it can't be
        said, if they are inside the subset or not.
        Nans surrounded by non nan values are not affected by this. The passed
        arrays won't be changed in any way.

        Return:
            start and end index that can be used to cut leading and trailing nans
        """
        if 0 < end_index <= primary_values.size:
            if np.isnan(primary_values[end_index - 1]) and end_index > start_index:
                end_index -= 1
        if 0 <= start_index < primary_values.size:
            if np.isnan(primary_values[start_index]) and start_index < end_index:
                start_index += 1
        return start_index, end_index

    @staticmethod
    def _are_primary_and_secondary_value_arrays_empty(
            primary_values: np.ndarray,
            secondary_values_list: List[np.ndarray],
    ) -> bool:
        """function for checking if the passed numpy arrays are empty"""
        if primary_values.size != 0:
            return False
        return any(secondary_values.size for secondary_values in secondary_values_list)

    @staticmethod
    def _searchsorted_with_nans(array: np.ndarray, value: float, side: str, contains_nan: bool = True) -> int:
        """np.searchsorted with nan support. This function can be sped up by quite a lot, if the user knows,
        the array does not contain nan values"""
        if not contains_nan:
            return np.searchsorted(array, value, side=side)
        sorting_indices = np.argsort(array)
        index = np.searchsorted(array, value, side=side, sorter=sorting_indices)
        if index <= 0:
            return index
        count_nan_values = np.count_nonzero(~np.isnan(array))
        if index >= count_nan_values:
            return array.size
        return sorting_indices[index]


class SortedCurveDataBuffer(BaseSortedDataBuffer):
    """
    Sorted buffer for a line graph. Its contents are:

    * **primary**: x-position; **secondary**: y-position
    """

    def reset(self):
        super().reset()
        # X Value
        self._primary_values = np.empty(self._size)
        self._primary_values.fill(np.nan)
        # Y Value
        self._secondary_values_lists.append(np.empty(self._size))
        self._secondary_values_lists[0].fill(np.nan)

    @deprecated_param_alias(x_value="x", y_value="y")
    def add_entry(self, x: float, y: float):
        """
        Add a single point to the buffer.

        This method will also sort the buffer after insertion by the x-value. You must ensure that the
        entered data is valid and can be drawn.

        Args:
            x: x-value that should be added to the buffer.
            y: y-value that should be added to the buffer.
        """
        super().add_entry_to_buffer(primary_value=x, secondary_values=[y])

    @deprecated_param_alias(x_values="x", y_values="y")
    def add_list_of_entries(self, x: np.ndarray, y: np.ndarray):
        """
        Add an array of points to the buffer.

        This method will also sort the buffer after inserting the values by the x-value. :obj:`~numpy.nan` are
        treated similarly to :func:`numpy.sort`, meaning they will be moved to the end of the array.
        If :obj:`~numpy.nan` values are to be stored at the specific positions, use :meth:`add_entry`.

        Args:
            x: Array of x-values that should be added to the buffer.
            y: Array of y-values that should be added to the buffer.
        """
        super().add_entries_to_buffer(primary_values=x, secondary_values_list=[y])

    def subset_for_primary_val_range(
            self,
            start: float,
            end: float,
            interpolated: bool = False,
            interpolation_max: int = 100,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get slice of the data, ranging between the given start and end points.

        Additional to the base class it is possible to clip the curve at the
        start and end, so the curve fills the whole area. The subset then
        contains points that are calculated by intersecting the curve with
        the given boundaries and adding these points to the end of the curve.
        The interpolated points will not be added permanently to the data-buffer
        and are only included in the returned subset.

        Args:
            start: Lower boundary of the subset.
            end: Upper boundary of the subset.
            interpolated: Interpolate the curve at the edges, creating an imaginary point on each end
                          (for purposes, when range does not coincide with points directly).
            interpolation_max: Threshold for the amount of points in the slice. When exceeded, interpolation is
                               omitted, since it does not make a visual difference.

        Returns:
            Tuple of x-values and y-values subsets.
        """
        i = self.occupied_size
        x: np.ndarray = self._primary_values[:i]
        y: np.ndarray = self._secondary_values_lists[0][:i]
        start_index = self._searchsorted_with_nans(array=x, value=start, side="left", contains_nan=self._contains_nan)
        end_index = self._searchsorted_with_nans(array=x, value=end, side="right", contains_nan=self._contains_nan)
        # Clipping for a lot of points does not make much sense
        if interpolated and (end_index - start_index) < interpolation_max:
            return self._clip_at_boundaries_if_possible(
                x=x,
                y=y,
                start_index=start_index,
                end_index=end_index,
                start_boundary=start,
                end_boundary=end,
            )
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x,
            start_index=start_index,
            end_index=end_index,
        )
        return x[start_index:end_index], y[start_index:end_index]

    @staticmethod
    @deprecated_param_alias(x_values="x", y_values="y")
    def _clip_at_boundaries_if_possible(
            x: np.ndarray,
            y: np.ndarray,
            start_index: int,
            end_index: int,
            start_boundary: float,
            end_boundary: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """ Create subset with clipped ends

        Args:
            x: Array of x values to create the subset from
            y: Array of y values to create the subset from
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
            primary_values=x,
            start_index=start_index,
            end_index=end_index,
        )
        # Clip with start boundary, if points are available in the front
        if 0 < start_index < x.size and x[start_index] != start_boundary:
            point_after_boundary = PointData(
                x=x[start_index],
                y=y[start_index],
                check_validity=False,
            )
            point_in_front_of_boundary = PointData(
                x=x[start_index - 1],
                y=y[start_index - 1],
                check_validity=False,
            )
            if (
                not point_in_front_of_boundary.is_nan
                and not point_after_boundary.is_nan
            ):
                start_clipping_point = calc_intersection(
                    point_in_front_of_boundary,
                    point_after_boundary,
                    start_boundary,
                )
        # Clip with end boundary
        if (
            0 < end_index < x.size
            and end_index < y.size
            and x[end_index - 1] != end_boundary
        ):
            point_after_boundary = PointData(
                x=x[end_index],
                y=y[end_index],
                check_validity=False,
            )
            point_in_front_of_boundary = PointData(
                x=x[end_index - 1],
                y=y[end_index - 1],
                check_validity=False,
            )
            if (
                not point_in_front_of_boundary.is_nan
                and not point_after_boundary.is_nan
            ):
                end_clipping_point = calc_intersection(
                    point_in_front_of_boundary,
                    point_after_boundary,
                    end_boundary,
                )
        # Connect
        return_x: np.ndarray = x[start_index:end_index]
        return_y: np.ndarray = y[start_index:end_index]
        if start_clipping_point:
            return_x = np.concatenate((np.array([start_clipping_point.x]), return_x))
            return_y = np.concatenate((np.array([start_clipping_point.y]), return_y))
        if end_clipping_point:
            return_x = np.concatenate((return_x, np.array([end_clipping_point.x])))
            return_y = np.concatenate((return_y, np.array([end_clipping_point.y])))
        return return_x, return_y


class SortedBarGraphDataBuffer(BaseSortedDataBuffer):
    """
    Sorted buffer for a bar graph. Its contents are:

    * **primary**: x-position; **secondary**: [y-position, height]
    """

    def reset(self):
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

    @deprecated_param_alias(x_value="x", y_value="y")
    def add_entry(self, x: float, y: float, height: float):
        """
        Add a single bar to the buffer.

        This method will also sort the buffer after insertion by the x-value. You must ensure that the
        entered data is valid and can be drawn.

        Args:
            x: x-value that should be added to the buffer.
            y: y-value that should be added to the buffer.
            height: Height of the bar.
        """
        super().add_entry_to_buffer(primary_value=x, secondary_values=[y, height])

    @deprecated_param_alias(x_values="x", y_values="y")
    def add_list_of_entries(self, x: np.ndarray, y: np.ndarray, heights: np.ndarray):
        """
        Add a list of bars to the buffer.

        This method will also sort the buffer after inserting the values by the x-value.
        :obj:`~numpy.nan` are treated similarly to :func:`numpy.sort`, meaning they will be moved to the
        end of the array. If :obj:`~numpy.nan` values are to be stored at the specific positions, use
        :meth:`add_entry`.

        Args:
            x: Array of x-values that should be added to the buffer.
            y: Array of y-values that should be added to the buffer.
            heights: Array of the heights of the bars.
        """
        super().add_entries_to_buffer(primary_values=x, secondary_values_list=[y, heights])

    def subset_for_primary_val_range(self, start: float, end: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get slice of the data, ranging between the given start and end points.

        Args:
            start: Lower boundary of the subset.
            end: Upper boundary of the subset.

        Returns:
            Tuple of subsets for x-values, y-values and heights.
        """
        i = self.occupied_size
        x: np.ndarray = self._primary_values[:i]
        y: np.ndarray = self._secondary_values_lists[0][:i]
        height: np.ndarray = self._secondary_values_lists[1][:i]
        start_index = self._searchsorted_with_nans(array=x, value=start, side="left", contains_nan=self._contains_nan)
        end_index = self._searchsorted_with_nans(array=x, value=end, side="right", contains_nan=self._contains_nan)
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x,
            start_index=start_index,
            end_index=end_index,
        )
        return (
            x[start_index:end_index],
            y[start_index:end_index],
            height[start_index:end_index],
        )


class SortedInjectionBarsDataBuffer(BaseSortedDataBuffer):
    """
    Sorted buffer for an injection bar graph. Its contents are:

    * **primary**: x-position; **secondary**: [y-position, height, width, label]
    """

    def reset(self):
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
        # Label
        self._secondary_values_lists.append(np.empty(self._size, dtype="<U100"))

    @deprecated_param_alias(x_value="x", y_value="y")
    def add_entry(self, x: float, y: float, height: float, width: float, label: str):
        """
        Add a single injection bar to the buffer.

        This method will also sort the buffer after insertion by the x-value. You must ensure that the
        entered data is valid and can be drawn.

        Args:
            x: x-value that should be added to the buffer.
            y: y-value that should be added to the buffer.
            height: Height of the bar.
            width: Width of the bar.
            label: Text displayed next to the corresponding bar.
        """
        super().add_entry_to_buffer(
            primary_value=x,
            secondary_values=[y, height, width, label],
        )

    @deprecated_param_alias(x_values="x", y_values="y")
    def add_list_of_entries(
        self,
        x: np.ndarray,
        y: np.ndarray,
        heights: np.ndarray,
        widths: np.ndarray,
        labels: np.ndarray,
    ):
        """
        Add a list of injection bars to the buffer.

        This method will also sort the buffer after inserting the values by the x-value.
        :obj:`~numpy.nan` are treated similarly to :func:`numpy.sort`, meaning they will be moved to the
        end of the array. If :obj:`~numpy.nan` values are to be stored at the specific positions, use
        :meth:`add_entry`.

        Args:
            x: Array of x-values that should be added to the buffer.
            y: Array of y-values that should be added to the buffer.
            heights: Array of the heights of the bars.
            widths: Array of the widths of the bars.
            labels: Array of texts displayed next to each corresponding bar.
        """
        super().add_entries_to_buffer(
            primary_values=x,
            secondary_values_list=[y, heights, widths, labels],
        )

    def subset_for_primary_val_range(self, start: float, end: float) -> Tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """
        Get slice of the data, ranging between the given start and end points.

        Args:
            start: Lower boundary of the subset.
            end: Upper boundary of the subset.

        Returns:
            Tuple of subsets for x-values, y-values, heights, widths and labels.
        """
        i = self.occupied_size
        x: np.ndarray = self._primary_values[:i]
        y: np.ndarray = self._secondary_values_lists[0][:i]
        heights: np.ndarray = self._secondary_values_lists[1][:i]
        widths: np.ndarray = self._secondary_values_lists[2][:i]
        labels: np.ndarray = self._secondary_values_lists[3][:i]
        start_index = self._searchsorted_with_nans(array=x, value=start, side="left", contains_nan=self._contains_nan)
        end_index = self._searchsorted_with_nans(array=x, value=end, side="right", contains_nan=self._contains_nan)
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x,
            start_index=start_index,
            end_index=end_index,
        )
        return (
            x[start_index:end_index],
            y[start_index:end_index],
            heights[start_index:end_index],
            widths[start_index:end_index],
            labels[start_index:end_index],
        )


class SortedTimestampMarkerDataBuffer(BaseSortedDataBuffer):
    """
    Sorted buffer for a bar graph. Its contents are:

    * **primary**: x-position; **secondary**: [color, label]
    """

    def reset(self):
        super().reset()
        # X Value
        self._primary_values = np.empty(self._size)
        self._primary_values.fill(np.nan)
        # Color
        self._secondary_values_lists.append(np.empty(self._size, dtype="<U100"))
        # Label
        self._secondary_values_lists.append(np.empty(self._size, dtype="<U100"))

    @deprecated_param_alias(x_value="x")
    def add_entry(self, x: float, color: str, label: str):
        """
        Add a single timestamp marker to the buffer.

        This method will also sort the buffer after insertion by the x-value. You must ensure that the
        entered data is valid and can be drawn.

        Args:
            x: x-value that should be added to the buffer.
            color: Color of the corresponding infinite line.
            label: Text displayed next to the corresponding infinite line.
        """
        super().add_entry_to_buffer(primary_value=x, secondary_values=[color, label])

    @deprecated_param_alias(x_values="x")
    def add_list_of_entries(self, x: np.ndarray, colors: np.ndarray, labels: np.ndarray):
        """
        Add a list of timestamp markers to the buffer.

        This method will also sort the buffer after inserting the values by the x-value.
        :obj:`~numpy.nan` are treated similarly to :func:`numpy.sort`, meaning they will be moved to the
        end of the array. If :obj:`~numpy.nan` values are to be stored at the specific positions, use
        :meth:`add_entry`.

        Args:
            x: Array of x-values that should be added to the buffer.
            colors: Array of colors for each corresponding infinite line.
            labels: Array of text displayed next to each corresponding bar.
        """
        super().add_entries_to_buffer(primary_values=x, secondary_values_list=[colors, labels])

    def subset_for_primary_val_range(self, start: float, end: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get slice of the data, ranging between the given start and end points.

        Args:
            start: Lower boundary of the subset.
            end: Upper boundary of the subset.

        Returns:
            Tuple of subsets for x-values, colors and labels.
        """
        i = self.occupied_size
        x: np.ndarray = self._primary_values[:i]
        color: np.ndarray = self._secondary_values_lists[0][:i]
        label: np.ndarray = self._secondary_values_lists[1][:i]
        start_index = self._searchsorted_with_nans(array=x, value=start, side="left", contains_nan=self._contains_nan)
        end_index = self._searchsorted_with_nans(array=x, value=end, side="right", contains_nan=self._contains_nan)
        # indices for removing leading/trailing entries that have NaN as their primary value
        start_index, end_index = super()._get_indices_for_cutting_leading_and_trailing_nans(
            primary_values=x,
            start_index=start_index,
            end_index=end_index,
        )
        return (
            x[start_index:end_index],
            color[start_index:end_index],
            label[start_index:end_index],
        )
