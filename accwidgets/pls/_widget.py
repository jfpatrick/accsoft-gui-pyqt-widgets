try:
    from asyncio import create_task
except ImportError:
    from asyncio import ensure_future as create_task  # type: ignore
from dataclasses import dataclass
from typing import Optional, List, cast, Union, Tuple
from pathlib import Path
from qtpy.uic import loadUi
from qtpy.QtGui import QShowEvent
from qtpy.QtCore import QStringListModel, Qt, Signal, Property
from qtpy.QtWidgets import QWidget, QComboBox, QFrame, QCheckBox, QStackedWidget, QLabel, QVBoxLayout
from pyccda import sync_models as CCDATypes
from ._model import PlsSelectorModel
from accwidgets._designer_base import is_designer


@dataclass
class PLSSelectorConfig:
    machine: Optional[str] = None
    group: Optional[str] = None
    line: Optional[str] = None
    enabled: bool = True

    @classmethod
    def no_selector(cls):
        return cls(enabled=False)


# TODO: Replace ActivityIndicator
# TODO: Make properties on the widget (users only, no selector support, etc)
# TODO: Make a dialog / qaction
# TODO: Single dropdown with selected domain
# TODO: Input as either machine/group/line or single timing string
# TODO: Add examples
# TODO: Cancel fetch on hide


