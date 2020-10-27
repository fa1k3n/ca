*** Settings ***
Documentation	"A basic resource file"

Library		libs/centralsystem.py

*** Variables ***
${cp_id}

${cs_addr}=  %{CENTRAL_SYSTEM_IP=0.0.0.0}
${cs_port}=  %{CENTRAL_SYSTEM_PORT=9000}

*** Keywords ***
Given a connected chargepoint
      start CentralSystem  ${cs_addr}  ${cs_port}
      ${id}=  wait for ChargePoint to connect
      Sleep  1s  # Wait for possible handshake sequence
      set global variable  ${cp_id}  ${id}

when sending a TriggerMessage requesting a BootNotification
     clear msg queue  ${cp_id}
     add msg trap  ${cp_id}  BootNotification
     send TriggerMessage  ${cp_id}  BootNotification

we expect to receive a BootNotification reply within 10 seconds
   [Timeout]  10
   ${msg}=  wait for msg  ${cp_id}  BootNotification
   Should be equal as strings  ${msg.charge_point_model}  HALO
   Should be equal as strings  ${msg.charge_point_vendor}  Charge Amps
   Should be equal as strings  ${msg.meter_type}  ATM90E32AS  

set light intenisty to ${to} should change the actual value when reading back
   Given a connected chargepoint
   Set light intensity  ${cp_id}  ${to}
   ${li}=  Get light intensity  ${cp_id}
   Should be equal as integers  ${li}  ${to}
   #Sleep  2s