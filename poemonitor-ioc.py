#!/usr/bin/python
# -*- coding: utf-8 -*-

#Source links used for developing this IOC

#source_1 = http://docs.python-requests.org/en/master/api/#requests.Response
#source_2 = https://support.hpe.com/hpsc/doc/public/display?sp4ts.oid=7074783&docLocale=en_US&docId=emr_na-c05373669
#source_3 = https://www.w3schools.com/python/python_json.asp
#source_4 = https://docs.python.org/3/library/json.html#module-json
#source_5 = https://docs.python.org/3/library/queue.html
#source_6 = https://docs.python.org/3.4/library/threading.html
#source_7 = https://www.tutorialspoint.com/python/python_files_io.htm
#source_8 - https://www.youtube.com/watch?v=pmIm7GeOZds

#Developer: Paulo Baraldi Mausbach

#poemonitor-ioc.py

#This program is used for monitoring the ports power-over-ethernet (PoE) status from switches Aruba 2930M
#used on the network infrastructure at Sirius. It also permits to enable/disable PoE interface from ports
#through caput requests. For start/stop monitoring switches/devices it's necessary to insert/remove their
#data into the configuration file (peomonitor.config) following it's storage pattern described on :
# <LINK DA ESPECIFICAÇÃO DO ARQUIVO DE CONFIGURAÇÃO>
#You can also check the IOC structure explanation diagram on the link below for a high level view of how
#does this IOC worksself.
# <LINK DO DIAGRAMA DE ESTRUTURA DO CÓDIGO>

#Tested with python 3.6.5 and pcaspy 0.7.2

#Necessary modules

import json
import requests         #Library for making HTTP requests
import threading
from time import sleep
from pcaspy import Driver, SimpleServer, Alarm, Severity #Library creation and manipulation of EPICS PVs
from queue import Queue

#Configuration filename
CONFIG_FILE_NAME = 'poemonitor.config'

#Delay, in seconds, to insert a new read request into a queue
SCAN_DELAY = 1

#Maximum number of request retries for considering connection lost
MAX_RETRIES = 3


prefix = 'Teste:'
pvdb = {

    #PoE status PVs

    'T1:PwrState-Sts' : {
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    },
    'T2:PwrState-Sts' : {

        'type'  :   'enum',
        'enums' :   ['Off','On'],
    },
    'T1:PwrState-Raw' : {
        'type'  :   'string'
    },
    'T2:PwrState-Raw' : {
        'type'  :   'string'
    },

    #PoE enable/disable selector PVs

    'T1:PwrState-Sel' : {
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    },
    'T2:PwrState-Sel' : {
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    }
}

#Class responsible for reading poemonitor-ioc configuration file
class PoemonitorConfigReader():

    def readFile(self,fileName):
        with open(fileName,'r') as f:
            fileData = json.loads(f.read())
        return fileData

    def getNumberOfSwitchesFrom(self,fileData):
        return len(fileData['switches'])

    def getLoginDataFrom(self,queueId,fileData):
        return fileData['switches'][queueId]['login_data']

    def getDevicesFrom(self,queueId,fileData):
        return fileData['switches'][queueId]['devices']

    def getQueueIdByDeviceNameFrom(self,deviceName,fileData):
        for i in range(0, len(fileData['switches'])):
            for j in fileData['switches'][i]['devices']:
                if j['name'] == deviceName:
                    return i
        return False

    def getDevicePortByDeviceNameFrom(self,queueId,deviceName,fileData):
        for i in fileData['switches'][queueId]['devices']:
            if deviceName in i["name"]:
                return i['port']

    def getAllDeviceNamesFrom(self,fileData):
        devices = []
        for switch in fileData['switches']:
            for device in switch['devices']:
                devices.append(device['name'])
        return devices

