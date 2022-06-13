import functools
import json
import warnings
from abc import ABC
from datetime import datetime
from dataclasses import dataclass
from copy import copy
from enum import IntEnum, auto
from pjlsa import LSAClient
from jpype import JException
from typing import Optional, Any, Dict, List, Union, Set, Iterable, cast
from qtpy.QtGui import QColor, QFont
from qtpy.QtCore import QAbstractTableModel, QObject, QModelIndex, Qt, QVariant, Signal, QSortFilterProxyModel
from qtpy.QtWidgets import QTableView
from accwidgets.designer_check import is_designer


class LsaSelectorAccelerator(IntEnum):
    """
    Enumeration of CERN accelerators available in LSA framework.

    * It does not include ``LINAC3`` (that was available in original LSA framework) because it is the part of :attr:`LEIR` now.
    * It does not include ``LINAC4`` (that was available in original LSA framework) because it is the part of :attr:`PSB` now.
    * ``REX`` has also been removed as obsolete.
    """
    # The above statements were reviewed by Roman Gorbonosov. The rest of the enum replicates Java's
    # cern.accsoft.commons.domain.CernAccelerator. NORTH has been left, even though it is invalid now, as it may
    # reappear in the future.

    AD = auto()
    """Antiproton Decelerator."""

    CTF = auto()
    """CLIC Test Facility."""

    ISOLDE = auto()
    """On-Line Isotope Mass Separator."""

    LEIR = auto()
    """Low Energy Ion Ring (includes LINAC3)."""

    LHC = auto()
    """Large Hadron Collider."""

    PS = auto()
    """Proton Synchrotron."""

    PSB = auto()
    """Proton Synchrotron Booster + Linear Accelerators (LINACs)."""

    SPS = auto()
    """Super Proton Synchrotron."""

    NORTH = auto()
    """SPS North Area"""

    AWAKE = auto()
    """Advanced Proton Driven Plasma Wakefield Acceleration Experiment."""

    ELENA = auto()
    """ELENA ring."""


@dataclass(frozen=True)
class LsaSelectorTooltipInfo:
    users: Set[str]
    name: str
    type_name: str
    length: int
    description: str
    multiplexed: bool
    created: datetime
    creator: str
    modified: datetime
    modifier: str
    id: int


@dataclass(frozen=True)
class AbstractLsaSelectorContext(ABC):
    """Base class for LSA context classes."""

    class Category(IntEnum):
        """Values used to categorize different contexts depending on their usage."""

        TEST = auto()
        """Test."""

        MD = auto()
        """Machine Development."""

        OPERATIONAL = auto()
        """Operational."""

        OBSOLETE = auto()
        """Obsolete."""

        ARCHIVED = auto()
        """Set of LSA settings that is archived can be used to restore the accelerator to a previously known state."""

        REFERENCE = auto()
        """Reference settings allow highlighting the differences between the current setup and some known state."""

    name: str
    """Name of the LSA cycle/context."""

    category: "AbstractLsaSelectorContext.Category"
    """Category of the context that can be used for filtering."""


@dataclass(frozen=True)
class LsaSelectorNonResidentContext(AbstractLsaSelectorContext):
    """Non-resident cycle is a cycle that is not associated or mapped to a timing user."""

    multiplexed: bool
    """Time-multiplexing or Pulse-to-Pulse Modulation (PPM) trait requires a selector as a key for accessing information."""

    can_become_resident: bool = False
    """
    Indicates if the specified beam process can become resident i.e. it is not yet resident, but belongs to an
    active hyper cycle and has a user mapped.
    """


@dataclass(frozen=True)
class AbstractLsaSelectorResidentContext(AbstractLsaSelectorContext):
    """
    Base class for resident context classes.

    Resident cycles are associated or mapped to a timing user.
    """

    user: str
    """
    Mapped timing user. This string is always stored in the complete format, e.g. ``LEI.USER.LIN3MEAS`` even if
    user displayed in the widget is ``LIN3MEAS``.
    """


@dataclass(frozen=True, init=False)
class LsaSelectorNonMultiplexedResidentContext(AbstractLsaSelectorResidentContext):
    """
    Resident context that is not time-multiplexed, i.e. does not use Pulse-to-Pulse Modulation (PPM).

    Non-multiplexed objects cannot accept selector as a key for accessing information and therefore must always
    operate with empty selectors.
    """

    user: str = ""
    """Mapped timing user is always empty for non-resident cycles."""

    def __init__(self, name: str, category: AbstractLsaSelectorContext.Category):
        super().__init__(name=name, category=category, user="")


