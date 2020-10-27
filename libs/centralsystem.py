from robot.api import logger
from chargeamps import CentralSystem as cs

import time
class centralsystem:
    ROBOT_LIBRARY_SCOPE = 'SUITE'
    
    def start_CentralSystem(self, addr, port):
        if not hasattr(self, "cs"):
            self.cs = cs.CentralSystem()
            self.cs.serve(addr, port)
        elif self.cs.addr != addr or self.cs.port != port: 
            logger.console("CentralSystem with different config, bailing")
            raise Exception("CentralSystem already running with different config")
        
    def wait_for_ChargePoint_to_connect(self):
        cp_id = self.cs.wait_for_connection()
        time.sleep(0.5)  # Sleep a bit for startup comm to finish
        return cp_id
        
    def send_TriggerMessage(self, charge_id, msg):
        chargepoint = self.cs.find_chargepoint(charge_id)
        chargepoint.trigger_message(msg)
        
    def disconnect_central_system(self):
        pass

    def clear_msg_queue(self, charge_id):
        chargepoint = self.cs.find_chargepoint(charge_id)
        chargepoint.clear_msg_queue()
        
    def wait_for_msg(self, charge_id, msg):
        chargepoint = self.cs.find_chargepoint(charge_id)
        return chargepoint.wait_msg(msg)

    def add_msg_trap(self, charge_id, msg):
        chargepoint = self.cs.find_chargepoint(charge_id)
        chargepoint.add_msg_trap(msg)
        
    def create_message(self, msgType, **kwargs):
        ret = {}
        ret["type"] = msgType
        ret["payload"] = {}
        return ret

    def set_message_field(self, msg,  field, value):
        # field is dot separated dict
        fields = field.split('.')
        if fields[0] not in msg["payload"].keys():
            msg["payload"][fields[0]] = {}
        tmp = msg["payload"][fields[0]]
        for f in fields[1:]:
            if fields.index(f) == len(fields) - 1:
                tmp[f] = value
                return 
            elif f not in tmp.keys():
                tmp[f] = {}
            tmp = tmp[f]

    def set_light_intensity(self, cp_id, intensity):
        chargepoint = self.cs.find_chargepoint(cp_id)
        chargepoint.light_intensity = int(intensity)

    def get_light_intensity(self, cp_id):
        chargepoint = self.cs.find_chargepoint(cp_id)
        return chargepoint.light_intensity
    
def main():
    sys = centralsystem()
    sys.start_CentralSystem('0.0.0.0', 9000)
    charge = sys.wait_for_ChargePoint_to_connect()
    sys.send_TriggerMessage(charge, "BootNotification")
    sys.wait_for_msg(charge, "BootNotification")
    while True:
        pass
    #sys.wait_for_msg(charge)
    #sys.disconnect_central_system()
    
if __name__ == "__main__":
    main()
    
