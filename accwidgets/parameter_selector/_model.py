import operator
from asyncio import Future
try:
    from asyncio import create_task
except ImportError:
    from asyncio import ensure_future as create_task  # type: ignore
from typing import Optional, List, TypeVar, Tuple, Any, Union, cast, AsyncIterator, AsyncGenerator
from qtpy.QtCore import (Signal, QModelIndex, QObject, QIdentityProxyModel, QAbstractItemModel, Qt, QVariant,
                         QSignalBlocker, QItemSelectionModel, QAbstractListModel)
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QListView
from pyccda import AsyncAPI as CCDA


_T = TypeVar("_T")


SearchResultsModelSubTree = List[Tuple[str, List[str]]]
SearchResultsModelTree = List[Tuple[str, SearchResultsModelSubTree]]


class SearchResultsModel(QAbstractListModel):

    loading_state_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._data: SearchResultsModelTree = []
        self._is_loading = False
        self._iter_exhausted = False
        self._iter: Optional[AsyncIterator] = None
        self._active_task: Optional[Future] = None

    def set_data(self, iter: AsyncIterator[SearchResultsModelTree], first_batch: Optional[SearchResultsModelTree]):
        self.cancel_active_requests()
        self._iter = None  # Keep here so that trigger_row_update does not trigger next loading, we do it manually
        self._iter_exhausted = first_batch is None
        self.beginResetModel()
        self._data.clear()
        self.endResetModel()
        self._trigger_row_update(new_data=first_batch, loading=False)
        self._iter = iter
        if self.canFetchMore(QModelIndex()):
            self.fetchMore(QModelIndex())

    def cancel_active_requests(self):
        if self._active_task:
            self._active_task.cancel()
            self._active_task = None
        self._set_loading(False)

    def canFetchMore(self, parent: QModelIndex) -> bool:
        if self.is_loading:
            return False
        return not self._iter_exhausted and self._iter is not None

    def fetchMore(self, parent: QModelIndex):
        if self.is_loading:
            return
        self._active_task = create_task(self._do_fetch_more())

    def index(self, row: int, column: int, *_) -> QModelIndex:
        return self.createIndex(row, column)

    def rowCount(self, *_) -> int:
        return 1

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.DisplayRole:
            return QVariant()
        return self._data

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemNeverHasChildren
        return super().flags(index)

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        return QVariant()

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    def _set_loading(self, new_val: bool):
        if self._is_loading == new_val:
            return
        self._is_loading = new_val
        self.loading_state_changed.emit(new_val)

    async def _do_fetch_more(self):
        if self._iter is None:
            return
        self._trigger_row_update(loading=True)
        try:
            next_batch = await self._iter.__anext__()
        except StopAsyncIteration:
            self._iter_exhausted = True
            next_batch = None
        self._active_task = None
        self._trigger_row_update(loading=False, new_data=next_batch)

    def _trigger_row_update(self, new_data: Optional[SearchResultsModelTree] = None, loading: Optional[bool] = None):
        if new_data is None and (loading is None or loading == self.is_loading):
            return

        # In this method, we avoid using (begin)ResetModel() because it invalidates selected rows, which collide
        # with user browsing during loading. In addition, it triggers fetchMore, which results in data loading
        # all the way until the end is reached. Instead, we combined removeRows and insertRows to achieve the update.

        # Remove the loading row before appending
        start_idx = len(self._data)
        if self.is_loading:
            self.beginRemoveRows(QModelIndex(), start_idx, start_idx)
            self._set_loading(False)
            self.endRemoveRows()

        if new_data is not None:
            self.beginInsertRows(QModelIndex(), start_idx, start_idx + len(new_data) - 1)
            self._data.extend(new_data)
            self.endInsertRows()
            start_idx = len(self._data)

        if loading:
            self.beginInsertRows(QModelIndex(), start_idx, start_idx)
            self._set_loading(True)
            self.endInsertRows()