@dataclass(frozen=True)
class LsaSelectorMultiplexedResidentContext(AbstractLsaSelectorResidentContext):
    """
    Resident context that is time-multiplexed, i.e. uses Pulse-to-Pulse Modulation (PPM).

    Multiplexed objects require a non-empty timing user to operate. Such context will always display a value in
    "TGM User" column of the :class:`LsaSelector`.
    """

    class UserType(IntEnum):
        """Type of the timing user for the given LSA cycle."""

        INACTIVE = auto()
        """LSA cycle is resident but not active."""

        ACTIVE_SPARE = auto()
        """LSA cycle is resident and active and is mapped to a spare timing user."""

        ACTIVE_NORMAL = auto()
        """LSA cycle is resident and active and is mapped to a normal timing user."""

    user_type: "LsaSelectorMultiplexedResidentContext.UserType"
    """Type of the timing user for the given LSA cycle."""


@dataclass(frozen=True)
class LsaSelectorRowViewModel:

    ctx: AbstractLsaSelectorContext
    tooltip: Optional[LsaSelectorTooltipInfo] = None


class LsaSelectorColorRole(IntEnum):
    """Roles used to access colors from the mapping when rendering a table of LSA cycles."""

    FG_USER = auto()
    """Foreground color of the "TGM User" column."""

    FG_CTX_RESIDENT_ACTIVE = auto()
    """Foreground color of the active resident cycles mapped to a normal timing user."""

    FG_CTX_RESIDENT_NORMAL = auto()
    """Foreground color of the inactive resident cycles."""

    FG_CTX_RESIDENT_SPARE = auto()
    """Foreground color of the active resident cycles mapped to a spare timing user."""

    FG_CTX_RESIDENT_NON_PPM = auto()
    """Foreground color of the non-multiplexed resident cycles."""

    FG_CTX_NON_RESIDENT_NON_PPM = auto()
    """Foreground color of the non-multiplexed non-resident cycles."""

    FG_CTX_NON_RESIDENT_NORMAL = auto()
    """Foreground color of the multiplexed non-resident cycles."""

    BG_CTX_RESIDENT = auto()
    """Background color of the resident cycles."""

    BG_CTX_NON_RESIDENT = auto()
    """Background color of the non-resident cycles."""

    BG_CTX_CAN_BE_RESIDENT = auto()
    """
    Background color of the non-resident cycles that can become resident
    (see :attr:`LsaSelectorNonResidentContext.can_become_resident`).
    """


Color = Union[Qt.GlobalColor, QColor]


ColorMap = Dict[LsaSelectorColorRole, QColor]


CONTEXT_TABLE_ROLE = Qt.UserRole + 324


