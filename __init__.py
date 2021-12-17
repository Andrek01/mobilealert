#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2020-      <AUTHOR>                                  <EMAIL>
#########################################################################
#  This file is part of SmartHomeNG.
#  https://www.smarthomeNG.de
#  https://knx-user-forum.de/forum/supportforen/smarthome-py
#
#  Sample plugin for new plugins to run with SmartHomeNG version 1.5 and
#  upwards.
#
#  SmartHomeNG is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHomeNG is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHomeNG. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################


import sys
import requests
from bs4 import BeautifulSoup
import json
import datetime
import hashlib
import time


from lib.model.smartplugin import *
from lib.item import Items

from .webif import WebInterface



class Sensor(object):
    def __init__(self, id):
        self.id = id
        self.name = ""
        self.values = {}


class Sensors(object):
    def __init__(self):
        self.sensors = {}

    def exists(self, id):
        return id in self.sensors

    def get(self, id):
        return self.sensors[id]

    def put(self, Sensor):
        self.sensors[Sensor.id] = Sensor



sys.path.append('/devtools/eclipse/plugins/org.python.pydev.core_8.1.0.202012051215/pysrc')
import pydevd

# If a needed package is imported, which might be not installed in the Python environment,
# add it to a requirements.txt file within the plugin's directory


