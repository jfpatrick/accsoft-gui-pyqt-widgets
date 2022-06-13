"""
:class:`~accwidgets.timing_bar.TimingBar`'s model deals with connecting to XTIM devices and retrieving timing
information, such as supercycle structure, as well as listening to timing events.
"""

import numpy as np
import operator
from typing import Optional, List, Dict, Any, Tuple, Callable, Set, Type, TYPE_CHECKING
from datetime import datetime, tzinfo
from dateutil.tz import UTC
from enum import Enum
from dataclasses import dataclass
from qtpy.QtCore import QObject, Signal
from accwidgets.designer_check import is_designer


if TYPE_CHECKING:
    from pyjapc import PyJapc  # noqa: F401


class TimingBarDomain(Enum):
    """
    Enumeration of known timing domains that can be resolved to an XTIM
    device supplying timing information.

    .. note:: While timing domains sound similar to accelerator machine names, they do not necessarily represent
              timing of only that machine.
    """

    LHC = "LHC"
    """Large Hadron Collider."""

    SPS = "SPS"
    """Super Proton Synchrotron."""

    CPS = "CPS"
    """Proton Synchrotron Complex."""

    PSB = "PSB"
    """Proton Synchrotron Booster + Linear Accelerators (LINACs)."""

    LNA = "LNA"
    """ELENA ring."""

    LEI = "LEI"
    """Low Energy Ion Ring (includes LINAC3)."""

    ADE = "ADE"
    """Antiproton Decelerator."""


@dataclass(frozen=True)
class PyJapcSubscription:
    """Class to work around PyJapc's limitation of not allowing to stop individual subscriptions."""
    param_name: str
    handler: object  # This is the Jpype object
    selector: str

    @property
    def monitoring(self) -> bool:
        return self.handler.isMonitoring()  # type: ignore  # Java call

    def set_monitoring(self, new_val: bool):
        if new_val:
            self.handler.startMonitoring()  # type: ignore  # Java call
        else:
            self.handler.stopMonitoring()  # type: ignore  # Java call


@dataclass(frozen=True)
class TimingUpdate:
    timestamp: datetime
    offset: int
    user: str
    lsa_name: str


@dataclass(frozen=True)
class TimingCycle:
    """Model for each cycle (one box out of many in the supercycle)."""

    user: str
    """
    User of the beam in the cycle.

    If :attr:`TimingBar.cycleSelector` is defined, it will be compared to this name to highlight if the
    cycle matches the "monitored" one.
    """

    lsa_name: str
    """
    LSA name of the cycle. If one does not exist, normally it will be prepopulated with the string "~~zero~~"
    by the timing system.
    """

    offset: int
    """Offset of the cycle in the supercycle in basic periods (1.2s)."""

    duration: int
    """Number of basic periods (1.2s) that the cycle spans to."""


@dataclass
class TimingSuperCycle:
    normal: List[TimingCycle]
    spare: List[TimingCycle]
    spare_mode: bool = False

    @property
    def cycles(self) -> List[TimingCycle]:
        return self.spare if self.spare_mode else self.normal

    def cycle_at_basic_period(self, bp: int) -> Tuple[int, TimingCycle]:
        if bp < 0:
            raise ValueError
        for idx, cycle in enumerate(self.cycles):
            if cycle.offset <= bp < cycle.offset + cycle.duration:
                return idx, cycle
        else:
            raise ValueError


