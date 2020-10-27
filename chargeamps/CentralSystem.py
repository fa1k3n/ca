import asyncio
import threading
import websockets
import time

from robot.api import logger
from datetime import datetime

from chargeamps import ChargePointProxy as cpp
from chargeamps import AsyncCommunicator as acomm

import functools

class CentralSystem:    
    async def __on_connect(self, websocket, path):
        charge_point_id = path.strip('/')
        
        cp = cpp.ChargePointProxy(charge_point_id, websocket)
        comm = acomm.AsyncCommunicator(functools.partial(cpp.ChargePointProxy.call, cp), asyncio.get_event_loop())
        cp.set_comm(comm)
        
        logger.console("New ChargePoint connected " + charge_point_id)
        self.__connected_chargepoints.append(cp)
        self.__conn_event.set()
        
        try:
            await cp.start()
        except websockets.exceptions.ConnectionClosedOK:
            logger.console("Connection closed by client")

    def has_connections(self):
        """
        returns if any chargepoint is connected to the central system
        """
        return len(self.__connected_chargepoints) > 0

    def find_chargepoint(self, cp_id:str):
        """
        searches amongs the connected chargepoints for a specific 
        charge point

        Paramters:
        cp_id(str): chargepoint id to find
        """
        cp = [x for x in self.__connected_chargepoints if x.id == cp_id]
        if len(cp) == 0:
            raise Exception("Chargepoint " + cp_id + " not connected")
        return cp[0]

    def serve_(self):
        self.__loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__loop)
        server = websockets.serve(
            self.__on_connect,
            self.addr,
            self.port,
            subprotocols=['ocpp1.6']
        )
        self.__loop.run_until_complete(server)
        self.__loop.run_forever()
        
    def serve(self, addr, port):
        self.__connected_chargepoints = []
        self.addr = addr
        self.port = port
        self.__conn_event = threading.Event()
        self.__thread = threading.Thread(target=self.serve_, daemon=True).start()

    def is_active(self):
        return self.__thread.running()
    
    def wait_for_connection(self):
        if not self.has_connections():
            self.__conn_event.wait()
        self.__conn_event.clear()
        return self.__connected_chargepoints[-1].id
