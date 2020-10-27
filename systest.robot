*** Settings ***

Resource     resources/resources.robot

*** Test Cases ***
Trigger BootNotification message
	Given a connected chargepoint
	when sending a TriggerMessage requesting a BootNotification
	we expect to receive a BootNotification reply within 10 seconds

Setting the light intensity
	[Template]  set light intenisty to ${to} should change the actual value when reading back
	1 
	25 
	75
	100 