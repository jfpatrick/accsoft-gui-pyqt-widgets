import operator
import functools
import warnings
from asyncio import Future, CancelledError
try:
    from asyncio import create_task
except ImportError:
    from asyncio import ensure_future as create_task  # type: ignore
from typing import Optional, List, cast, Union, Dict, Tuple
from pathlib import Path
from copy import deepcopy
from qtpy.uic import loadUi
from qtpy.QtGui import QShowEvent, QHideEvent
from qtpy.QtCore import QStringListModel, Qt, Signal, Property, QSignalBlocker
from qtpy.QtWidgets import QWidget, QComboBox, QFrame, QCheckBox, QStackedWidget, QLabel, QVBoxLayout
from accwidgets.qt import ActivityIndicator
from accwidgets._designer_base import is_designer
from accwidgets._async_utils import install_asyncio_event_loop
from ._model import CycleSelectorModel, CycleSelectorConnectionError
from ._data import CycleSelectorValue


class CycleSelector(QWidget):

    valueChanged = Signal(str)
    """
    Fires whenever the selector value changes. The payload will be a string version of selector in the format
    ``DOMAIN.GROUP.LINE``.

    :type: pyqtSignal
    """

    def __init__(self, parent: Optional[QWidget] = None, model: Optional[CycleSelectorModel] = None):
        """
        Widget for choosing control system "selector" (sometimes called timing user).

        Args:
            parent: Owning widget.
            model: Mediator for communication with CCDB.
        """
        super().__init__(parent)

        self._sel_value: Optional[CycleSelectorValue] = None
        self._last_used_sel_value: Optional[CycleSelectorValue] = None
        self._only_users = False
        self._allow_all_user = True
        self._require_selector = False
        self._give_up_ui_on_cancel = False

        self._enforced_domain: Optional[str] = None

        self._model = model or CycleSelectorModel()
        self._orig_data: List[Tuple[str, List[Tuple[str, List[str]]]]] = []
        self._filtered_data: Optional[List[Tuple[str, List[Tuple[str, List[str]]]]]] = None
        self._active_ccda_task: Optional[Future] = None

        self._ui = CycleSelectorUi(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)
        self.setLayout(layout)

        self._connect_model(self._model)

        self._ui.machine_combo.setModel(QStringListModel())
        # We do not use models for other 2 comboboxes because model cannot be used well with separators

        self._ui.activity.hint = "Loading available selectors…"

        self._update_no_selector_checkbox()
        self._toggle_selector(self._ui.no_selector.checkState())

        self._ui.no_selector.stateChanged.connect(self._toggle_selector)
        self._ui.machine_combo.activated.connect(self._on_machine_selected)
        self._ui.group_combo.activated.connect(self._on_group_selected)
        self._ui.line_combo.activated.connect(self._on_line_selected)
        self._update_selector_ui()
        self._update_machine_ui()
        self._update_group_ui()

        install_asyncio_event_loop()

    def _get_sel_value(self) -> Optional[CycleSelectorValue]:
        if is_designer() and self._sel_value:
            # Show as string in Qt Designer
            return str(self._sel_value)  # type: ignore
        return self._sel_value

    def _set_sel_value(self, new_val: Union[str, CycleSelectorValue, None]):
        if is_designer() and new_val == "":
            new_val = None
        if new_val is None and self.requireSelector:
            raise ValueError(f"Cannot accept {new_val} selector because requireSelector is set to True")
        processed_val: Optional[CycleSelectorValue]
        if isinstance(new_val, str):
            list_val = new_val.split(".")
            if len(list_val) != 3 or any(len(v) == 0 for v in list_val):
                if is_designer():
                    # User might be still typing, we should not raise exceptions here. Just bail out and hope for correct
                    # value on the next keystrokes.
                    return
                else:
                    raise ValueError(f'Incorrect string format passed ("{new_val}"), must be of format DOMAIN.GROUP.LINE')
            machine, group, line = tuple(list_val)
            processed_val = CycleSelectorValue(domain=machine, group=group, line=line)
        else:
            processed_val = new_val
        if self.enforcedDomain is not None and (processed_val is not None and processed_val.domain != self.enforcedDomain):
            raise ValueError(f'Given cycle selector "{processed_val}" does not belong to the '
                             f'enforced domain "{self.enforcedDomain}"')
        if processed_val == self._sel_value:
            return
        self._sel_value = processed_val
        self._update_no_selector_checkbox()
        if self._orig_data:
            self._render_data_if_needed()
        self._notify_new_selector()

    value: Optional[CycleSelectorValue] = Property(str, _get_sel_value, _set_sel_value)
    """
    Currently selected value. Updating this attribute will update the corresponding UI.

    .. note:: Setting it to :obj:`None` will raise an error if :attr:`requireSelector` is set to :obj:`True`.
              Also, when :attr:`enforcedDomain` is set, only values of the same domain can be assigned.
    """

    def _get_model(self) -> CycleSelectorModel:
        return self._model

    def _set_model(self, new_val: CycleSelectorModel):
        if new_val == self._model:
            return
        self._disconnect_model(self._model)
        self._model = new_val
        self._connect_model(new_val)

    model = property(fget=_get_model, fset=_set_model)
    """Mediator for communication with CCDB."""

    def _get_only_users(self) -> bool:
        return self._only_users

    def _set_only_users(self, new_val: bool):
        if new_val == self.onlyUsers:
            return
        self._only_users = new_val
        self._update_group_ui()
        if self._orig_data:
            self._filtered_data = None
            self._render_data_if_needed()

    onlyUsers: bool = Property(bool, _get_only_users, _set_only_users)
    """
    Only display ``USER`` option in the "group" combobox. This is useful to narrow down options in operations,
    when selectors only used for timing users, hence all of them belonging to the ``*.USER.*`` format.
    Defaults to :obj:`False`.

    When set to :obj:`False`, all groups will be available. ``USER`` group will be always on the top in the dropdown
    menu and will be emphasized by a menu separator.
    """

    def _get_allow_all_user(self) -> bool:
        return self._allow_all_user

    def _set_allow_all_user(self, new_val: bool):
        if new_val == self.allowAllUser:
            return
        self._allow_all_user = new_val
        if self._orig_data:
            self._filtered_data = None
            self._render_data_if_needed()

    allowAllUser: bool = Property(bool, _get_allow_all_user, _set_allow_all_user)
    """
    This option renders an artificial line called ``ALL``, enabling selectors such as ``PSB.USER.ALL``.
    While not a real selector from the hardware perspective, this option allows all destinations of the
    current machine to be selected. Defaults to :obj:`True`.

    When set to :obj:`True`, ``ALL`` line will be always on the top in the dropdown
    menu and will be emphasized by a menu separator.
    """

    def _get_require_selector(self) -> bool:
        return self._require_selector

    def _set_require_selector(self, new_val: bool):
        if new_val == self.requireSelector:
            return
        if new_val and self._sel_value is None:
            if is_designer():
                if self._orig_data:
                    # In Qt Designer, don't throw errors, try to come up with any valid selector
                    self.value = self._reconstruct_selector(ignore_no_selector=True)
                else:
                    # No data loaded, can't reconstruct, simply bail out
                    return
            else:
                raise ValueError("Cannot set requireSelector to True, because current value is None")
        self._require_selector = new_val
        self._update_selector_ui()

    requireSelector: bool = Property(bool, _get_require_selector, _set_require_selector)
    """
    Setting this flag to :obj:`True` will remove the checkbox that omits the selector, hence the result returned from
    the :attr:`value` can never be :obj:`None`.

    .. note:: If :attr:`value` is :obj:`None`, setting this flag to :obj:`True` will produce an error. You must set
              :attr:`value` to a non-empty selector before attempting that.
    """

    def _get_enforced_domain(self) -> Optional[str]:
        return self._enforced_domain

    def _set_enforced_domain(self, new_val: Optional[str]):
        if new_val == self.enforcedDomain:
            return
        if not is_designer() and new_val and self._sel_value is not None and self._sel_value.domain != new_val.upper():
            raise ValueError(f'Cannot set enforcedDomain to {new_val}, because current value "{self._sel_value}" is incompatible')

        self._enforced_domain = new_val.upper() if new_val else None
        self._update_machine_ui()

        if self._orig_data:
            self._render_data_if_needed()
            # FIXME: Check how this behaves when current slector is None (I guess it's ok to select the first in list)?? Or throw...

    enforcedDomain: Optional[str] = Property(str, _get_enforced_domain, _set_enforced_domain)
    """
    This option limits the selection to the domain of a specific machine. It is useful for applications that are designed
    for a certain machine and will never need selectors of a different domain.

    .. note:: If :attr:`value` is set to a non-empty selector that belongs to a different domain,
              setting this option will produce an error.
    """

    def refetch(self):
        """
        Force the widget to query available selectors from CCDB and re-render the UI.

        This is an optional method, as the widget will query CCDB when it becomes visible for the first time.
        """
        create_task(self._fetch_data())

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._give_up_ui_on_cancel = False

        # Have we been shown?
        if event.spontaneous():
            return

        if self._orig_data:
            if not self._filtered_data:
                # Fetched data exists, only need to reprocess and render it
                self._render_data_if_needed()
        else:
            # Fetch data does not exist
            self.refetch()

    def hideEvent(self, event: QHideEvent):
        self._ui.activity.stopAnimation()
        self._give_up_ui_on_cancel = True
        self._cancel_running_tasks()
        super().hideEvent(event)

    async def _fetch_data(self):
        # Only execute this once after being shown for the first time
        self._set_mode(_STACK_LOADING)
        self._filtered_data = None

        self._active_ccda_task = create_task(self.model.fetch())
        try:
            fetched_data = await self._active_ccda_task
        except CancelledError:
            if not self._give_up_ui_on_cancel:
                self._set_mode(_STACK_COMPLETE)
            return
        except CycleSelectorConnectionError as e:
            self._show_error(str(e))
            return

        if not fetched_data:
            self._show_error("Received empty data from CCDB")
            return
        self._orig_data = convert_data(fetched_data)

        self._set_mode(_STACK_COMPLETE)
        self._render_data_if_needed()

    def _processed_data(self):
        if not self._filtered_data:
            domains = deepcopy(self._orig_data)
            filter_data(domains, allow_all_user=self.allowAllUser, only_users=self.onlyUsers)
            sort_data(domains)
            self._filtered_data = domains
        return self._filtered_data

    def _render_data_if_needed(self):
        machine, group, line = ((self._sel_value.domain, self._sel_value.group, self._sel_value.line) if self._sel_value
                                else (None, None, None))

        if self.enforcedDomain:
            machine = self.enforcedDomain

        # Pre-filter if needed
        domains = self._processed_data()

        if (machine is None and group is None and line is None
                and len(cast(QStringListModel, self._ui.machine_combo.model()).stringList()) > 0):
            # Leave the combobox arrangement as is
            # (e.g. if it was selected before, but then checkbox to not use it was ticked)
            # However, when rendering for the first time, we still must go through the whole procedure
            return

        self._do_render_data(domains, machine, group, line)

    def _do_render_data(self,
                        domains: List[Tuple[str, List[Tuple[str, List[str]]]]],
                        machine: Optional[str],
                        group: Optional[str],
                        line: Optional[str]):
        cast(QStringListModel, self._ui.machine_combo.model()).setStringList(map(operator.itemgetter(0), domains))

        if machine is None:
            machine_idx = 0
        else:
            machine_idx = self._ui.machine_combo.findText(machine)
            # machine_idx = item_idx(self._ui.machine_combo, machine)
            if machine_idx == -1:
                if is_designer():
                    # User might be still typing. Bail out...
                    return
                machine_idx = 0
                fallback_machine = self._ui.machine_combo.itemText(0)
                warnings.warn(f"Wanted machine {machine} does not exist in the list. Falling back to {fallback_machine}")

        self._ui.machine_combo.setCurrentIndex(machine_idx)
        self._repopulate_groups_combo(machine_idx=machine_idx)

        if self._ui.group_combo.count() == 0:
            warnings.warn(f"Groups corresponding to the machine {self._ui.machine_combo.currentText()} are empty. UI bails out.")
            return

        if group is None:
            ui_group_idx, data_group_idx = 0, 0
        else:
            ui_group_idx = self._ui.group_combo.findText(group)
            if ui_group_idx == -1:
                if is_designer():
                    # User might be still typing. Bail out...
                    return
                ui_group_idx, data_group_idx = 0, 0
                fallback_group = self._ui.group_combo.itemText(ui_group_idx)
                warnings.warn(f"Wanted group {group} does not exist in the list. Falling back to {fallback_group}")
            else:
                data_group_idx = item_idx(self._ui.group_combo, group)

        self._ui.group_combo.setCurrentIndex(ui_group_idx)
        self._repopulate_lines_combo(machine_idx=machine_idx, group_idx=data_group_idx)

        if self._ui.line_combo.count() == 0:
            warnings.warn(f"Lines corresponding to the group {self._ui.machine_combo.currentText()}."
                          f"{self._ui.group_combo.currentText()} are empty. UI bails out.")
            return

        if line is None:
            line_idx = 0
        else:
            line_idx = self._ui.line_combo.findText(line)
            if line_idx == -1:
                if is_designer():
                    # User might be still typing. Bail out...
                    return
                line_idx = 0
                fallback_line = self._ui.line_combo.itemText(line_idx)
                warnings.warn(f"Wanted line {line} does not exist in the list. Falling back to {fallback_line}")

        self._ui.line_combo.setCurrentIndex(line_idx)

    def _on_machine_selected(self, index: int):
        self._repopulate_groups_combo(machine_idx=index)
        new_group_idx = 0
        self._ui.group_combo.setCurrentIndex(new_group_idx)
        self._repopulate_lines_combo(machine_idx=index, group_idx=new_group_idx)
        try:
            self._sel_value = self._reconstruct_selector()
        except ValueError:
            return
        self._notify_new_selector()

    def _on_group_selected(self, index: int):
        self._repopulate_lines_combo(machine_idx=self._ui.machine_combo.currentIndex(), group_idx=index)
        self._ui.line_combo.setCurrentIndex(0)
        try:
            self._sel_value = self._reconstruct_selector()
        except ValueError:
            return
        self._notify_new_selector()

    def _on_line_selected(self):
        try:
            self._sel_value = self._reconstruct_selector()
        except ValueError:
            return
        self._notify_new_selector()

    def _repopulate_groups_combo(self, machine_idx: int):
        _, groups = self._processed_data()[machine_idx]
        # We do not use models because model cannot be used well with separators
        self._ui.group_combo.clear()
        add_sep = len(groups) > 1
        for i, gr in enumerate(groups):
            group_name, _ = gr
            self._ui.group_combo.addItem(group_name)
            if add_sep and i == 0 and group_name == GROUP_NAME_USER:
                self._ui.group_combo.insertSeparator(i + 1)

    def _repopulate_lines_combo(self, machine_idx: int, group_idx: int):
        _, groups = self._processed_data()[machine_idx]
        _, lines = groups[group_idx]
        # We do not use models because model cannot be used well with separators
        self._ui.line_combo.clear()
        add_sep = len(lines) > 1
        for i, val in enumerate(lines):
            self._ui.line_combo.addItem(val)
            if add_sep and i == 0 and val == VALUE_NAME_ALL:
                self._ui.line_combo.insertSeparator(i + 1)

    def _toggle_selector(self, state: Qt.CheckState):
        none_sel = state == Qt.Checked
        self._update_frame_ui()
        try:
            self.value = None if none_sel else self._reconstruct_selector()
        except ValueError:
            pass

    def _notify_new_selector(self):
        if self._sel_value == self._last_used_sel_value:
            return

        self._last_used_sel_value = self._sel_value
        self.valueChanged.emit(str(self._sel_value) if self._sel_value else "")

    def _show_error(self, msg: str):
        self._set_mode(_STACK_ERROR)
        self._ui.error.setText(msg)

    def _connect_model(self, model: CycleSelectorModel):
        self._model.setParent(self)

    def _disconnect_model(self, model: CycleSelectorModel):
        if model.parent() is self:
            model.setParent(None)
            model.deleteLater()

    def _set_mode(self, mode: int):
        self._ui.stack.setCurrentIndex(mode)
        if mode != _STACK_LOADING:
            self._ui.activity.stopAnimation()
        else:
            self._ui.activity.startAnimation()

    def _update_selector_ui(self):
        self._ui.no_selector.setVisible(not self.requireSelector)

    def _update_no_selector_checkbox(self):
        blocker = QSignalBlocker(self._ui.no_selector)
        self._ui.no_selector.setChecked(self._sel_value is None)
        blocker.unblock()
        self._update_frame_ui()

    def _update_frame_ui(self):
        self._ui.chooser_frame.setEnabled(not self._ui.no_selector.isChecked())

    def _update_machine_ui(self):
        self._ui.machine_combo.setEnabled(not self.enforcedDomain)

    def _update_group_ui(self):
        self._ui.group_combo.setEnabled(not self.onlyUsers)

    def _cancel_running_tasks(self):
        if self._active_ccda_task is not None:
            self._active_ccda_task.cancel()
            self._active_ccda_task = None

    def _reconstruct_selector(self, ignore_no_selector: bool = False) -> Optional[CycleSelectorValue]:
        if not ignore_no_selector and self._ui.no_selector.isChecked():
            return None
        machine = self._ui.machine_combo.currentText()
        group = self._ui.group_combo.currentText()
        line = self._ui.line_combo.currentText()
        if not machine or not group or not line:
            raise ValueError
        return CycleSelectorValue(domain=machine, group=group, line=line)


