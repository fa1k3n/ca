import chargeamps.exceptions as err

from ocpp.v16 import ChargePoint as cp
from ocpp.routing import on
from ocpp.v16 import call_result, call

from datetime import datetime
from robot.api import logger

import queue
        
class ChargePointProxy(cp):
    """
    ChargePointProxy is the local mirroring of a connected 
    ChargePoint. The purpose is that it is used with setters
    and getters to change state of the remote chargepoint
    """

    def __init__(self, charge_point_id: str, socket, comm = None):
        """
        Constructor

        Parameters:
        charge_point_id(str): the string ID of charge point
        socket(object): the websocket to connect to
        comm(object): the communicator to use
        """
        super().__init__(charge_point_id, socket)
        self.__msgq = queue.Queue()
        self.__comm = comm
        self.__awaited_msgs = set()

    def set_comm(self, comm):
        self.__comm = comm
        
    @on('BootNotification')
    def on_boot_notification(self, **payload):
        """
        Callback function for BootNotification messages
        """
        logger.console("=> BootNotification " + str(payload))
        if "BootNotification" in self.__awaited_msgs:
            self.__msgq.put(call.BootNotificationPayload(**payload))
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=5,
            status='Accepted'
            )

    @on('Heartbeat')
    def on_heartbeat(self):
        """
        callback function for when a heartbeat is received
        """
        logger.console("=> Hearbeat")
        if "Heartbeat" in self.__awaited_msgs:
            self.__msgq.put(call.HeartbeatPayload())
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') + "Z"
            )

    @on('StatusNotification')
    def on_status_notification(self, **payload):
        """
        Callback function for StatusNotification messages
        """
        logger.console("=> StatusNotification " + str(payload))
        if "StatusNotification" in self.__awaited_msgs:
            self.__msgq.put(call.StatusNotificationPayload(**payload))
        return call_result.StatusNotificationPayload()
    
    def trigger_message(self, msg: str):
        """
        This method will do a call to the charge point requesting the 
        trigger message 

        Parametars:
        msg (str):  A string name of the message to be triggered

        Returns:
        object: The response object from the OCPP transaction
        """
        triggableMsgs = ["BootNotification", "DiagnosticsStatusNotification",
                         "FirmwareStatusNotification", "Heartbeat",
                         "MeterValues", "StatusNotification"]
        if msg not in triggableMsgs:
            raise err.TriggerMessageException("Message " + msg + " is not triggable")
        logger.console("<= TriggerMessage: " + msg)
        request = call.TriggerMessagePayload(
            requested_message = msg
            )
        resp = self.__comm.blocking_call(request)
    
        if resp.status != "Accepted":
            raise err.TriggerMessageException("Message " + msg + " was rejected, reason: " + str(resp.status))
        return resp
        
    ### Proxy configuration properties
    @property
    def light_intensity(self) -> int:
        """
        Getter method for light intensity 
        under the hood it calls the charge point with a 
        get configuration payload and awaits response

        Returns:
        int: the light intensity
        """
        # Due to how the python ocpp library builds its routing tables
        # this code needs to be included. A ticket has
        # been created on the library that fixxes this issue
        #if not hasattr(self, "_ChargePointProxy__event_loop"):
        #    return -1
        request = call.GetConfigurationPayload(
            key = ["LightIntensity"]
            )
        try:
            resp = self.__comm.blocking_call(request)
        except Exception as e:
            logger.console("ERROR: " + str(e))
            return -1
        return int(resp.configuration_key[0]["value"])
    
    @light_intensity.setter
    def light_intensity(self, val: int):
        """
        Setter method for light intensity 
        under the hood it calls the charge point with a 
        change configuration payload and awaits response

        Parameters:
        val (int): the new value, should be between 0 and 100
        """
        if val < 0 or val > 100:
            raise err.ChangeConfigurationException("Light intensity value out of range")
        
        request = call.ChangeConfigurationPayload(
            key = "LightIntensity",
            value = str(val)
            )
        resp = self.__comm.blocking_call(request)
        if resp.status != "Accepted":
            raise err.ChangeConfigurationException("Unable to change light intensity. ChargePoint reported " + str(resp.status))

    def add_msg_trap(self, msg: str):
        """
        Add message to message traps, meaning that it is awaitable

        Parameters:
        msg (str): the string name of the message
        """
        if msg not in self.__awaited_msgs:
            self.__awaited_msgs.add(msg)
            
    def wait_msg(self, msg: str = None, timeout:int =1):
        """
        Waits for a specific message. This uses the trap mechanism to acheive the effect
        once a trap is hit it is removed from the trap list

        Parameters:
        msg (str): message to wait for, if left out will wait for any message in trigger list
        timeout (int): timeout of wait, will raise TimeoutException if timeout occurs

        Returns:
        object:  the message object 
        """
        self.add_msg_trap(msg)
        try:
            recv = self.__msgq.get(timeout=timeout)
        except queue.Empty:
            raise err.TimeoutException("Wait timedout, no message received")
        self.__awaited_msgs.remove(msg)
        return recv

    def clear_msg_queue(self):
        """
        Clears the message queue
        """
        self.__msgq = queue.Queue()