class LsaSelectorModel(QObject):

    background_color_changed = Signal()
    """
    Signals when background color has changed. This is used to keep in sync the background of the resident cycles
    (defined inside the model, due to :class:`QAbstractItemModel` architecture) and the overall background color of
    the table, managed by the view (:class:`LsaSelector`).

    :type: pyqtSignal
    """

    title_filter_changed = Signal()
    """
    Notifies when the filter by context title has been updated.

    :type: pyqtSignal
    """

    category_filter_changed = Signal()
    """
    Notifies when the filter by context category has been updated.

    :type: pyqtSignal
    """

    lsa_error_received = Signal(str)
    """
    Indicates the problem while retrieving data from an LSA server. Error message is passed as an argument, but
    can also be accessed via :attr:`last_error`.

    :type: pyqtSignal
    """

    def __init__(self,
                 accelerator: LsaSelectorAccelerator = LsaSelectorAccelerator.LHC,
                 lsa: Optional[LSAClient] = None,
                 resident_only: bool = True,
                 categories: Optional[Set[AbstractLsaSelectorContext.Category]] = None,
                 parent: Optional[QObject] = None):
        """
        Model retrieves data an LSA server and stores it, managing filtering and necessary changes when relevant
        properties get updated. Stored data is wrapped inside custom data structures and is abstracted from
        LSA Java implementations.

        Args:
            accelerator: LSA accelerator to retrieve cycles for.
            lsa: Optional instance of :class:`~pjlsa.LSAClient`, in case there's a need to use a specific instance (e.g.
                 if a subclass is preferred, or it absolutely needs to operate on a singleton). If :obj:`None` provided,
                 a new instance is created with default arguments (i.e. GPN server).
            resident_only: Choice for retrieving only resident or all LSA cycles.
            categories: Choice to limit retrieved cycles to only specific context categories. If :obj:`None` is given,
                        only :attr:`~AbstractLsaSelectorContext.Category.OPERATIONAL` contexts will be fetched.
            parent: Owning object.
        """
        super().__init__(parent)
        self._acc = accelerator
        self._fetch_resident_only = resident_only
        self._fetch_categories = categories or {AbstractLsaSelectorContext.Category.OPERATIONAL}
        self._lsa: LSAClient = lsa or (LSAClient() if not is_designer() else None)
        self._rows: Optional[List[LsaSelectorRowViewModel]] = None
        self._last_error: Optional[str] = None
        default_bold = QFont(self.DEFAULT_FONT)
        default_bold.setBold(True)
        self._table_model = LsaSelectorTableModel(row_models=self._row_models,
                                                  color_map=self.DEFAULT_COLOR_MAP,
                                                  resident_font=default_bold,
                                                  non_resident_font=self.DEFAULT_FONT,
                                                  parent=self)
        self._table_filter = LsaSelectorFilterModel(parent=self)
        self._table_filter.setSourceModel(self._table_model)

    def _get_accelerator(self) -> LsaSelectorAccelerator:
        return self._acc

    def _set_accelerator(self, new_val: LsaSelectorAccelerator):
        if new_val == self._acc:
            return
        self._acc = new_val
        self.refetch()

    accelerator = property(fget=_get_accelerator, fset=_set_accelerator)
    """LSA accelerator to retrieve cycles for. Updating this property will automatically re-fetch data."""

    def _get_resident_only(self) -> bool:
        return self._fetch_resident_only

    def _set_resident_only(self, new_val: bool):
        if new_val == self._fetch_resident_only:
            return
        self._fetch_resident_only = new_val
        self.refetch()

    resident_only = property(fget=_get_resident_only, fset=_set_resident_only)
    """
    Choice for retrieving only resident or all LSA cycles.
    Updating this property will automatically re-fetch data.
    """

    def _get_categories(self) -> Set[AbstractLsaSelectorContext.Category]:
        return self._fetch_categories

    def _set_categories(self, new_val: Set[AbstractLsaSelectorContext.Category]):
        if new_val == self._fetch_categories:
            return
        self._fetch_categories = new_val
        self.refetch()

    categories = property(fget=_get_categories, fset=_set_categories)
    """
    Choice to limit cycles to only specific context categories. Updating this property will automatically re-fetch
    data. When intention is to only limit amount of displayed cycles from already fetched cycles, attribute
    :attr:`filter_categories` can be used instead.
    """

    def color(self, role: LsaSelectorColorRole) -> QColor:
        """
        Read out color for a specific role that is used in the LSA cycles table.

        Args:
            role: Role associated with the color of interest.

        Returns:
            Mapped color.
        """
        return self._table_model.color_map[role]

    def set_color(self, role: LsaSelectorColorRole, color: Color):
        """
        Update the color for the specific role that is used in the LSA cycles table.

        When the ``color`` is identical to already used, no action is taken, otherwise the table is reloaded
        (without re-fetching data from the server). If role is given as :attr:`LsaSelectorColorRole.BG_CTX_RESIDENT`,
        :attr:`background_color_changed` will be fired to synchronize the view.

        Args:
            role: Role associated with the color of interest.
            color: New color value.
        """
        if not isinstance(color, QColor):
            color = QColor(color)

        if color == self.color(role):
            return
        color_map = copy(self._table_model.color_map)
        color_map[role] = color
        self._table_model.color_map = color_map
        if role == LsaSelectorColorRole.BG_CTX_RESIDENT:
            self.background_color_changed.emit()

    def _get_resident_font(self) -> QFont:
        return self._table_model.resident_font

    def _set_resident_font(self, new_val: QFont):
        self._table_model.resident_font = new_val

    resident_font = property(fget=_get_resident_font, fset=_set_resident_font)
    """
    Font used to display resident cycles. Updating this property will reload the table (without re-fetching data
    from the server).
    """

    def _get_non_resident_font(self) -> QFont:
        return self._table_model.non_resident_font

    def _set_non_resident_font(self, new_val: QFont):
        self._table_model.non_resident_font = new_val

    non_resident_font = property(fget=_get_non_resident_font, fset=_set_non_resident_font)
    """
    Font used to display non-resident cycles. Updating this property will reload the table (without re-fetching data
    from the server).
    """

    def _get_filter_title(self) -> str:
        return self._table_filter.name_filter or ""

    def _set_fitler_title(self, new_val: str):
        if new_val == self._table_filter.name_filter:
            return
        self._table_filter.name_filter = new_val
        self.title_filter_changed.emit()

    filter_title = property(fget=_get_filter_title, fset=_set_fitler_title)
    """
    String used to filter displayed cycles by LSA context name. Updating this property to a different value will
    fire :attr:`title_filter_changed` signal.
    """

    def _get_filter_categories(self) -> Set[AbstractLsaSelectorContext.Category]:
        return self._table_filter.category_filter or set()

    def _set_filter_categories(self, new_val: Set[AbstractLsaSelectorContext.Category]):
        if new_val == self._table_filter.category_filter:
            return
        self._table_filter.category_filter = new_val
        self.category_filter_changed.emit()

    filter_categories = property(fget=_get_filter_categories, fset=_set_filter_categories)
    """
    Set of context categories used to limit the displayed cycles. As opposed to :attr:`categories`,
    it does not influence the fetched data, but rather narrows down the already retrieved cycles to even finer
    collection.
    """

    def refetch(self):
        """Force fetch the data from the servers even if it was already downloaded."""
        self._rows = None
        self._table_model.set_row_models(self._row_models)

    def connect_table(self, table: QTableView):
        """
        Connect table view with the model's internal table models.

        Args:
            table: Table to get connected to the model.
        """
        table.setModel(self._table_filter)

    def find_stored_categories(self) -> Set[AbstractLsaSelectorContext.Category]:
        """
        Convenience accessor to find out the context categories associated with the retrieved data.

        Returns:
            All categories associated with the contexts that have been retrieved from the server.
        """
        res = set()
        for row in self._row_models:
            res.add(row.ctx.category)
        return res

    @property
    def last_error(self) -> Optional[str]:
        """Error that was recorded last during the communication with the LSA server. If no error has occurred,
        this value is :obj:`None`."""
        return self._last_error

    @property
    def _row_models(self) -> List[LsaSelectorRowViewModel]:
        if self._rows is None:
            rows: Iterable[LsaSelectorRowViewModel]
            if is_designer():
                rows = sample_contexts_for_accelerator(accelerator=self._acc,
                                                       resident_only=self._fetch_resident_only,
                                                       categories=self._fetch_categories)
            else:
                try:
                    rows = contexts_for_accelerator(accelerator=self._acc,
                                                    lsa=self._lsa,
                                                    resident_only=self._fetch_resident_only,
                                                    categories=self._fetch_categories)
                except JException as e:
                    msg = e.getMessage()
                    self._last_error = msg
                    self.lsa_error_received.emit(msg)
                    return []
                self._last_error = None
            self._rows = sorted_row_models(rows)
        return self._rows

    # Corresponding to Java implementation: https://gitlab.cern.ch/acc-co/inca/lsa/-/blob/develop/lsa-gui/src/java/cern/lsa/gui/selection/context/StandAloneContextCellRenderer.java
    DEFAULT_COLOR_MAP = {
        LsaSelectorColorRole.FG_CTX_RESIDENT_NON_PPM: QColor("orange"),
        LsaSelectorColorRole.FG_CTX_RESIDENT_ACTIVE: QColor("lime"),
        LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.yellow),
        LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.cyan),
        LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NORMAL: QColor(Qt.black),
        LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(198, 102, 0),
        LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.black),
        LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.white),
        LsaSelectorColorRole.BG_CTX_CAN_BE_RESIDENT: QColor(200, 200, 200),
        LsaSelectorColorRole.FG_USER: QColor(Qt.white),
    }
    """Definition of colors used by default in the widgets. Custom colors can be injected via :meth:`set_color`."""

    DEFAULT_FONT = QFont("Helvetica", 8)
    """
    Definition of the default font used for non-resident cycles (resident cycles will be the same by bold).
    Custom fonts can be assigned via :attr:`resident_font` and :attr:`non_resident_font` properties.
    """