class SearchProxyModel(QIdentityProxyModel):

    selection_changed = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.selected_idx = -1

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        if role not in [self._LIST_ROLE, Qt.DisplayRole] or not index.isValid():
            return super().data(index, role)

        src = self.sourceModel()
        if not src:
            return QVariant()

        if isinstance(src, SearchProxyModel):
            data = src.index(src.selected_idx, 0).data(self._LIST_ROLE)
        else:
            data = src.index(0, 0).data()  # Root model, returns the full list

        try:
            data_item = data[index.row()]  # ('name', [list of items])
        except (IndexError, TypeError):
            return QVariant()

        if role == self._LIST_ROLE:
            if isinstance(data_item, tuple):
                return data_item[1]
            return QVariant()
        else:
            # Assuming Qt.DisplayRole
            if isinstance(data_item, tuple):
                return data_item[0]
            return data_item  # leaf, so it's gonna be a string

    def rowCount(self, *_) -> int:
        src = self.sourceModel()
        if not src:
            return 0

        if isinstance(src, SearchProxyModel):
            data = src.index(src.selected_idx, 0).data(self._LIST_ROLE)
        else:
            data = src.index(0, 0).data()  # Root model, returns the full list
        if data is None:
            return 0
        return len(data)

    def setSourceModel(self, sourceModel: QAbstractItemModel) -> None:
        self.beginResetModel()
        prev_src = self.sourceModel()
        if prev_src:
            if isinstance(prev_src, SearchProxyModel):
                prev_src.selection_changed.disconnect(self.reset_selected_idx)
            else:
                prev_src.modelReset.disconnect(self.reset_selected_idx)
        super().setSourceModel(sourceModel)
        if isinstance(sourceModel, SearchProxyModel):
            sourceModel.selection_changed.connect(self.reset_selected_idx)
        else:
            sourceModel.modelReset.connect(self.reset_selected_idx)
        self.endResetModel()

    def update_selection(self, new_index: Union[QModelIndex, int]):
        row = new_index.row() if isinstance(new_index, QModelIndex) else new_index
        if row >= self.rowCount():
            return
        self.selected_idx = row
        self.selection_changed.emit()

    def reset_selected_idx(self):
        self.beginResetModel()
        if self.rowCount() == 0:
            self.selected_idx = -1
        else:
            self.selected_idx = 0
        self.endResetModel()
        self.selection_changed.emit()

    def install(self, list: QListView):

        def highlight_selected_index():
            blocker = QSignalBlocker(list.selectionModel())
            index = self.createIndex(self.selected_idx, 0)
            list.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectCurrent)
            list.scrollTo(index, QListView.EnsureVisible)
            blocker.unblock()

        list.setModel(self)
        highlight_selected_index()
        self.selection_changed.connect(highlight_selected_index)
        list.selectionModel().currentRowChanged.connect(self.update_selection)

    _LIST_ROLE = Qt.UserRole + 60


class ExtendableProxyModel(SearchProxyModel):

    def canFetchMore(self, parent: QModelIndex) -> bool:
        try:
            return self.sourceModel().canFetchMore(parent)
        except AttributeError:
            return False

    def fetchMore(self, parent: QModelIndex):
        try:
            self.sourceModel().fetchMore(parent)
        except AttributeError:
            pass

    def rowCount(self, *args) -> int:
        real_count = super().rowCount(args)
        src = cast(SearchResultsModel, self.sourceModel())
        return real_count + 1 if src and src.is_loading else real_count

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        if (index.row() == self.rowCount() - 1
                and self.sourceModel() and cast(SearchResultsModel, self.sourceModel()).is_loading):
            if role == Qt.DisplayRole:
                return "Loading more..."
            elif role == Qt.FontRole:
                font = cast(QFont, super().data(index, role))
                font = font or QFont()
                font.setItalic(True)
                return font
        return super().data(index, role)

    def flags(self, index: QModelIndex):
        orig_flags = super().flags(index)

        if (index.row() == self.rowCount() - 1 and self.sourceModel()
                and cast(SearchResultsModel, self.sourceModel()).is_loading):
            return orig_flags ^ Qt.ItemIsSelectable
        return orig_flags


_ccda: Optional[CCDA] = None
_CCDA_PAGINATION_SIZE = 5


def get_ccda() -> CCDA:
    global _ccda
    if _ccda is None:
        _ccda = CCDA()
    return _ccda


async def _look_up_ccda(device_name: str) -> Tuple[AsyncIterator[SearchResultsModelTree], Optional[SearchResultsModelTree]]:
    device_pages = await get_ccda().Device.search('name=="*{dev}*"'.format(dev=device_name))

    async def wrapper() -> AsyncGenerator[SearchResultsModelTree, None]:

        def map_result(dev: CCDA.Device, dev_class: CCDA.DeviceClass) -> Tuple[str, SearchResultsModelSubTree]:
            subtree = []
            for prop in sorted(dev_class.device_class_properties, key=operator.attrgetter("name")):
                fields = sorted((field.name for field in prop.data_fields))
                subtree.append((prop.name, fields))

            return (dev.name, subtree)

        cnt = 0
        results = []
        async for device in device_pages:
            results.append(map_result(dev=device, dev_class=await device.device_class()))
            cnt += 1
            if cnt >= _CCDA_PAGINATION_SIZE:
                cnt = 0
                yield results
                results = []
        else:
            yield results

    generator = wrapper()
    iter = generator.__aiter__()
    first_batch: Optional[SearchResultsModelTree]
    try:
        first_batch = await iter.__anext__()
    except StopAsyncIteration:
        first_batch = None

    return iter, first_batch


def look_up_ccda(device_name: str) -> Future:
    return create_task(_look_up_ccda(device_name))