class TimingBarModel(QObject):

    NON_SUPERCYCLE_BP_COUNT = 128
    """
    Amount of cycle blocks for timing domains that do not have a supercycle structure.

    Supercycles are relevant only to a subset of timing domains. For others, such as :attr:`~TimingBarDomain.LHC` or
    :attr:`~TimingBarDomain.ADE`, the bar will present a row of number of cycles determined by this constant, and each
    of will have the width of 1 basic period (1.2 seconds).
    """

    timingUpdateReceived = Signal(bool)
    """
    Signal that is fired on the next timing event from an XTIM device. Its boolean argument represents whether the
    current basic period really advanced (devices may fire more than one event at once), hence it is useful to know
    when these events represent a change in state (e.g. for indicating heartbeat). Otherwise, if each even would be
    duplicated, the heartbeat value would be canceled out.

    :type: pyqtSignal
    """

    timingErrorReceived = Signal(str)
    """
    Signal that is fired when a connection error is received. This can be either a supercycle structure problem,
    or connection issues with XTIM or CTIM devices. The string argument represents the error message.

    :type: pyqtSignal
    """

    domainNameChanged = Signal(str)
    """
    Signal to notify that domain has been changed. The widget should update its domain name label, without necessarily
    repainting the rest of the canvas. The string argument is the name of the new timing domain.

    :type: pyqtSignal
    """

    monitoringChanged = Signal(bool)
    """
    Signal to notify that model's monitoring state has been altered. This signal arrives before subscriptions have been
    affected. Therefore, if subscription procedure produces an error, :attr:`timingErrorReceived` signal will follow
    afterwards.

    :type: pyqtSignal
    """

    def __init__(self,
                 domain: TimingBarDomain = TimingBarDomain.PSB,
                 japc: Optional["PyJapc"] = None,
                 timezone: Optional[tzinfo] = None,
                 monitoring: bool = True,
                 parent: Optional[QObject] = None):
        """
        Model manages the JAPC/RDA connections to the XTIM devices to receive timing events, as well as retrieves
        overall supercycle information for relevant domains from the CTIM (Central Timing) devices.

        It works on a given timing domain. Whenever this domain changes, a set of new connections is established
        to the devices, serving that new domain.

        Model does not initialize JAPC/RDA subscriptions until :meth:`activate` method is called, mainly to defer
        extra work until the widget actually gets shown to the user.

        Args:
            domain: Timing domain to retrieve cycle information as well as timing events from.
            japc: Optional instance of :class:`~pyjapc.PyJapc`, in case there's a need to use a specific instance (e.g.
                  if a subclass is preferred, or it absolutely needs to operate on a singleton). If none provided,
                  a new instance is created internally, with InCA disabled.
            timezone: Timezone to use when creating timestamp objects. If :obj:`None` is provided, UTC timezone is used.
            monitoring: Pass :obj:`False` to not establish connection to CTIM/XTIM devices, until enabled explicitly
                  later using :attr:`monitoring` setter.
            parent: Owning object.
        """
        super().__init__(parent)
        self._monitoring = monitoring
        self._japc = japc
        self._domain = domain
        self._tz = timezone or UTC
        self._japc_activated = False
        self._error_state: Set[str] = set()  # Keep error for both XTIM and CTIM, as they are launched in parallel and may cancel each others error flag
        self._active_subs: List[PyJapcSubscription] = []
        self._bcd: Optional[TimingSuperCycle] = None
        self._current_bp: int = -1
        self._last_shadow_bp: int = -1  # Used for non-supercycle mode, to detect when the new update is actually effective (for double calls)
        self._last_info: Optional[TimingUpdate] = None
        # This MUST be a lambda, otherwise the method will never be called, as explained here: https://stackoverflow.com/a/35304400
        self.destroyed.connect(lambda: self._detach_japc())

    @property
    def current_basic_period(self) -> int:
        """
        Indicates the time position in the supercycle divided into 1 basic period chunks (1.2 seconds).

        For timing domains with the supercycle structure, this position is taken directly from the XTIM device
        events. When working with the timing domain that does not have a supercycle structure, this offset is
        calculated locally, based on assumed rotation within :attr:`NON_SUPERCYCLE_BP_COUNT` time span.

        Until the first XTIM device event has been received, this value stays at ``-1``.
        """
        return self._current_bp

    @property
    def last_info(self) -> Optional[TimingUpdate]:
        """
        State-of-the-art information about the timing state, that can be referenced at any render time.
        This information gets updated only on the next XTIM event.

        Until the first XTIM device event has been received, this value stays :obj:`None`.
        """
        return self._last_info

    @property
    def is_supercycle_mode(self) -> bool:
        """
        Identifies whether current timing domain has a supercycle structure. If not, a dummy supercycle structure
        is assumed with 1 basic period blocks, totalling at :attr:`NON_SUPERCYCLE_BP_COUNT` units.
        """
        return self._bcd is not None

    @property
    def supercycle(self) -> List[TimingCycle]:
        """
        Supercycle composition that is represented as a list of cycle objects. This information should be accessed
        only when timing domain is known to have a supercycle structure. In other cases, :exc:`TypeError` will be
        thrown.

        Raises:
            TypeError: Information is accessed in the incompatible mode.
        """
        if self._bcd is None:
            raise TypeError
        return self._bcd.cycles

    @property
    def cycle_count(self) -> int:
        """
        Amount of cycles in the supercycle.

        If the current timing domain does not have a supercycle structure, this number will be fixed at
        :attr:`NON_SUPERCYCLE_BP_COUNT`, as all cycles will be assumed to have a length of 1 basic period.
        """
        return self.NON_SUPERCYCLE_BP_COUNT if self._bcd is None else len(self._bcd.cycles)

    @property
    def supercycle_duration(self) -> int:
        """
        Supercycle duration in basic periods.

        If the current timing domain does not have a supercycle structure, this number will be fixed at
        :attr:`NON_SUPERCYCLE_BP_COUNT`.
        """
        if self._bcd is None:
            return self.NON_SUPERCYCLE_BP_COUNT
        return sum(map(operator.attrgetter("duration"), self._bcd.cycles))

    @property
    def current_cycle_index(self) -> int:
        """
        Indicates the index of the cycle corresponding to the :attr:`current_basic_period`, considering that some
        cycles may have lengths of multiple basic periods.

        For timing domains without the supercycle structure, this value cannot be determined, and therefore
        this property should not be accessed when :attr:`is_supercycle_mode` resolves to :obj:`False`, otherwise
        a :exc:`TypeError` will be thrown.

        If :attr:`current_basic_period` is outside of the known supercycle bounds, return value will be ``-1``.

        Raises:
            TypeError: Information is accessed in the incompatible mode.
        """
        if self._bcd is None:
            raise TypeError
        try:
            idx, _ = self._bcd.cycle_at_basic_period(self._current_bp)
        except ValueError:
            return -1  # BCD exists, but we have not yet received an XTIM update to know the current basic period
        return idx

    def _get_domain(self) -> TimingBarDomain:
        return self._domain

    def _set_domain(self, new_val: TimingBarDomain):
        if new_val == self._domain:
            return
        self._detach_japc()
        self._domain = new_val
        self.domainNameChanged.emit(new_val.value)
        self._attach_japc()

    domain = property(fget=_get_domain, fset=_set_domain)
    """
    Currently displayed timing domain. Resetting this value will lead to termination of the active connections
    to XTIM and CTIM devices and creation of the new ones.
    """

    def _get_monitoring(self) -> bool:
        return self._monitoring

    def _set_monitoring(self, new_val: bool):
        if self._monitoring == new_val:
            return
        self._monitoring = new_val
        self.monitoringChanged.emit(new_val)
        for sub in self._active_subs:
            self._monitor_param(sub, monitor=new_val)

    monitoring = property(fget=_get_monitoring, fset=_set_monitoring)
    """
    Advanced control over JAPC subscriptions to XTIM and CTIM devices. When a widget needs to be "frozen", this
    property can be set to :obj:`False`.

    .. note:: If initially monitoring of the model was set to :obj:`False`, setting this to :obj:`True` will not
              automatically create connections. It is still required to call :meth:`activate`.
    """

    @property
    def activated(self) -> bool:
        """
        Whether :meth:`activate` method has already been called. Activation happens only once and then the model
        stays connected until it's destroyed.
        """
        return self._japc_activated

    @property
    def has_error(self) -> bool:
        """
        Whether the last connection to XTIM or CTIM devices has failed and has not been restored since.
        """
        return len(self._error_state) > 0

    def activate(self):
        """
        Method to be called by the widget, to start subscriptions only when appearing on screen in order to avoid
        creating unnecessary connections while being hidden.
        """
        if not self._japc_activated:
            self._japc_activated = True

            if not is_designer():
                if self._japc is None:
                    pyjapc_class = import_pyjapc()
                    self._japc = pyjapc_class(selector="",
                                              incaAcceleratorName=None,  # XTIM does not need InCA
                                              timeZone=self._tz)
                self._attach_japc()
            else:
                # For Designer, create a fake model information and notify the widget to re-render
                self._last_info = TimingUpdate(timestamp=datetime.now(tz=self._tz),
                                               user="USER",
                                               lsa_name="~~zero~~",
                                               offset=0)
                self._notify_timing_update(True)

    def _on_bcd_structure_update(self, parameterName: str, data: Dict[str, Any]):
        try:
            self._error_state.remove(parameterName)
        except KeyError:
            pass
        try:
            self._bcd = TimingSuperCycle(normal=self._create_supercycle(data=data,
                                                                        lengths_key="normalCycleLengthsBp",
                                                                        lsa_key="normalLsaCycleNames",
                                                                        users_key="normalUsers"),
                                         spare=self._create_supercycle(data=data,
                                                                       lengths_key="spareCycleLengthsBp",
                                                                       lsa_key="spareLsaCycleNames",
                                                                       users_key="spareUsers"))
        except ValueError:
            self._error_state.add(parameterName)
            self.timingErrorReceived.emit("Received contradictory supercycle structure.")
            return

        self._recalculate_last_info()
        self._notify_timing_update(False)

    def _on_timing_update(self, parameterName: str, data: Dict[str, Any], header: Dict[str, Any]):
        try:
            self._error_state.remove(parameterName)
        except KeyError:
            pass

        if header.get("isFirstUpdate", False):
            # Do not report timing on the first update, as with multiple users, first updates
            # may come in an arbitrary order, which is not representative, and may result in
            # the initial state showing a very wrong thing.
            return

        # Merging data because some XTIM devices have acqStamp field, others don't. But this field may be exposed
        # in the meta information. Only when both are not found, will fall back to datetime.now()
        merged_data = {**header, **data}

        new_bp = max(merged_data.get("BASIC_PERIOD_NB", -1) - 1, -1)  # It starts counting from 1, we need from 0
        if not self.is_supercycle_mode:
            if self._last_shadow_bp != new_bp:
                self._last_shadow_bp = new_bp
                # We do not trust reported basic period number for non-supercycle accelerators, because it can be
                # lower than our imaginary period count. So we just rotate through periods of NON_SUPERCYCLE_BP_COUNT
                new_bp = (self._current_bp + 1) % self.NON_SUPERCYCLE_BP_COUNT
            else:
                # Double execution on the same event. Should not change anything
                new_bp = self._current_bp
        bp_changed = new_bp != self._current_bp
        self._current_bp = new_bp
        self._recalculate_last_info(merged_data)
        self._notify_timing_update(bp_changed)

    def _on_timing_exception(self, parameterName: str, __, exception: Exception):
        self._error_state.add(parameterName)
        self.timingErrorReceived.emit(exception.getMessage())  # type: ignore  # Java call

    def _on_xtim_exception(self, parameter_name: str, description: str, exception: Exception):
        if exception.getHeader().isFirstUpdate():   # type: ignore  # Java call
            # We should allow first update exceptions as it is likely to happen,
            # when not all users are playing (first update returns data for played users
            # and exceptions for others). This is expected, hence we should not show
            # an error to the user.
            return
        self._on_timing_exception(parameter_name, description, exception)

    def _detach_japc(self):
        japc = self._japc
        if japc:
            for sub in self._active_subs:
                # As discussed with Phil, it's better to have a risk of accessing Java API, than allow
                # clearing subscriptions by parameterName, selector (which potentially may erase subscriptions
                # done by the user from another part of the application)
                sub.set_monitoring(False)
                # TODO: This is accessing private API and should be eliminated when we move to PyJapc 3
                key = japc._transformSubscribeCacheKey(sub.param_name, sub.selector)
                try:
                    japc._subscriptionHandleDict[key].remove(sub.handler)
                except ValueError:
                    # When subscription is not part of the dictionary anymore
                    pass
            self._active_subs.clear()

            # Similar to how PyJapc does it, we need GC to clean up dangling subscriptions
            try:
                japc._java_gc.trigger()
            except AttributeError:
                # Call does not exist in earlier versions of pyjapc
                pass
        self._current_bp = -1
        self._last_shadow_bp = -1
        self._last_info = None
        self._bcd = None

    def _attach_japc(self):
        self._bcd = None
        self._listen_supercycle_updates()  # May fail if the timing domain does not expose BCD structure
        self._listen_timing_events()

    def _listen_supercycle_updates(self):
        japc = self._japc
        if japc:
            try:
                param = _CTIM_MAPPING[self._domain]
            except KeyError:
                return
            self._subscribe_japc(param=param,
                                 callback=self._on_bcd_structure_update,
                                 exception_callback=self._on_timing_exception)

    def _listen_timing_events(self):
        japc = self._japc
        if japc:
            try:
                param, sel = _XTIM_MAPPING[self._domain]
            except KeyError:
                raise ValueError(f"Unknown timing domain '{self._domain}'.")
            self._subscribe_japc(param=param,
                                 sel=sel,
                                 get_header=True,
                                 callback=self._on_timing_update,
                                 exception_callback=self._on_xtim_exception)

    def _subscribe_japc(self, param: str, callback: Callable, exception_callback: Callable, get_header: bool = False, sel: str = ""):
        if not self._japc:
            return
        # As discussed with Phil, it's better to have a risk of accessing Java API, than allow
        # clearing subscriptions by parameterName, selector (which potentially may erase subscriptions
        # done by the user from another part of the application)
        try:
            handler = self._japc.subscribeParam(parameterName=param,
                                                timingSelectorOverride=sel,
                                                getHeader=get_header,
                                                onValueReceived=callback,
                                                onException=exception_callback)
        except Exception as e:  # noqa: B902
            # Exception may happen here when PyJapc is used without GPN or TN availability and is configured for InCA
            # e.g. org.springframework.remoting.RemoteAccessException: Failed to connect to all InCA servers
            self._error_state.add(param)
            self.timingErrorReceived.emit(str(e))
            return

        sub = PyJapcSubscription(param_name=param,
                                 selector=sel,
                                 handler=handler)
        self._active_subs.append(sub)
        if self.monitoring:
            self._monitor_param(sub, monitor=True)

    def _recalculate_last_info(self, timing_update: Optional[Dict[str, Any]] = None):
        if not timing_update:
            if self._last_info:
                timestamp = self._last_info.timestamp
            else:
                timestamp = datetime.now(tz=self._tz)
        else:
            timestamp = timing_update.get("acqStamp", datetime.now(tz=self._tz))

        if self._bcd is not None:
            if timing_update is None:
                timing_update = {}
            is_normal_mode = timing_update.get("BEAM_LEVEL_NORMAL", not timing_update.get("BEAM_LEVEL_SPARE", False))
            self._bcd.spare_mode = not is_normal_mode

            # Calculate last values from BCD structure
            try:
                _, cycle = self._bcd.cycle_at_basic_period(self._current_bp)
            except ValueError:
                # Basic period may still be -1
                return

            if cycle is not None:
                self._last_info = TimingUpdate(lsa_name=cycle.lsa_name,
                                               offset=cycle.offset,
                                               user=cycle.user,
                                               timestamp=timestamp)
        elif timing_update is not None:
            # Assume equally distributed number of cycles, each of 1 basic period
            # Thus we do not extract information from the BCD structure, but expect it
            # to arrive from XTIM devices directly
            self._last_info = TimingUpdate(user=timing_update.get("USER", "---"),
                                           lsa_name=timing_update.get("lsaCycleName", "---"),
                                           offset=max(timing_update.get("BASIC_PERIOD_NB", -1) - 1, -1),
                                           timestamp=timestamp)

    def _create_supercycle(self, data: Dict[str, Any], lengths_key: str, lsa_key: str, users_key: str) -> List[TimingCycle]:
        durations = data.get(lengths_key, np.array([]))
        lsa_names = data.get(lsa_key, np.array([]))
        users = data.get(users_key, np.array([]))

        # This is a workaround for PyJapc bug (https://issues.cern.ch/browse/ACCPY-724)
        if not isinstance(durations, np.ndarray):
            durations = [durations]
        if not isinstance(lsa_names, np.ndarray):
            lsa_names = [lsa_names]
        if not isinstance(users, np.ndarray):
            users = [users]

        if not (len(durations) == len(lsa_names) == len(users)):
            raise ValueError

        res: List[TimingCycle] = []
        offset = 0
        for user, lsa_name, duration in zip(users, lsa_names, durations):
            cycle = TimingCycle(user=user,
                                lsa_name=lsa_name,
                                duration=duration,
                                offset=offset)
            offset += duration
            res.append(cycle)
        return res

    def _notify_timing_update(self, time_advanced: bool):
        if not self.has_error:
            self.timingUpdateReceived.emit(time_advanced)

    def _monitor_param(self, param: PyJapcSubscription, monitor: bool):
        try:
            param.set_monitoring(monitor)
        except Exception as e:  # noqa: B902
            self._error_state.add(param.param_name)
            self.timingErrorReceived.emit(str(e))