class PlsSelector(QWidget):

    # FIXME: Change to valueChanged, also see if need to be emitted from programmatic update
    selector_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, model: Optional[PlsSelectorModel] = None):  #, config: PLSSelectorConfig):
        """
        Dialog for choosing control system "selector" on the window level.

        Args:
            config: Initial telegram info to configure UI for.
            parent: Owning widget.
        """
        super().__init__(parent)

        self._pls_value: Optional[Tuple[str, str, str]] = None
        self._enforced_domain: Optional[str] = None

        self._original_machine: Optional[str] = None
        self._original_group: Optional[str] = None
        self._original_line: Optional[str] = None

        self._model = model or PlsSelectorModel()
        self._data: List[CCDATypes.SelectorDomain] = []

        self._ui = PlsSelectorUi(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)
        self.setLayout(layout)

        self._connect_model(self._model)

        # FIXME: Think of a smarter model, see ParameterSelector
        self._ui.machine_combo.setModel(QStringListModel())
        self._ui.group_combo.setModel(QStringListModel())
        self._ui.line_combo.setModel(QStringListModel())

        # FIXME: Revive this
        # self._ui.no_selector.setChecked(not config.enabled)
        # self._toggle_selector(self.no_selector.checkState())
        #
        # self._original_machine = config.machine
        # self._original_group = config.group
        # self._original_line = config.line

        self._ui.no_selector.stateChanged.connect(self._toggle_selector)
        # FIXME: This is for dialog only
        # self.accepted.connect(self._notify_new_selector)

    def _get_pls_value(self) -> Optional[Tuple[str, str, str]]:
        if is_designer() and self._pls_value:
            # Show as string in Qt Designer
            return ".".join(self._pls_value)
        return self._pls_value

    def _set_pls_value(self, new_val: Union[str, Tuple[str, str, str], None]):
        if isinstance(new_val, str):
            tuple_val = new_val.split(".")
            if len(tuple_val) != 3:
                raise ValueError(f"Incorrect string format passed ({new_val}), must be of format DOMAIN.GROUP.LINE")
            new_val = tuple(tuple_val)
        if self._enforced_domain is not None and (new_val is None or new_val[0] != self._enforced_domain):
            sel = ".".join(new_val) if new_val is not None else new_val
            raise ValueError(f'Given PLS selector "{sel}" does not belong to the '
                             f'enforced domain "{self._enforced_domain}"')
        if new_val == self._pls_value:
            return
        self._pls_value = new_val

    value: Optional[Tuple[str, str, str]] = Property(str, _get_pls_value, _set_pls_value)

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)

        # Have we been shown?
        if event.spontaneous() or self._data:
            return

        create_task(self._fetch_data())

    async def _fetch_data(self):
        # Only execute this once after being shown for the first time
        self._ui.stack.setCurrentIndex(_STACK_LOADING)
        await self._model.fetch()
        self._data = self._model.domains

        if not self._data:
            err_msg = "Empty data received from CCDA. Cannot populate PLS dialog."
            self._ui.stack.setCurrentIndex(_STACK_ERROR)
            self._ui.error.setText(err_msg)
            return

        self._ui.stack.setCurrentIndex(_STACK_COMPLETE)

        cast(QStringListModel, self._ui.machine_combo.model()).setStringList([x.name for x in self._data])
        if self._original_machine is None:
            machine_idx = 0
        else:
            machine_idx = max(0, self._ui.machine_combo.findText(self._original_machine))

        self._ui.machine_combo.setCurrentIndex(machine_idx)
        self._update_groups_for_machine(machine_idx)

        if self._original_group is None:
            group_idx = 0
        else:
            group_idx = max(0, self._ui.group_combo.findText(self._original_group))

        self._ui.group_combo.setCurrentIndex(group_idx)
        self._update_lines_for_group(machine_idx=machine_idx, group_idx=group_idx)

        if self._original_line is None:
            line_idx = 0
        else:
            line_idx = max(0, self._ui.line_combo.findText(self._original_line))

        self._ui.line_combo.setCurrentIndex(line_idx)

        self._ui.machine_combo.currentIndexChanged[str].connect(self._machine_updated)
        self._ui.group_combo.currentIndexChanged[str].connect(self._group_updated)

    def _machine_updated(self, text: str):
        index = self._ui.machine_combo.findText(text)
        if index == -1:
            return

        self._update_groups_for_machine(index)
        self._ui.group_combo.setCurrentIndex(0)

    def _group_updated(self, text: str):
        index = self._ui.group_combo.findText(text)
        if index == -1:
            return

        self._update_lines_for_group(machine_idx=self._ui.machine_combo.currentIndex(), group_idx=index)
        self._ui.line_combo.setCurrentIndex(0)

    def _update_groups_for_machine(self, index: int):
        machine = self._data[index]
        cast(QStringListModel, self._ui.group_combo.model()).setStringList([x.name for x in machine.selector_groups])

    def _update_lines_for_group(self, machine_idx: int, group_idx: int):
        machine = self._data[machine_idx]
        group = machine.selector_groups[group_idx]
        cast(QStringListModel, self._ui.line_combo.model()).setStringList([x.name for x in group.selector_values])

    def _toggle_selector(self, state: Qt.CheckState):
        self._ui.chooser_frame.setEnabled(state != Qt.Checked)

    def _notify_new_selector(self):
        new_selector: Optional[str]
        if self._ui.no_selector.isChecked():
            new_selector = None
        else:
            machine = self._ui.machine_combo.currentText()
            group = self._ui.group_combo.currentText()
            line = self._ui.line_combo.currentText()
            if not machine or not group or not line:
                return

            new_selector = ".".join([machine, group, line])

        self.selector_selected.emit(new_selector)

    def _connect_model(self, model: PlsSelectorModel):
        pass

    def _disconnect_model(self, model: PlsSelectorModel):
        pass


class PlsSelectorUi(QWidget):

    def __init__(self, parent: Optional[QWidget]):
        super().__init__(parent)

        self.machine_combo: QComboBox = None
        self.group_combo: QComboBox = None
        self.line_combo: QComboBox = None
        self.chooser_frame: QFrame = None
        self.no_selector: QCheckBox = None
        self.stack: QStackedWidget = None
        self.error: QLabel = None

        loadUi(Path(__file__).parent / "pls.ui", self)

_STACK_COMPLETE = 0
_STACK_LOADING = 1
_STACK_ERROR = 2
