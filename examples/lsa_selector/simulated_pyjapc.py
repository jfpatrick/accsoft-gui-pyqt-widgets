# flake8: noqa: F401
from papc.interfaces.pyjapc import SimulatedPyJapc
from papc.device import Device
from papc.system import System
from papc.deviceproperty import Acquisition
from papc.fieldtype import FieldType
from papc.simulator.trig import RepeatedTimer


class DemoDevice(Device):
    frequency = 1

    def __init__(self):
        super().__init__(name='DemoDevice',
                         device_properties=(
                             Acquisition(name='Acquisition', fields=(
                                 FieldType(name='Demo', datatype='str', initial_value='Tick'),
                             )),
                         ),
                         timing_selectors=[
                             'LEI.USER.ZERO',
                             'LEI.USER.LIN3MEAS',
                         ])
        self._cnt = True
        self._timer = RepeatedTimer(1 / (self.frequency * 2), self.time_tick)
        self._timer2 = RepeatedTimer(1 / (self.frequency * 3), self.time_tick2)

    def time_tick(self):
        self.set_state({'Acquisition#Demo': f'{self._cnt!s}@LEI.USER.LIN3MEAS'}, 'LEI.USER.LIN3MEAS')
        self._cnt += 1

    def time_tick2(self):
        self.set_state({'Acquisition#Demo': f'{self._cnt!s}@LEI.USER.ZERO'}, 'LEI.USER.ZERO')
        self._cnt += 1


def create_device():
    """Entrypoint for the example to start simulating data flow."""
    d = DemoDevice()
    d.time_tick()  # Trigger the first/initial tick (gives us nicer values).
    d.time_tick2()  # Trigger the first/initial tick (gives us nicer values).
    return System(devices=[d])


PyJapc = SimulatedPyJapc.from_simulation_factory(papc_system_init=create_device)
