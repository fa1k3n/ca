import unittest
from unittest.mock import Mock
from ocpp.v16 import call_result, call

from chargeamps.ChargePointProxy import ChargePointProxy
import chargeamps.exceptions as err

class MockSocket:
    def __init__(self):
        pass
    
class TestChargePointProxy(unittest.TestCase):

    def test_set_light_intensity_with_accepted_answer(self):
        """
        Test that it is possible to set light intensity
        
        Acceptable values are 0 - 100 
        """
        comm = Mock()
        comm.blocking_call.return_value=call_result.ChangeConfigurationPayload(status='Accepted')
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        for i in range(0, 110, 10):
            cpp.light_intensity = i
            comm.blocking_call.assert_called_with(call.ChangeConfigurationPayload(key='LightIntensity', value=str(i)))

    def test_set_light_intensity_with_rejected_answer(self):
        """
        Test that an exception is raised if server reports reject on a set light intensity
        """
        comm = Mock()
        comm.blocking_call.return_value=call_result.ChangeConfigurationPayload(status='Rejected')
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        with self.assertRaises(err.ChangeConfigurationException) as e:
            cpp.light_intensity = 90

    def test_set_light_intensity_with_value_out_of_range(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        with self.assertRaises(err.ChangeConfigurationException) as e:
            cpp.light_intensity = 110

    def test_get_light_intensity(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        for i in range(0, 110, 10):
            comm.blocking_call.return_value=call_result.GetConfigurationPayload(
            configuration_key=[{'key': "LightIntensity", 'readonly': False, 'value': str(i)}]
            )
            self.assertEqual(cpp.light_intensity, i)
            comm.blocking_call.assert_called_with(call.GetConfigurationPayload(key=['LightIntensity']))

    def test_trigger_message(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        comm.blocking_call.return_value=call_result.TriggerMessagePayload(status='Accepted')
        cpp.trigger_message("Heartbeat")
        comm.blocking_call.assert_called_with(call.TriggerMessagePayload(requested_message="Heartbeat"))

    def test_trigger_message_with_rejected_response(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        comm.blocking_call.return_value=call_result.TriggerMessagePayload(status='Rejected')
        with self.assertRaises(err.TriggerMessageException) as e:
            cpp.trigger_message("Heartbeat")
        comm.blocking_call.assert_called()

    def test_trigger_message_that_is_not_allowed_to_trigger(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        with self.assertRaises(err.TriggerMessageException) as e:
            cpp.trigger_message("StopTransaction")
        comm.blocking_call.assert_not_called()

    def test_heartbeat_handler(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        res = cpp.on_heartbeat()
        self.assertTrue(isinstance(res, call_result.HeartbeatPayload))

    def test_heartbeat_handler_with_msg_trap(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        cpp.add_msg_trap("Heartbeat")
        cpp.on_heartbeat()
        msg = cpp.wait_msg("Heartbeat")
        self.assertTrue(isinstance(msg, call.HeartbeatPayload))

    def test_wait_for_message_with_timeout(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        cpp.on_heartbeat()
        with self.assertRaises(err.TimeoutException) as e:
            msg = cpp.wait_msg("Heartbeat", 0.1)

    def test_when_a_message_trigger_occurs_the_trigger_is_removed(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        cpp.add_msg_trap("Heartbeat")
        cpp.on_heartbeat()
        msg = cpp.wait_msg("Heartbeat")
        self.assertTrue(isinstance(msg, call.HeartbeatPayload))
        with self.assertRaises(err.TimeoutException) as e:
            msg = cpp.wait_msg("Heartbeat", 0.1)

    def test_wait_message_without_message_argument(self):
        comm = Mock()
        socket = MockSocket()
        cpp = ChargePointProxy("CP1", socket, comm)
        cpp.add_msg_trap("Heartbeat")
        cpp.on_heartbeat()
        msg = cpp.wait_msg()
        self.assertTrue(isinstance(msg, call.HeartbeatPayload))
        
if __name__ == '__main__':
    unittest.main()
