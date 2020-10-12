from unittest import mock
from datetime import datetime
from qtpy.QtCore import QTimer

try:
    from accwidgets.timing_bar._model import TimingBarModel, TimingUpdate, TimingCycle, TimingSuperCycle, TimingBarDomain
except ImportError:
    # Ignore PyJapc import error, as we are faking it here
    pass


class SampleTimingBarModel(TimingBarModel):

    def __init__(self, domain: TimingBarDomain = TimingBarDomain.PSB):
        super().__init__(japc=mock.MagicMock(), domain=domain)
        cycles = [
            TimingCycle(user="USER1",
                        lsa_name="LSA1",
                        offset=0,
                        duration=2),
            TimingCycle(user="USER2",
                        lsa_name="LSA3",
                        offset=2,
                        duration=4),
            TimingCycle(user="USER3",
                        lsa_name="LSA3",
                        offset=6,
                        duration=1),
        ]
        self._bcd = TimingSuperCycle(normal=cycles, spare=cycles, spare_mode=False)
        self._timer = QTimer()
        self._timer.timeout.connect(self._simulate_notification)
        self._timer.start(1200)
        self.timingUpdateReceived.emit(False)

    def simulate_error(self, error: str):
        self._timer.stop()
        self._error_state = set(("simulated"))
        self.timingErrorReceived.emit(error)

    def _simulate_notification(self):
        self._current_bp = (self._current_bp + 1) % 7
        _, cycle = self._bcd.cycle_at_basic_period(self._current_bp)
        self._last_info = TimingUpdate(timestamp=datetime.now(),
                                       offset=cycle.offset,
                                       user=cycle.user,
                                       lsa_name=cycle.lsa_name)
        self.timingUpdateReceived.emit(True)

    def _attach_japc(self):
        pass

    def _detach_japc(self):
        pass