class CycleSelectorUi(QWidget):

    def __init__(self, parent: Optional[QWidget]):
        super().__init__(parent)
        self.machine_combo: QComboBox = None
        self.group_combo: QComboBox = None
        self.line_combo: QComboBox = None
        self.chooser_frame: QFrame = None
        self.no_selector: QCheckBox = None
        self.stack: QStackedWidget = None
        self.error: QLabel = None
        self.activity: ActivityIndicator = None  # type: ignore
        loadUi(Path(__file__).parent / "selector.ui", self)


_STACK_COMPLETE = 0
_STACK_LOADING = 1
_STACK_ERROR = 2


def item_idx(combobox: QComboBox, name: str) -> int:
    # Because separator items can be in the combobox, it's not possible to use findText()
    # which returns the index, considering the separators above. If you use this index to search through data,
    # the out of bounds error may happen. Hence we need to know the index with separator items removed
    all_names = (combobox.itemText(i) for i in range(combobox.count()))
    non_sep_names = filter(bool, all_names)
    try:
        return list(non_sep_names).index(name)
    except ValueError:
        return -1


def convert_data(data: Dict[str, Dict[str, List[str]]]) -> List[Tuple[str, List[Tuple[str, List[str]]]]]:
    res = []
    for domain_name, groups in data.items():
        intermediate = list(groups.items())
        res.append((domain_name, intermediate))
    return res


