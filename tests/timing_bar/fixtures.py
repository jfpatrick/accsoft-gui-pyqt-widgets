import pytest
from accwidgets.timing_bar._model import TimingSuperCycle, TimingCycle


@pytest.fixture
def supercycle_obj() -> TimingSuperCycle:
    return TimingSuperCycle(normal=[TimingCycle(user="normal-user-1",
                                                lsa_name="normal-lsa-1",
                                                offset=0,
                                                duration=1),
                                    TimingCycle(user="normal-user-2",
                                                lsa_name="normal-lsa-2",
                                                offset=1,
                                                duration=3)],
                            spare=[TimingCycle(user="spare-user-1",
                                               lsa_name="spare-lsa-1",
                                               offset=0,
                                               duration=1)])
