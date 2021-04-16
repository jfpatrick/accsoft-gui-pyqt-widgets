import operator
from asyncio import Future
try:
    from asyncio import create_task
except ImportError:
    from asyncio import ensure_future as create_task  # type: ignore
from typing import Optional, List, TypeVar, Tuple, Any, Union
from qtpy.QtCore import (Signal, QModelIndex, QObject, QIdentityProxyModel, QAbstractItemModel, Qt, QVariant,
                         QSignalBlocker, QItemSelectionModel, QAbstractListModel)
from qtpy.QtWidgets import QListView
from pyccda import AsyncAPI as CCDA


_T = TypeVar("_T")


SearchResultsModelSubTree = List[Tuple[str, List[str]]]
SearchResultsModelTree = List[Tuple[str, SearchResultsModelSubTree]]


class SearchResultsModel(QAbstractListModel):

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._data: SearchResultsModelTree = []

    def set_data(self, new_val: SearchResultsModelTree):
        self.beginResetModel()
        self._data = new_val
        self.endResetModel()

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
        self.selected_idx = new_index.row() if isinstance(new_index, QModelIndex) else new_index
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


_ccda: Optional[CCDA] = None


def get_ccda() -> CCDA:
    global _ccda
    if _ccda is None:
        _ccda = CCDA()
    return _ccda


async def _look_up_ccda(device_name: str) -> SearchResultsModelTree:
    device_pages = await get_ccda().Device.search('name=="*{dev}*"'.format(dev=device_name))

    def map_result(dev: CCDA.Device, dev_class: CCDA.DeviceClass) -> Tuple[str, SearchResultsModelSubTree]:
        subtree = []
        for prop in sorted(dev_class.device_class_properties, key=operator.attrgetter("name")):
            fields = sorted((field.name for field in prop.data_fields))
            subtree.append((prop.name, fields))

        return (dev.name, subtree)

    return [map_result(dev=device, dev_class=await device.device_class())
            async for device in device_pages]


def look_up_ccda(device_name: str) -> Future:
    return create_task(_look_up_ccda(device_name))