_XTIM_MAPPING = {
    TimingBarDomain.LHC: ("XTIM.HX.BPNM-CT/Acquisition", ""),
    TimingBarDomain.LNA: ("XTIM.AX.SBP-CT/Acquisition", "LNA.USER.ALL"),
    TimingBarDomain.PSB: ("XTIM.BX.SBP-CT/Acquisition", "PSB.USER.ALL"),
    TimingBarDomain.ADE: ("XTIM.DX.SBP-CT/Acquisition", "ADE.USER.ALL"),
    TimingBarDomain.SPS: ("XTIM.SX.SBP-CT/Acquisition", "SPS.USER.ALL"),
    TimingBarDomain.CPS: ("XTIM.PX.SBP-CT/Acquisition", "CPS.USER.ALL"),
    TimingBarDomain.LEI: ("XTIM.EX.SBP-CT/Acquisition", "LEI.USER.ALL"),
}


_CTIM_MAPPING = {
    TimingBarDomain.CPS: "PX.CZERO-CTML/SuperCycle",
    TimingBarDomain.PSB: "BX.CZERO-CTML/SuperCycle",
    TimingBarDomain.LEI: "EX.CZERO-CTML/SuperCycle",
    TimingBarDomain.SPS: "SX.CZERO-CTML/SuperCycle",
}


def import_pyjapc() -> Type:
    from accwidgets._api import assert_dependencies
    import accwidgets.timing_bar
    assert_dependencies(accwidgets.timing_bar.__file__)
    import pyjapc
    return pyjapc.PyJapc
