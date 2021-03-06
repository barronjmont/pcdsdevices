import logging

from unittest.mock import Mock

from pcdsdevices.inout import InOutRecordPositioner
from pcdsdevices.ipm import IPM
from pcdsdevices.sim.pv import using_fake_epics_pv

from .conftest import connect_rw_pvs, attr_wait_true

logger = logging.getLogger(__name__)


def fake_ipm():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    ipm = IPM("Test:My:IPM", name='test_ipm')
    connect_rw_pvs(ipm.diode.state)
    connect_rw_pvs(ipm.state)
    ipm.diode.state._write_pv.put('Unknown')
    ipm.diode.state._read_pv.enum_strs = (['Unknown'] +
                                          InOutRecordPositioner.states_list)
    ipm.state._write_pv.put('Unknown')
    ipm.state._read_pv.enum_strs = ['Unknown'] + IPM.states_list
    ipm.wait_for_connection()
    return ipm


@using_fake_epics_pv
def test_ipm_states():
    logger.debug('test_ipm_states')
    ipm = fake_ipm()
    ipm.state._read_pv.put(5)
    assert ipm.removed
    assert not ipm.inserted
    ipm.state._read_pv.put(1)
    assert not ipm.removed
    assert ipm.inserted


@using_fake_epics_pv
def test_ipm_motion():
    logger.debug('test_ipm_motion')
    ipm = fake_ipm()
    # Remove IPM Targets
    ipm.remove(wait=True, timeout=1.0)
    assert ipm.state._write_pv.get() == 5
    # Insert IPM Targets
    ipm.set(1)
    assert ipm.state._write_pv.get() == 1
    # Move diodes in
    ipm.diode.insert()
    assert ipm.diode.state._write_pv.get() == 1
    ipm.diode.remove()
    # Move diodes out
    assert ipm.diode.state._write_pv.get() == 2


@using_fake_epics_pv
def test_ipm_subscriptions():
    logger.debug('test_ipm_subscriptions')
    ipm = fake_ipm()
    # Subscribe a pseudo callback
    cb = Mock()
    ipm.subscribe(cb, event_type=ipm.SUB_STATE, run=False)
    # Change the target state
    ipm.state._read_pv.put(2)
    attr_wait_true(cb, 'called')
    assert cb.called
