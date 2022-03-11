from typing import Optional, Union
from qtpy.QtWidgets import QAction, QMenu, QWidgetAction, QWidget, QVBoxLayout
from qtpy.QtCore import QEvent
from qtpy.QtGui import QIcon
from ._model import CycleSelectorModel
from ._common import CycleSelectorWrapper
from ._data import CycleSelectorValue


class CycleSelectorAction(QAction, CycleSelectorWrapper):

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 text: Optional[str] = None,
                 icon: Optional[QIcon] = None,
                 model: Optional[CycleSelectorModel] = None):
        """
        This action provides a menu with :class:`~accwidgets.cycle_selector.CycleSelector` that can be used as
        a popup in a :class:`QToolButton` or in another menu.

        Args:
            parent: Owning widget.
            text: Text to be displayed for the action. When left as :obj:`None`, the text will be dynamically
                  configured to represent the chosen selector, e.g. ``Selector: PSB.USER.ALL`` or ``Selector: ---``
                  when none selected.
            icon: Icon for the action.
            model: Mediator for communication with CCDB.
        """
        QAction.__init__(self, parent)
        CycleSelectorWrapper.__init__(self, model)
        widget_action = QWidgetAction(self)
        menu = QMenu(parent)
        widget = PopupWrapper()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(self._sel)
        widget_action.setDefaultWidget(widget)
        menu.addAction(widget_action)
        if text:
            self.setText(text)
        else:
            # Make the title dynamic, depending on the selected value:
            self._sel.valueChanged.connect(self._update_title)
            self._update_title(self._sel.value)
        if icon:
            self.setIcon(icon)
        self.setMenu(menu)

    def _update_title(self, val: Union[str, CycleSelectorValue, None]):
        self.setText(f"Selector: {val or '---'}")


class PopupWrapper(QWidget):

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonPress or event.type() == QEvent.MouseButtonRelease:
            # Prevent widget being hidden on a click inside the popup area
            return True
        return super().event(event)