class mobile_alert(SmartPlugin):
    """
    Main class of the Plugin. Does all plugin specific stuff and provides
    the update functions for the items
    """

    PLUGIN_VERSION = '1.0.0'    # (must match the version specified in plugin.yaml), use '1.0.0' for your initial plugin Release

    def __init__(self, sh):
        """
        Initalizes the plugin.

        If you need the sh object at all, use the method self.get_sh() to get it. There should be almost no need for
        a reference to the sh object any more.

        Plugins have to use the new way of getting parameter values:
        use the SmartPlugin method get_parameter_value(parameter_name). Anywhere within the Plugin you can get
        the configured (and checked) value for a parameter by calling self.get_parameter_value(parameter_name). It
        returns the value in the datatype that is defined in the metadata.
        """
        # internal Values of the plugin
        self.Sensors = Sensors()
        self._phoneID = self.get_parameter_value('phone_id')
        self.items = Items.get_instance()
        
        # Call init code of parent class (SmartPlugin)
        super().__init__()

        # get the parameters for the plugin (as defined in metadata plugin.yaml):
        # self.param1 = self.get_parameter_value('param1')

        # cycle time in seconds, only needed, if hardware/interface needs to be
        # polled for value changes by adding a scheduler entry in the run method of this plugin
        # (maybe you want to make it a plugin parameter?)
        self._cycle = self.get_parameter_value('update_cycle')        

        # Initialization code goes here

        # On initialization error use:
        #   self._init_complete = False
        #   return

        # if plugin should start even without web interface
        self.init_webinterface(WebInterface)
        # if plugin should not start without web interface
        # if not self.init_webinterface():
        #     self._init_complete = False

        return

    def run(self):
        """
        Run method for the plugin
        """
        #pydevd.settrace("192.168.178.37", port=5678)
        self.logger.debug("Run method called")
        # setup scheduler for device poll loop   (disable the following line, if you don't need to poll the device. Rember to comment the self_cycle statement in __init__ as well)
        self.poll_device()
        self.scheduler_add('poll_device', self.poll_device, cycle=self._cycle)

        self.alive = True
        # if you need to create child threads, do not make them daemon = True!
        # They will not shutdown properly. (It's a python bug)

    def stop(self):
        """
        Stop method for the plugin
        """
        self.logger.debug("Stop method called")
        self.scheduler_remove('poll_device')
        self.alive = False

    def parse_item(self, item):
        """
        Default plugin parse_item method. Is called when the plugin is initialized.
        The plugin can, corresponding to its attribute keywords, decide what to do with
        the item in future, like adding it to an internal array for future reference
        :param item:    The item to process.
        :return:        If the plugin needs to be informed of an items change you should return a call back function
                        like the function update_item down below. An example when this is needed is the knx plugin
                        where parse_item returns the update_item function when the attribute knx_send is found.
                        This means that when the items value is about to be updated, the call back function is called
                        with the item, caller, source and dest as arguments and in case of the knx plugin the value
                        can be sent to the knx with a knx write function within the knx plugin.
        """
        if self.has_iattr(item.conf, 'mobile_alert_id'):
            #pydevd.settrace("192.168.178.37", port=5678)
            self.logger.debug("parse item: {}".format(item))
            if (self.Sensors.exists(item.conf['mobile_alert_id'])):
                actSensor = self.Sensors.get(item.conf['mobile_alert_id'])
                actSensor.values[item.conf['mobile_alert_index']] = "{}".format(item)
            else:
                self.Sensors.put(Sensor(item.conf['mobile_alert_id']))
                actSensor = self.Sensors.get(item.conf['mobile_alert_id'])
                actSensor.Name = ""
                actSensor.values[item.conf['mobile_alert_index']] = "{}".format(item)
            
            return None
        # todo
        # if interesting item for sending values:
        #   return self.update_item

    def parse_logic(self, logic):
        """
        Default plugin parse_logic method
        """
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def update_item(self, item, caller=None, source=None, dest=None):
        """
        Item has been updated

        This method is called, if the value of an item has been updated by SmartHomeNG.
        It should write the changed value out to the device (hardware/interface) that
        is managed by this plugin.

        :param item: item to be updated towards the plugin
        :param caller: if given it represents the callers name
        :param source: if given it represents the source
        :param dest: if given it represents the dest
        """
        if self.alive and caller != self.get_shortname():
            # code to execute if the plugin is not stopped
            # and only, if the item has not been changed by this this plugin:
            self.logger.info("Update item: {}, item has been changed outside this plugin".format(item.id()))

            if self.has_iattr(item.conf, 'foo_itemtag'):
                self.logger.debug("update_item was called with item '{}' from caller '{}', source '{}' and dest '{}'".format(item,
                                                                                                               caller, source, dest))
            pass

    def poll_device(self):
        """
        Polls for updates of the device

        This method is only needed, if the device (hardware/interface) does not propagate
        changes on it's own, but has to be polled to get the actual status.
        It is called by the scheduler which is set within run() method.
        """
        #pydevd.settrace("192.168.178.37", port=5678)
        myResult = self._get_Data_by_Rest()
        if (myResult == True):
            return
        else:
            self._get_Data_by_HTML()
        
    
    def _get_Data_by_HTML(self):
        myResponse = requests.post('https://measurements.mobile-alerts.eu'+ '?phoneid=' + self._phoneID)
        myText = myResponse.text
        
        # Now get the soup
        soup = BeautifulSoup(myText, "html.parser")
        
        inputSensors=soup.select("div[class='sensor']")
        for entry in inputSensors:
            myComponentCollection = entry.select("div[class='sensor-component']")
            myID = ""
            myValue = ""
            for component in myComponentCollection:
                key = str(component.select("h5")[0]).replace("<h5>","").replace("</h5>","")
                value = str(component.select("h4")[0]).replace("<h4>","").replace("</h4>","")
                myResult = key +" : " +  value 
                print (myResult)
                if (key == 'ID'):
                    myID = value
                if (key == 'Temperatur' or key == 'Luftfeuchte' or key == 'Regen' or key == 'Windgeschwindigkeit' or 'Temperatur' in key):
                    myValue = value
            
            # Write to Item if values found
            if (myValue != "" and myID != ""):
                if (self.Sensors.exists(myID) ==True):
                    mySensor = self.Sensors.get(myID)
                    item = self.items.return_item(mySensor.item)  
                    if (item != None): 
                        item(float(myValue.split(" ")[0].replace(",",".")), self.get_shortname())
                myValue = ""
        
    def _get_Data_by_Rest(self):
        #sensors =  set(['02232A5ED0BC','06109E8993C7'])
        #pydevd.settrace("192.168.178.37", port=5678)
        sensors = []
        for mySensor in self.Sensors.sensors:
            sensors.append(mySensor)

        devicetoken = 'empty'                                   # defaults to "empty"
        vendorid = '7be5c039-f650-439e-887f-f410b3c959db'       # iOS vendor UUID (returned by iOS, any UUID will do). Launch uuidgen from the terminal to generate a fresh one.
        phoneid = 'Unknown'                                     # Phone ID - probably generated by the server based on the vendorid (this string can be "Unknown" and it still works)
        version = '1.35'                                        # Info.plist CFBundleShortVersionString
        build = '132'                                           # Info.plist CFBundleVersion
        executable = 'Mobile Alerts'                            # Info.plist CFBundleExecutable
        bundle = 'de.synertronixx.remotemonitor'                # [[NSBundle mainBundle] bundleIdentifier]
        lang = 'en'                                             # preferred language
        
        request = "devicetoken=%s&vendorid=%s&phoneid=%s&version=%s&build=%s&executable=%s&bundle=%s&lang=%s" % (devicetoken,vendorid,phoneid,version,build,executable,bundle,lang)
        request += '&timezoneoffset=%d' % 60                    # local offset to UTC time
        request += '&timeampm=%s' % ('true')                    # 12h vs 24h clock
        request += '&usecelsius=%s' % ('true')                  # Celcius vs Fahrenheit
        request += '&usemm=%s' % ('true')                       # mm va in
        request += '&speedunit=%d' % 0                          # wind speed (0: m/s, 1: km/h, 2: mph, 3: kn)
        # current UTC timestamp
        request += '&timestamp=%s' %  str(datetime.datetime.utcnow().timestamp()).split(".")[0] 
        
        requestMD5 = request + 'uvh2r1qmbqk8dcgv0hc31a6l8s5cnb0ii7oglpfj'    # SALT for the MD5
        requestMD5 = requestMD5.replace('-','')
        requestMD5 = requestMD5.replace(',','')
        requestMD5 = requestMD5.replace('.','')
        requestMD5 = requestMD5.lower()
        requestMD5 = requestMD5.encode('utf-8')
        
        m = hashlib.md5()
        m.update(requestMD5)
        hexdig = m.hexdigest()
        
        request += '&requesttoken=%s' % hexdig
        
        request += '&deviceids=%s' % ','.join(sensors)
        #request += '&measurementfroms=%s' % ('0,' * len(sensors))
        #request += '&measurementcounts=%s' % ('50,' * len(sensors))
        
        http_header = {
                        "User-Agent" : "remotemonitor/248 CFNetwork/758.2.8 Darwin/15.0.0",
                        "Accept-Language" : "en-us",
                        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                        "Host" : "www.data199.com:8080",
                        }
        
        
        # create your HTTP request
        myResponse = requests.post('https://www.data199.com/api/v1/dashboard',headers=http_header,data=request)
        
        self.logger.debug("got Reponse from www.data199.com - Statuscode : {}".format(myResponse.status_code))
        myResult = json.loads(myResponse.content.decode())
        self.logger.debug("Success-State from www.data199.com - Success : {}".format(myResult['success']))
        if (myResult['success'] == False):
            return False
        
        #pydevd.settrace("192.168.178.37", port=5678)
        for myDevice in myResult['result']['devices']: 
            myID = myDevice['deviceid']
            if (self.Sensors.exists(myID) ==True):
                mySensor = self.Sensors.get(myID)
                if 'lowbattery' in mySensor.values:
                    myItem = mySensor.values['lowbattery']
                    item = self.items.return_item(myItem)  
                    if (item != None): 
                        item(myDevice['lowbattery'], self.get_shortname())
                
                # Write values to items
                for Entry in mySensor.values:
                    if Entry in myDevice['measurements'][0]:
                        try:
                            myItem = mySensor.values[Entry]
                            item = self.items.return_item(myItem)  
                            if (item != None): 
                                item(float(myDevice['measurements'][0][Entry]), self.get_shortname())
                        except Exception as err:
                            self.logger.debug("Problem by settings item-value for : {} Device-ID : {}".format(Entry, myID))
        return True