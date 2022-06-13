from typing import Optional
from qtpy.QtCore import Signal
from ._widget import CycleSelector
from ._model import CycleSelectorModel
from ._data import CycleSelectorValue


class CycleSelectorWrapper:

    valueChanged = Signal(str)
    """
    Fires whenever the selector value changes. The payload will be a string version of selector in the format
    ``DOMAIN.GROUP.LINE``.

    :type: pyqtSignal
    """

    def __init__(self, model: Optional[CycleSelectorModel] = None):
        super().__init__()
        self._sel = CycleSelector(model=model)
        self._sel.valueChanged.connect(self.valueChanged)

    def _get_value(self) -> Optional[CycleSelectorValue]:
        return self._sel.value

    def _set_value(self, new_val: Optional[CycleSelectorValue]):
        self._sel.value = new_val

    value = property(fget=_get_value, fset=_set_value)
    """
    Currently selected value. Updating this attribute will update the corresponding UI.

    .. note:: Setting it to :obj:`None` will raise an error if :attr:`requireSelector` is set to :obj:`True`.
              Also, when :attr:`enforcedDomain` is set, only values of the same domain can be assigned.
    """

    def _get_only_users(self) -> bool:
        return self._sel.onlyUsers

    def _set_only_users(self, new_val: bool):
        self._sel.onlyUsers = new_val

    onlyUsers = property(fget=_get_only_users, fset=_set_only_users)
    """
    Only display ``USER`` option in the "group" combobox. This is useful to narrow down options in operations,
    when selectors only used for timing users, hence all of them belonging to the ``*.USER.*`` format.
    Defaults to :obj:`False`.

    When set to :obj:`False`, all groups will be available. ``USER`` group will be always on the top in the dropdown
    menu and will be emphasized by a menu separator.
    """

    def _get_allow_all_user(self) -> bool:
        return self._sel.allowAllUser

    def _set_allow_all_user(self, new_val: bool):
        self._sel.allowAllUser = new_val

    allowAllUser = property(fget=_get_allow_all_user, fset=_set_allow_all_user)
    """
    This option renders an artificial line called ``ALL``, enabling selectors such as ``PSB.USER.ALL``.
    While not a real selector from the hardware perspective, this option allows all destinations of the
    current machine to be selected. Defaults to :obj:`True`.

    When set to :obj:`True`, ``ALL`` line will be always on the top in the dropdown
    menu and will be emphasized by a menu separator.
    """

    def _get_require_selector(self) -> bool:
        return self._sel.requireSelector

    def _set_require_selector(self, new_val: bool):
        self._sel.requireSelector = new_val

    requireSelector = property(fget=_get_require_selector, fset=_set_require_selector)
    """
    Setting this flag to :obj:`True` will remove the checkbox that omits the selector, hence the result returned from
    the :attr:`value` can never be :obj:`None`.

    .. note:: If :attr:`value` is :obj:`None`, setting this flag to :obj:`True` will produce an error. You must set
              :attr:`value` to a non-empty selector before attempting that.
    """

    def _get_enforced_domain(self) -> Optional[str]:
        return self._sel.enforcedDomain

    def _set_enforced_domain(self, new_val: Optional[str]):
        self._sel.enforcedDomain = new_val

    enforcedDomain = property(fget=_get_enforced_domain, fset=_set_enforced_domain)
    """
    This option limits the selection to the domain of a specific machine. It is useful for applications that are designed
    for a certain machine and will never need selectors of a different domain.

    .. note:: If :attr:`value` is set to a non-empty selector that belongs to a different domain,
              setting this option will produce an error.
    """
