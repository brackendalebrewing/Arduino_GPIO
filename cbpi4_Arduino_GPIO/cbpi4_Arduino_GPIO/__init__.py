#from telemetrix import telemetrix
from telemetrix_aio import telemetrix_aio


# -*- coding: utf-8 -*-
import os
from aiohttp import web
import logging
from unittest.mock import MagicMock, patch
import asyncio
import random
from cbpi.api import *
from cbpi.api.config import ConfigType
from cbpi.api.dataclasses import Props
from cbpi.api.base import CBPiBase

import serial
import serial.tools.list_ports


#******************************************************************************************
@parameters([])
class DummySensor(CBPiSensor):

    def __init__(self, cbpi, id, props):
        super(DummySensor, self).__init__(cbpi, id, props)
        self.value = 0

    async def run(self):
        global val
        val = 55
        start = 50
        stop =75
        step = .25
        while self.running:
            #self.value = random.randint(10, 100)
            val = val + step
            self.value = val 
            if (val > stop):
                val = start
            self.log_data(self.value)

            self.push_update(self.value)
            await asyncio.sleep(1)

    def get_state(self):
        return dict(value=self.value)




#******************************************************************************************
Uno =	{
  "total_count"  : 20,
  "digital_pins":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27],
  "pwm_count": 6,
  "pwm_pins":[3,5,6,9,10,11 ],
  "analog_count":6,
  "name": "uno"
}

Nano =	{
  "total_count"  : 20,
  "digital_pins":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27],
  "pwm_count": 6,
  "pwm_pins":[3,5,6,9,10,11 ],
  "analog_count":6,
  "name": "Nano"
}

Mega =	{
  "total_count"  : 70,
  "digital_pins":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],
  "pwm_count": 15,
  "pwm_pins":[2,3,5,6,9,10,11,12,13, 44,45,46],
  "analog_count":16,
  "name": "Mega"
}

arduino_type =	{
  "type_1": Uno,
  "type_2": Nano,
  "type_3": Mega
}


global board

logger = logging.getLogger(__name__)

# creates the PCF_IO object only during startup. All sensors are using the same object
async def TelemetrixInitialize():
    global p1
    global board
    pins=[5,6,7,8]
    logger.info("***************** Start Telemetrix  ************************")
    try:
        #board = telemetrix.Telemetrix()
        find_arduino()
        # get the event loop
        loop1 = asyncio.get_event_loop()

        # instantiate pymata_express
        board =  telemetrix_aio.TelemetrixAIO(autostart=False,loop=loop1)
        await board.start_aio()
        
        
        p1=99
        pass
    except:
        p1 = None
        logging.info("Error. Could not activate Telemetrix ")
        pass

def find_arduino(port=None):
    print("find_arduino") 
    """Get the name of the port that is connected to Arduino."""
    if port is None:
        ports = serial.tools.list_ports.comports()
        if(len(ports) == 0):
            print("[ERROR] No COM ports found!")
            exit()
            
        TargetPort = None    
        for Port in ports:
            StringPort = str(Port)
            print("[INFO] Port: {}".format(StringPort))
            if("USB" in StringPort):
                TargetPort = StringPort.split(" ")[0]
                print("[INFO] Use {}...".format(TargetPort))    

        print("The serial port is -->",port) 
        print("The serial port List is -->",ports) 
        for p in ports:
            if p.manufacturer is not None and "Arduino" in p.manufacturer:
                port = p.device
                print(port)        
    return port     


# call TelemetrixInitialize function once at startup to create the TelemetrixInitialize Actor object
class AtrduinoTelemetrix(CBPiExtension):

    def __init__(self,cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.init_actor())

    async def init_actor(self):
        logger.info("Checked PCF Address")
        await asyncio.sleep(1)
        address=77
        await TelemetrixInitialize()

    """
    async def PCF8574_Address(self): 
        global PCF8574_address
        PCF8574_address= 555
        if PCF8574_address is None:
            logger.info("INIT Arduino")
            try:
                #await self.cbpi.config.add('PCF8574_Address', '0x20', ConfigType.STRING, 'PCF8574 I2C Bus address (e.g. 0x20). Change requires reboot')
                #PCF8574_Address = self.cbpi.config.get("PCF8574_Address", None)
                print("poop")
            except:
                logger.warning('Unable to update database')        
    """



