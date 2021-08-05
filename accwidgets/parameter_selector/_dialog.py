import logging
import functools
import asyncio
from asyncio import Future, CancelledError
from enum import IntEnum
from copy import copy
from typing import Optional, List, cast
from pathlib import Path
from qtpy.uic import loadUi
from qtpy.QtCore import Qt, QStringListModel, QModelIndex, QItemSelectionModel
from qtpy.QtGui import QKeyEvent, QHideEvent
from qtpy.QtWidgets import (QWidget, QDialog, QVBoxLayout, QPushButton, QLineEdit, QLabel, QStackedWidget,
                            QGroupBox, QListView, QComboBox, QDialogButtonBox)
from accwidgets._async_utils import install_asyncio_event_loop
from accwidgets.qt import ActivityIndicator
from ._name import ParameterName
from ._model import DeviceListModel, NestedListRootItem, look_up_ccda


logger = logging.getLogger(__name__)


class ParameterSelector(QWidget):

    class NetworkRequestStatus(IntEnum):
        COMPLETE = 0
        IN_PROGRESS = 1
        FAILED = 2

    def __init__(self, enable_protocols: bool, no_protocol_option: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        install_asyncio_event_loop()

        self._enable_protocols = enable_protocols
        self._selected_value = make_empty_addr()

        self.search_btn: QPushButton = None
        self.search_edit: QLineEdit = None
        self.selector_label: QLabel = None
        self.stack_widget: QStackedWidget = None
        self.results_group: QGroupBox = None
        self.device_list: QListView = None
        self.field_list: QListView = None
        self.prop_list: QListView = None
        self.cancel_btn: QPushButton = None
        self.err_label: QLabel = None
        self.protocol_combo: QComboBox = None
        self.protocol_group: QGroupBox = None
        self.activity_indicator: ActivityIndicator = None  # type: ignore

        loadUi(Path(__file__).parent / "selector.ui", self)

        self._search_results_model = DeviceListModel(self)
        self._requested_device: str = ""
        self._curr_search_status = ParameterSelector.NetworkRequestStatus.FAILED
        self._prev_search_status = ParameterSelector.NetworkRequestStatus.FAILED
        self._search_results: List[NestedListRootItem] = []
        self._active_ccda_task: Optional[Future] = None

        self.device_list.setModel(QStringListModel(self))
        self.prop_list.setModel(QStringListModel(self))
        self.field_list.setModel(QStringListModel(self))

        # Protocol selector
        if enable_protocols:
            self.protocol_combo.addItem(no_protocol_option, "")
            for proto in _KNOWN_PROTOCOLS:
                self.protocol_combo.addItem(proto.upper(), proto)

            self.protocol_combo.activated.connect(self._on_protocol_selected)
        else:
            self.protocol_group.hide()

        # Parameter name selector
        self.device_list.activated.connect(self._search_results_model.root_item_selection_changed)
        self.device_list.clicked.connect(self._search_results_model.root_item_selection_changed)
        self.prop_list.activated.connect(self._search_results_model.intermediate_item_selection_changed)
        self.prop_list.clicked.connect(self._search_results_model.intermediate_item_selection_changed)
        self.field_list.activated.connect(self._search_results_model.leaf_selection_changed)
        self.field_list.clicked.connect(self._search_results_model.leaf_selection_changed)
        self._search_results_model.root_items_changed.connect(functools.partial(self._on_list_changed, list_view=self.device_list))
        self._search_results_model.intermediate_items_changed.connect(functools.partial(self._on_list_changed, list_view=self.prop_list))
        self._search_results_model.leafs_changed.connect(functools.partial(self._on_list_changed, list_view=self.field_list))
        self._search_results_model.result_changed.connect(self._on_result_changed)

        # Search
        self.search_edit.textChanged.connect(self._on_device_search_changed)
        self.search_edit.returnPressed.connect(self._start_search)
        self.search_btn.clicked.connect(self._start_search)
        self.cancel_btn.clicked.connect(self._cancel_running_tasks)

        # Initially error page displays suggestion to start the search
        self._update_from_status(ParameterSelector.NetworkRequestStatus.FAILED)
        self._on_device_search_changed("")
        self._search_results_model.set_data([])

    @property
    def value(self) -> str:
        return str(self._selected_value)

    @value.setter
    def value(self, new_val: str):
        new_addr: Optional[ParameterName]
        if not new_val:
            new_addr = make_empty_addr()
        else:
            new_addr = ParameterName.from_string(new_val)
        if new_addr is None:
            return

        self._selected_value = new_addr

        # Adjust protocol
        if self._enable_protocols:
            parsed_proto = self._selected_value.protocol
            if parsed_proto:
                proto_idx = self.protocol_combo.findData(parsed_proto)
                if proto_idx == -1:
                    self._selected_value.protocol = None
                else:
                    self.protocol_combo.setCurrentIndex(proto_idx)
        else:
            self._selected_value.protocol = None

        device_addr = copy(self._selected_value)
        device_addr.protocol = None
        final_addr = str(device_addr)
        self.selector_label.setText(self.value)
        self.search_edit.setText(final_addr)
        self._start_search()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            event.accept()
            return
        super().keyPressEvent(event)

    def hideEvent(self, event: QHideEvent):
        super().hideEvent(event)
        self._cancel_running_tasks()

    def _on_device_search_changed(self, search_string: str):
        self.search_btn.setEnabled(len(search_string) > 0)

    def _on_protocol_selected(self):
        text: str = self.protocol_combo.currentData()
        self._selected_value.protocol = text.lower() or None
        self.selector_label.setText(self.value)

    def _on_list_changed(self, items: List[str], selected_index: QModelIndex, list_view: QListView):
        cast(QStringListModel, list_view.model()).setStringList(items)
        list_view.setEnabled(len(items) > 0)
        list_view.setCurrentIndex(selected_index)
        list_view.selectionModel().select(selected_index, QItemSelectionModel.Select)
        list_view.setFocus(Qt.ActiveWindowFocusReason)

    def _on_result_changed(self, result: str):
        parsed = ParameterName.from_string(result)
        if parsed is None:
            return

        self._selected_value.device = parsed.device
        self._selected_value.prop = parsed.prop
        self._selected_value.field = parsed.field

        # When setting from CCDB, assume no service
        if self._selected_value.service:
            self._selected_value.service = None
        self.selector_label.setText(self.value)

    def _start_search(self):
        asyncio.create_task(self._on_search_requested(self.search_edit.text()))

    def _update_from_status(self, status: "ParameterSelector.NetworkRequestStatus"):
        in_progress = status == ParameterSelector.NetworkRequestStatus.IN_PROGRESS
        if in_progress:
            self.activity_indicator.startAnimation()
        else:
            self.activity_indicator.stopAnimation()
        self.stack_widget.setCurrentIndex(status.value)
        self.search_edit.setEnabled(not in_progress)
        self.search_btn.setEnabled(not in_progress)

        # Disable these to allow tab order jump directly to the cancel button
        self.device_list.setEnabled(not in_progress)
        self.prop_list.setEnabled(not in_progress)
        self.field_list.setEnabled(not in_progress)

        self._prev_search_status = self._curr_search_status
        self._curr_search_status = status

    def _reset_selected_value(self):
        self._selected_value = ParameterName(device="", prop="", protocol=self._selected_value.protocol)
        self.selector_label.setText(self.value)

    def _cancel_running_tasks(self):
        if self._active_ccda_task is not None:
            self._active_ccda_task.cancel()
            self._active_ccda_task = None

    async def _on_search_requested(self, search_string: str):
        trimmed_search_string = search_string.strip()
        if not trimmed_search_string:
            return

        device_addr = ParameterName.from_string(trimmed_search_string)
        search_device = device_addr.device if device_addr is not None and device_addr.valid else trimmed_search_string

        self.activity_indicator.hint = f"Searching {search_device}..."
        self._update_from_status(ParameterSelector.NetworkRequestStatus.IN_PROGRESS)
        self._active_ccda_task = look_up_ccda(device_name=search_device,
                                              searched_prop=device_addr.prop if device_addr else None,
                                              searched_field=device_addr.field if device_addr else None)
        self._reset_selected_value()

        try:
            self._search_results = await self._active_ccda_task
        except CancelledError:
            self._update_from_status(self._prev_search_status)
            return
        except BaseException as e:  # noqa: B902
            self.err_label.setText(str(e))
            self._search_results.clear()
            self._update_from_status(ParameterSelector.NetworkRequestStatus.FAILED)
            return

        self._requested_device = search_device
        self.results_group.setTitle(f'Results for search query "{trimmed_search_string}":')

        self._search_results_model.set_data(self._search_results)

        # If device is the only one, auto select it
        if len(self._search_results) == 1:
            self._search_results_model.select_device(0)
        else:
            for idx, dev in enumerate(self._search_results):
                if dev.name == self._requested_device:
                    self._search_results_model.select_device(idx)

        self._update_from_status(ParameterSelector.NetworkRequestStatus.COMPLETE)


class ParameterSelectorDialog(QDialog):

    no_protocol_option = "Omit protocol"
    """This can be overridden to display a different label in protocol combobox, when no protocol is selected."""

    def __init__(self, initial_value: str = "", enable_protocols: bool = False, parent: Optional[QWidget] = None):
        """
        Dialog for choosing parameters (device/property#field) interactively from CCDB.

        Args:
            initial_value: Using this value starts the search immediately.
            enable_protocols: Allow selecting protocols.
            parent: Owning widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Parameter...")
        layout = QVBoxLayout()
        self._widget = ParameterSelector(parent=self,
                                         enable_protocols=enable_protocols,
                                         no_protocol_option=self.no_protocol_option)
        self._widget.value = initial_value
        layout.addWidget(self._widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(buttons)
        self.setLayout(layout)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.resize(526, 360)

    @property
    def value(self) -> str:
        """Selected address of the dialog."""
        return self._widget.value


def make_empty_addr() -> ParameterName:
    return ParameterName(device="", prop="")


_KNOWN_PROTOCOLS = [
    "rda3",
    "rda",
    "tgm",
    "no",
    "rmi",
]