def filter_data(data: List[Tuple[str, List[Tuple[str, List[str]]]]], allow_all_user: bool, only_users: bool):
    if not only_users and allow_all_user:
        # Data is complete, no need to filter
        return data

    for _, groups in data:
        if only_users:
            groups[:] = filter(lambda group: group[0].upper() == GROUP_NAME_USER, groups)
        if not allow_all_user:
            for group_name, lines in groups:
                if group_name != GROUP_NAME_USER:
                    continue
                lines[:] = filter(lambda v: v != VALUE_NAME_ALL, lines)
    return data


def sort_data(data: List[Tuple[str, List[Tuple[str, List[str]]]]]):
    data.sort(key=operator.itemgetter(0))
    for _, groups in data:
        groups.sort(key=functools.cmp_to_key(cmp_groups))
        for __, lines in groups:
            lines.sort(key=functools.cmp_to_key(cmp_values))


def cmp_groups(lhs: Tuple[str, List[str]], rhs: Tuple[str, List[str]]):
    """
    Sort data alphabetically
    ``USER`` group should always stay on top, regardless of the alphabetical order
    """
    if lhs[0] == GROUP_NAME_USER:
        return -1
    if rhs[0] == GROUP_NAME_USER:
        return 1
    return (lhs[0] > rhs[0]) - (lhs[0] < rhs[0])


def cmp_values(lhs: str, rhs: str):
    """
    Sort data alphabetically
    ``ALL`` user should always stay on top, regardless of the alphabetical order
    """
    if lhs == VALUE_NAME_ALL:
        return -1
    if rhs == VALUE_NAME_ALL:
        return 1
    return (lhs > rhs) - (lhs < rhs)


GROUP_NAME_USER = "USER"
VALUE_NAME_ALL = "ALL"