#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@parameters([Property.Select(label="GPIO", options=Mega['digital_pins']), Property.Select(label="Inverted", options=["Yes", "No"],description="No: Active on high; Yes: Active on low")])
class ArduinoGPIOActor(CBPiActor):

    @action(key="Cusotm Action", parameters=[Property.Number("Value", configurable=True), Property.Kettle("Kettle")])
    async def custom_action(self, **kwargs):
        print("ACTION", kwargs)
        
    
    @action(key="Cusotm Action2", parameters=[Property.Number("Value", configurable=True)])
    async def custom_action2(self, **kwargs):
        print("ACTION2")
        

    def get_GPIO_state(self, state):
        # ON
        if state == 1:
            return 1 if self.inverted == False else 0
        # OFF
        if state == 0:
            return 0 if self.inverted == False else 1

    async def on_start(self):
        self.gpio = self.props.GPIO
        self.inverted = True if self.props.get("Inverted", "No") == "Yes" else False
        await board.set_pin_mode_digital_output(self.gpio)
        await board.digital_write(self.gpio, 0)
        await asyncio.sleep(.2)


    async def on(self, power=0):
        logger.info("ACTOR %s ON - GPIO %s " %  (self.id, self.gpio))
        await board.digital_write(self.gpio, 1)
        await asyncio.sleep(.2)
        self.state = True

    async def off(self):
        logger.info("ACTOR %s OFF - GPIO %s " % (self.id, self.gpio))
        await board.digital_write(self.gpio, 0)
        await asyncio.sleep(.2)
        self.state = False

    def get_state(self):
        return self.state
    
    async def run(self):
        while self.running == True:
            await asyncio.sleep(1)
            

@parameters([Property.Select(label="GPIO", options=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]), 
    Property.Number("Frequency", configurable=True)])
class ArduinoGPIOPWMActor(CBPiActor):
    """
    # Custom property which can be configured by the user
    @action("test", parameters={})
    async def power(self, **kwargs):        
        #self.p.ChangeDutyCycle(1)
        self.p.analog_write(self.gpio, 250)
    """

        # Custom property which can be configured by the user
    @action("Set Power", parameters=[Property.Number(label="Power", configurable=True,description="Power Setting [0-100]")])
    async def setpower(self,Power = 100 ,**kwargs):
        logging.info(Power)
        self.power=int(Power)
        if self.power < 0:
            self.power = 0
        if self.power > 100:
            self.power = 100           
        await self.set_power(self.power)
        
    async def on_start(self):
        await super().start()
        self.gpio = self.props.GPIO
        self.frequency = self.props.get("Frequency")
        await board.set_pin_mode_analog_output(self.gpio)
        print("+++++++++++++++ pwm started ++++++++++++++++++++++")
        await board.analog_write(self.gpio, 0)
        self.state = False
        self.power = None
        self.p = None
 
        pass

    async def on(self, power = None):
        logging.info("PWM Actor Power: {}".format(power))
        if power is not None:
            self.power = power
        else:
            self.power = 100

        logging.info("PWM Final Power: {}".format(self.power))    
        
        logger.info("PWM ACTOR %s ON - GPIO %s - Frequency %s - Power %s" %  (self.id, self.gpio,self.frequency,self.power))
        try:
            await board.analog_write(self.gpio, int(self.power))
            self.state = True
            await self.cbpi.actor.actor_update(self.id,self.power)
        except:
            pass

    async def off(self):
        logger.info("PWM ACTOR %s OFF - GPIO %s " % (self.id, self.gpio))
        await board.analog_write(self.gpio, 0)
        
        #self.p.stop()
        self.state = False

    async def set_power(self, power):
        print("+++++++++set power pwm ++++++++++++++")
        if self.state == True:
             await board.analog_write(self.gpio, int(power))
             #await self.p
        await self.cbpi.actor.actor_update(self.id,int(power))
        pass

    def get_state(self):
        return self.state
    
    async def run(self):
        while self.running == True:
            
            await asyncio.sleep(1)





def setup(cbpi):
    cbpi.plugin.register("DummySensor", DummySensor)
    cbpi.plugin.register("ArduinoGPIOActor", ArduinoGPIOActor)
    cbpi.plugin.register("ArduinoGPIOPWMActor", ArduinoGPIOPWMActor)    
    cbpi.plugin.register("AtrduinoTelemetrix",AtrduinoTelemetrix)
    pass