#Class responsible for reacting to PV read/write requests
class PoemonitorDriver(Driver):

    connectionStatusList = []
    listOfQueues = []
    connected = False
    def  __init__(self):
        super(PoemonitorDriver, self).__init__()

        #Read configuration file content
        self.configReader = PoemonitorConfigReader()
        self.configData = self.configReader.readFile(CONFIG_FILE_NAME)

        #Create one request queue for each switch and set their connetion status as disconnected
        for i in range(0, self.configReader.getNumberOfSwitchesFrom(self.configData)):
            self.listOfQueues.append(Queue())
            self.connectionStatusList.append(False)

        #Event object used for periodically read the PVs values
        self.event = threading.Event()

        #Define and start the scan thread
        self.scan = threading.Thread(target = self.scanThread)
        self.scan.setDaemon(True)
        self.scan.start()

        #Define and start all the process threads
        for i in range(0,len(self.listOfQueues)):
            th = threading.Thread(target = self.processThread, args=[i])
            th.setDaemon(True)
            th.start()

    def scanThread(self):

        #Insert request for recovering last selection PVs values
        for queueId in range(0,len(self.listOfQueues)):
            self.listOfQueues[queueId].put({'request_type':'UPDATE_SELECTION_PVS'})

        #Periodically inserts read requests into each request queue
        while(True):
            queueId = 0
            print(self.connectionStatusList)
            for i in self.connectionStatusList:
                #Check if switch is connected
                if(i == True):
                    self.listOfQueues[queueId].put({'request_type':'READ_POE_PORT_STATUS'})
                #DEBUG
                print(self.listOfQueues[queueId].qsize())
                queueId += 1
            self.event.wait(SCAN_DELAY)

    def processThread(self,queueId):
        #Initialize cookie for session control
        cookie = None

        while(True):
            try:
                loginData = self.configReader.getLoginDataFrom(queueId,self.configData)
                #REST API request URL
                apiUrl ='http://'+ loginData['ip'] +':'+ loginData['port'] +'/rest/v3/'

                #Logout - No problem if not logged in
                    #DEBUG
                    ##if cookie != None:
                    ##print('Cookie')
                r = requests.request(method='delete',url=apiUrl + 'login-sessions',cookies=cookie)

                #REST API connection initialization
                r = requests.request(method='post',url=apiUrl + 'login-sessions', json={
                    'userName':loginData['username'],
                    'password':loginData['password']
                    })
                cookie = dict(r.json())
                self.connectionStatusList[queueId] = True
            except requests.exceptions.ConnectionError:
                print('Login Failed...')
                self.connectionStatusList[queueId] = False

            if(self.connectionStatusList[queueId] == True):
                try:
                    retries = 0
                    while(True):
                         request = self.listOfQueues[queueId].get(block=True)

                         #Execute requests

                         #========REQUEST FOR RECOVERING POE STATUS FROM SWITCH PORTS========
                         if request['request_type'] == 'READ_POE_PORT_STATUS':

                             #For each registered device linked to switch on configuration file
                             for device in self.configReader.getDevicesFrom(queueId,self.configData):

                                 #Retry request control loop
                                 while (retries < MAX_RETRIES):
                                     try:
                                         #Request POE port status using switch's REST API
                                         r = requests.request(method='get',url=apiUrl + 'ports/'+device['port']+'/poe/stats',cookies=cookie,timeout=10)
                                         r = dict(r.json())
                                         break
                                     except requests.exceptions.ReadTimeout:
                                         retries += 1

                                 #In case of MAX_RETRIES fails, consider connection lost
                                 if(retries >= MAX_RETRIES):
                                     raise requests.exceptions.ConnectionError
                                 else:
                                     retries = 0
                                 #DEBUG
                                 #print('updated PVs     queueID = ' + str(queueId))
                                 print('Port: ' + r['port_id'] + '   status: ' + r['poe_detection_status'])

                                 #Update PVs values
                                 self.setParam(device['name']+':PwrState-Raw',r['poe_detection_status'])

                                 if r['poe_detection_status'] == 'PPDS_DELIVERING' :
                                     self.setParam(device['name']+':PwrState-Sts',1)
                                 else:
                                     self.setParam(device['name']+':PwrState-Sts',0)
                                 self.updatePVs()

                         #========REQUEST FOR ENABLING/DISABLING POE ON SWITCH PORTS========

                         elif request['request_type'] == 'CHANGE_POE_PORT_STATUS' :
                             if request['value'] == 0 :

                                 command = {'cmd':'no interface '+request['port']+' power-over-ethernet'}

                                 #Retry request control loop
                                 while (retries < MAX_RETRIES):
                                     try:
                                          #Request state update on switch
                                          r = requests.request(method='post',url=apiUrl + 'cli',data=json.dumps(command),cookies=cookie,timeout=10)
                                          break
                                     except requests.exceptions.ReadTimeout:
                                          retries += 1

                                  #In case of MAX_RETRIES fails, consider connection lost
                                 if(retries >= MAX_RETRIES):
                                     raise requests.exceptions.ConnectionError
                                 else:
                                     retries = 0

                                 #PV update
                                 self.setParam(request['reason'],request['value'])
                                 self.updatePVs()
                             else:
                                  #Request state update on switch
                                  command = {'cmd':'interface '+request['port']+' power-over-ethernet'}

                                  #Retry request control loop
                                  while (retries < MAX_RETRIES):
                                      try:
                                           #Request state update on switch
                                           r = requests.request(method='post',url=apiUrl + 'cli',data=json.dumps(command),cookies=cookie,timeout=10)
                                           break
                                      except requests.exceptions.ReadTimeout:
                                           retries += 1

                                  #In case of MAX_RETRIES fails, consider connection lost
                                  if(retries >= MAX_RETRIES):
                                      raise requests.exceptions.ConnectionError
                                  else:
                                      retries = 0

                                  #PV update
                                  self.setParam(request['reason'],request['value'])
                                  self.updatePVs()

                          #========REQUEST FOR RECOVERING SELECTION PV VALUES AND INITIALIZE THEM========

                         elif request['request_type'] == 'UPDATE_SELECTION_PVS':

                              #Recover selection ṔVs last value
                              deviceNames = self.configReader.getAllDeviceNamesFrom(self.configData)
                              for i in deviceNames:
                                  #Update PVs values
                                  self.setParam(i + ':PwrState-Sel',self.getParam(i + ':PwrState-Sel'))
                                  self.updatePVs()

                except requests.exceptions.ConnectionError:
                    self.connectionStatusList[queueId] = False
                    #Remove all requests inserted while switch has been disconnected
                    self.listOfQueues[queueId].queue.clear()
                    #Insert request for recovering last selection PVs values
                    self.listOfQueues[queueId].put({'request_type':'UPDATE_SELECTION_PVS'})
                    print('Connection Lost...')

    def write(self,reason,value):

        print(reason)
        #Get queue ID
        deviceName = reason.split(':')
        queueId = self.configReader.getQueueIdByDeviceNameFrom(deviceName[0],self.configData)

        #Continue caput request only if device's respective switch is connected
        if(self.connectionStatusList[queueId] == True):
            #Get Device port
            devicePort = self.configReader.getDevicePortByDeviceNameFrom(queueId,deviceName[0],self.configData)

            #Create request
            request = {'request_type':'CHANGE_POE_PORT_STATUS','reason':reason,'port':devicePort,'value':value}

            #Check if PV has write permission
            if reason == 'T1:PwrState-Sel' or reason == 'T2:PwrState-Sel':

                #Only insert request for valid PV names
                self.listOfQueues[queueId].put(request)
            else:
                return False
        else:
            #Signalize unsuccessful write request due to connection problem
            self.setParam(reason,self.getParam(reason))
            self.setParamStatus(reason, Alarm.WRITE_ALARM, Severity.INVALID_ALARM)
            self.updatePVs()

#Main routine
if __name__ == '__main__':

    #Create PVs and start monitor threads
    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = PoemonitorDriver()

    # process CA transactions
    while True:
        server.process(0.1)