class LsaSelectorFilterModel(QSortFilterProxyModel):

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._name_filter: Optional[str] = None
        self._category_filter: Optional[Set[AbstractLsaSelectorContext.Category]] = None

    @property
    def name_filter(self) -> Optional[str]:
        return self._name_filter

    @name_filter.setter
    def name_filter(self, new_val: Optional[str]):
        if new_val == self._name_filter:
            return
        self._name_filter = new_val
        self.invalidateFilter()

    @property
    def category_filter(self) -> Optional[Set[AbstractLsaSelectorContext.Category]]:
        return copy(self._category_filter)

    @category_filter.setter
    def category_filter(self, new_val: Optional[Set[AbstractLsaSelectorContext.Category]]):
        if self._category_filter == new_val:
            return
        self._category_filter = new_val
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        index = self.sourceModel().index(source_row, 1)
        if self._category_filter:
            ctx: AbstractLsaSelectorContext = self.sourceModel().data(index, CONTEXT_TABLE_ROLE)
            if ctx.category not in self._category_filter:
                return False
        if self._name_filter:
            row: str = self.sourceModel().data(index)
            if self._name_filter.casefold() not in row.casefold():
                return False
        return True


class LsaSelectorTableModel(QAbstractTableModel):

    def __init__(self,
                 row_models: List[LsaSelectorRowViewModel],
                 color_map: ColorMap,
                 resident_font: QFont,
                 non_resident_font: QFont,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self._data = row_models
        self._color_map = color_map
        self._resident_font = resident_font
        self._non_resident_font = non_resident_font

    def set_row_models(self, new_val: List[LsaSelectorRowViewModel]):
        if new_val == self._data:
            return
        self.beginResetModel()
        self._data = new_val
        self.endResetModel()

    @property
    def color_map(self) -> ColorMap:
        return self._color_map

    @color_map.setter
    def color_map(self, new_val: ColorMap):
        if new_val == self._color_map:
            return
        self.beginResetModel()
        self._color_map = new_val
        self.endResetModel()

    @property
    def resident_font(self) -> QFont:
        return self._resident_font

    @resident_font.setter
    def resident_font(self, new_val: QFont):
        if new_val == self._resident_font:
            return
        self.beginResetModel()
        self._resident_font = new_val
        self.endResetModel()

    @property
    def non_resident_font(self) -> QFont:
        return self._non_resident_font

    @non_resident_font.setter
    def non_resident_font(self, new_val: QFont):
        if new_val == self._non_resident_font:
            return
        self.beginResetModel()
        self._non_resident_font = new_val
        self.endResetModel()

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
        """
        Returns the data for the given role and section in the header with the specified orientation.

        For horizontal headers, the section number corresponds to the column number. Similarly,
        for vertical headers, the section number corresponds to the row number.

        Args:
            section: column / row of which the header data should be returned
            orientation: Columns / Row
            role: Not used by this implementation, if not DisplayRole, super
                  implementation is called

        Returns:
            Header Data (e.g. name) for the row / column
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return " TGM User "
            else:
                return " LSA Context "
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        """
        Get Data from the table's model by a given index.

        Args:
            index: row & column in the table
            role: which property is requested

        Returns:
            Data associated with the passed index
        """
        if (not index.isValid()
                or role not in [Qt.DisplayRole, Qt.BackgroundRole, Qt.ForegroundRole,
                                Qt.FontRole, Qt.ToolTipRole, CONTEXT_TABLE_ROLE]
                or index.row() >= len(self._data)):
            return QVariant()
        row = self._data[index.row()]
        if role == Qt.FontRole:
            if isinstance(row.ctx, AbstractLsaSelectorResidentContext):
                return self._resident_font
            else:
                return self._non_resident_font
        if role == Qt.DisplayRole:
            if index.column() == 0:
                if isinstance(row.ctx, AbstractLsaSelectorResidentContext):
                    return row.ctx.user.split(".")[-1]
                else:
                    return ""
            else:
                return row.ctx.name
        elif role == Qt.BackgroundRole:
            if isinstance(row.ctx, LsaSelectorNonResidentContext):
                if row.ctx.can_become_resident:
                    return self._color_map[LsaSelectorColorRole.BG_CTX_CAN_BE_RESIDENT]
                else:
                    return self._color_map[LsaSelectorColorRole.BG_CTX_NON_RESIDENT]
            else:
                return self._color_map[LsaSelectorColorRole.BG_CTX_RESIDENT]
        elif role == Qt.ForegroundRole:
            if index.column() == 0:
                return self._color_map[LsaSelectorColorRole.FG_USER]
            else:
                color_role: LsaSelectorColorRole
                if isinstance(row.ctx, LsaSelectorMultiplexedResidentContext):
                    if row.ctx.user_type == LsaSelectorMultiplexedResidentContext.UserType.INACTIVE:
                        color_role = LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL
                    elif row.ctx.user_type == LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE:
                        color_role = LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE
                    elif row.ctx.user_type == LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL:
                        color_role = LsaSelectorColorRole.FG_CTX_RESIDENT_ACTIVE
                    else:
                        return QVariant()
                elif isinstance(row.ctx, LsaSelectorNonMultiplexedResidentContext):
                    color_role = LsaSelectorColorRole.FG_CTX_RESIDENT_NON_PPM
                else:
                    color_role = (LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NORMAL if row.ctx.multiplexed
                                  else LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM)
                return self._color_map[color_role]
        elif role == Qt.ToolTipRole:
            if row.tooltip is not None:
                return format_tooltip({
                    "Name": row.tooltip.name,
                    "Type Name": row.tooltip.type_name,
                    "Length": str(row.tooltip.length),
                    "Description": row.tooltip.description,
                    "Users": f"[{'non-multiplexed' if not row.tooltip.multiplexed else ','.join(row.tooltip.users)}]",
                    "Multiplexed": json.dumps(row.tooltip.multiplexed),
                    "Created": row.tooltip.created.isoformat(sep=" ", timespec="milliseconds"),
                    "Creator": row.tooltip.creator or "",
                    "Last Modified": row.tooltip.modified.isoformat(sep=" ", timespec="milliseconds"),
                    "Modified by": row.tooltip.modifier or "",
                    "Id": str(row.tooltip.id),
                })
        elif role == CONTEXT_TABLE_ROLE:
            return row.ctx
        return QVariant()

    def rowCount(self, _: Optional[QModelIndex] = None) -> int:
        return len(self._data)

    def columnCount(self, _: Optional[QModelIndex] = None) -> int:
        return 2


def format_tooltip(pairs: Dict[str, str]):
    return "<table>" + "".join(("<tr>"
                                f'<td align="right"><b>{k}:</b></td>'
                                f"<td>{v}</td>"
                                "</tr>" for k, v in pairs.items())) + "</table>"


def sorted_row_models(input: Iterable[LsaSelectorRowViewModel]) -> List[LsaSelectorRowViewModel]:

    def comparator(left, right):

        def compare(lhs: Any, rhs: Any) -> int:
            # Inspired by SO: https://stackoverflow.com/a/1144405
            return (lhs > rhs) - (lhs < rhs)

        def compare_by_status(lhs: LsaSelectorRowViewModel, rhs: LsaSelectorRowViewModel) -> int:

            def get_weight(ctx: AbstractLsaSelectorContext) -> int:
                weight = 0
                if isinstance(ctx, AbstractLsaSelectorResidentContext):
                    weight += 10
                    if isinstance(ctx, LsaSelectorMultiplexedResidentContext):
                        weight += 10
                        weight += ctx.user_type.value * 10
                elif isinstance(ctx, LsaSelectorNonResidentContext):
                    if ctx.can_become_resident:
                        weight += 5
                    if ctx.multiplexed:
                        weight += 1
                return weight

            return compare(get_weight(rhs.ctx), get_weight(lhs.ctx))

        def compare_by_name(lhs: LsaSelectorRowViewModel, rhs: LsaSelectorRowViewModel) -> int:
            return compare(lhs.ctx.name, rhs.ctx.name)

        compare_results = (compare(left, right) for compare in [compare_by_status, compare_by_name])
        return next((res for res in compare_results if res), 0)

    return sorted(input, key=functools.cmp_to_key(comparator))


def contexts_for_accelerator(accelerator: LsaSelectorAccelerator,
                             lsa: LSAClient,
                             resident_only: bool,
                             categories: Set[AbstractLsaSelectorContext.Category]) -> Iterable[LsaSelectorRowViewModel]:
    with lsa.java_api():
        from java.util import Collection
        from cern.accsoft.commons.domain import CernAccelerator
        from cern.lsa.client import ServiceLocator, ContextService, HyperCycleService
        from cern.lsa.domain.settings import DrivableContext, Contexts, ContextFamily, StandAloneCycle, StandAloneBeamProcess, HyperCycle

        ctx_mapping: Dict[LsaSelectorAccelerator, CernAccelerator] = {
            LsaSelectorAccelerator.AD: CernAccelerator.AD,
            LsaSelectorAccelerator.CTF: CernAccelerator.CTF,
            LsaSelectorAccelerator.ISOLDE: CernAccelerator.ISOLDE,
            LsaSelectorAccelerator.LEIR: CernAccelerator.LEIR,
            LsaSelectorAccelerator.LHC: CernAccelerator.LHC,
            LsaSelectorAccelerator.PS: CernAccelerator.PS,
            LsaSelectorAccelerator.PSB: CernAccelerator.PSB,
            LsaSelectorAccelerator.SPS: CernAccelerator.SPS,
            LsaSelectorAccelerator.AWAKE: CernAccelerator.AWAKE,
            LsaSelectorAccelerator.ELENA: CernAccelerator.ELENA,
            LsaSelectorAccelerator.NORTH: CernAccelerator.NORTH,
        }
        try:
            acc = ctx_mapping[accelerator]
        except KeyError:
            raise ValueError(f"Unknown LSA accelerator '{accelerator!s}'.")

        service = ServiceLocator.getService(ContextService)
        contexts: Collection[StandAloneCycle] = service.findStandAloneCycles(acc)
        if resident_only:
            contexts = Contexts.filterResidentContexts(contexts, True)

        if categories:
            category_names = [c.name for c in categories]
            filter_categories = [c for c in service.findContextCategories() if c.getName() in category_names]
            contexts = Contexts.filterByCategories(contexts, filter_categories)

        drivable_contexts = Contexts.getDrivableContexts(contexts)  # type: ignore  # mypy fails to agree that StandAloneCycle is a decsendant of Context
        active_users = service.findActiveTimingUsers(acc)

        active_hypercycle: Optional[HyperCycle] = None
        hypercycle_read: bool = False

        def find_active_hypercycle() -> Optional[HyperCycle]:
            nonlocal active_hypercycle
            nonlocal hypercycle_read
            if not hypercycle_read:
                hypercycle_read = True
                active_hypercycle = ServiceLocator.getService(HyperCycleService).findActiveHyperCycle()
            return active_hypercycle

        def can_become_resident(ctx: StandAloneBeamProcess) -> bool:
            hc = find_active_hypercycle()
            if hc is None:
                return False
            else:
                return Contexts.canBecomeResident(ctx, hc)

        def map_drivable_context(drivable: DrivableContext) -> LsaSelectorRowViewModel:
            lsa_name = drivable.getName()
            standalone = Contexts.getStandAloneContext(drivable)
            if standalone is None:
                raise RuntimeError("Drivable context is expected to belong to standalone context in this scenario.")
            category: AbstractLsaSelectorContext.Category
            category_name = standalone.getContextCategory().getName()
            try:
                category = AbstractLsaSelectorContext.Category[category_name]
            except KeyError:
                warnings.warn(f'Context category "{category_name}" is not supported by {LsaSelectorModel.__name__}'
                              f'. Context "{lsa_name}" will be assigned '
                              f'"{AbstractLsaSelectorContext.Category.OPERATIONAL.name}" category.')
                category = AbstractLsaSelectorContext.Category.OPERATIONAL

            extra_info = LsaSelectorTooltipInfo(name=lsa_name,
                                                type_name=drivable.getTypeName(),
                                                length=drivable.getLength(),
                                                description=drivable.getDescription(),
                                                multiplexed=drivable.isMultiplexed(),
                                                created=datetime.fromtimestamp(drivable.getCreationDate().getTime() / 1000),
                                                creator=drivable.getCreatorName(),
                                                modified=datetime.fromtimestamp(drivable.getModificationDate().getTime() / 1000),
                                                modifier=drivable.getModifierName(),
                                                id=drivable.getId(),
                                                users=set(Contexts.getUsers(standalone)))

            ctx: AbstractLsaSelectorContext
            is_beam_process = standalone.getContextFamily() == ContextFamily.BEAMPROCESS
            if is_beam_process and can_become_resident(cast(StandAloneBeamProcess, standalone)):
                ctx = LsaSelectorNonResidentContext(name=lsa_name,
                                                    multiplexed=drivable.isMultiplexed(),
                                                    category=category,
                                                    can_become_resident=True)
            else:
                if standalone.isResident():
                    if drivable.isMultiplexed():
                        user = drivable.getUser()
                        user_name = user.split(".")[-1]
                        user_type: LsaSelectorMultiplexedResidentContext.UserType
                        if not is_beam_process and active_users.contains(user_name):
                            if active_users.getNormalUsers().contains(user_name):
                                user_type = LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL
                            elif active_users.getSpareUsers().contains(user_name):
                                user_type = LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE
                            else:
                                user_type = LsaSelectorMultiplexedResidentContext.UserType.INACTIVE
                        else:
                            user_type = LsaSelectorMultiplexedResidentContext.UserType.INACTIVE

                        ctx = LsaSelectorMultiplexedResidentContext(name=lsa_name,
                                                                    user=user,
                                                                    user_type=user_type,
                                                                    category=category)
                    else:
                        ctx = LsaSelectorNonMultiplexedResidentContext(name=lsa_name, category=category)
                else:
                    ctx = LsaSelectorNonResidentContext(name=lsa_name,
                                                        multiplexed=drivable.isMultiplexed(),
                                                        category=category)
            return LsaSelectorRowViewModel(ctx=ctx, tooltip=extra_info)

        return map(map_drivable_context, drivable_contexts)


def sample_contexts_for_accelerator(accelerator: LsaSelectorAccelerator,
                                    resident_only: bool,
                                    categories: Set[AbstractLsaSelectorContext.Category]) -> List[LsaSelectorRowViewModel]:
    res: List[LsaSelectorRowViewModel] = []
    if not categories or (AbstractLsaSelectorContext.Category.OPERATIONAL in categories):
        res.extend([
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1_spare",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="_ZERO_",
                user="LEI.USER.ZERO",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
                name=f"_NON_MULTIPLEXED_{accelerator.name.upper()}",
                category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
            )),
        ])
    if not categories or (AbstractLsaSelectorContext.Category.MD in categories):
        res.append(LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )))
    if not resident_only:
        if not categories or (AbstractLsaSelectorContext.Category.OPERATIONAL in categories):
            res.extend([
                LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                    name="STANDALONE_NON_RESIDENT_OP",
                    multiplexed=True,
                    category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
                )),
                LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                    name="_NON_PPM_NON_RESIDENT_OP",
                    multiplexed=False,
                    category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
                )),
                LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                    name="_NON_PPM_CAN_BE_RESIDENT_OP",
                    multiplexed=False,
                    can_become_resident=True,
                    category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
                )),
                LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                    name="BP_CAN_BE_RESIDENT_OP",
                    multiplexed=True,
                    can_become_resident=True,
                    category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
                )),
            ])
        if not categories or (AbstractLsaSelectorContext.Category.MD in categories):
            res.append(LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="STANDALONE_NON_RESIDENT_MD",
                multiplexed=True,
                category=LsaSelectorNonResidentContext.Category.MD,
            )))
        if not categories or (AbstractLsaSelectorContext.Category.OBSOLETE in categories):
            res.append(LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="STANDALONE_NON_RESIDENT_OBS",
                multiplexed=True,
                category=LsaSelectorNonResidentContext.Category.OBSOLETE,
            )))
        if not categories or (LsaSelectorNonResidentContext.Category.REFERENCE in categories):
            res.append(LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="STANDALONE_NON_RESIDENT_REF",
                multiplexed=True,
                category=LsaSelectorNonResidentContext.Category.REFERENCE,
            )))
        if not categories or (AbstractLsaSelectorContext.Category.TEST in categories):
            res.append(LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="STANDALONE_NON_RESIDENT_TEST",
                multiplexed=True,
                category=LsaSelectorNonResidentContext.Category.TEST,
            )))
        if not categories or (AbstractLsaSelectorContext.Category.ARCHIVED in categories):
            res.append(LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="STANDALONE_NON_RESIDENT_ARCH",
                multiplexed=True,
                category=AbstractLsaSelectorContext.Category.ARCHIVED,
            )))
    return res
