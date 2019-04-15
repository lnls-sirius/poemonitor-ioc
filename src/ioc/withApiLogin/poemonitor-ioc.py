#!/usr/bin/python3
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
#data into the configuration file (switches.config) following it's storage pattern described on :
# <LINK DA ESPECIFICAÇÃO DO ARQUIVO DE CONFIGURAÇÃO>
#You can also check the IOC structure explanation diagram on the link below for a high level view of how
#does this IOC works.
# https://github.com/lnls-sirius/poemonitor-ioc/tree/master/IOC%20Diagrams
#It's is recommended to set the idle login timeout value in the switches that is going to be monitored
#by this IOC to the lowest value possible (Tested with 2 minutes timeout)

#Tested with python 3.6.5 and pcaspy 0.7.2

#Necessary modules
import json
import requests         #Library for making HTTP requests
from threading import Thread, Event
from pcaspy import Driver, SimpleServer, Alarm, Severity #Library creation and manipulation of EPICS PVs
from queue import Queue

#Configuration filename
CONFIG_FILE_NAME = 'switches.config'

#Delay, in seconds, to insert a new read request into a queue
SCAN_DELAY = 1

#Maximum number of request retries for considering connection lost
MAX_RETRIES = 1

#Requests timeout
REQ_TIMEOUT = 0.6

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

    def  __init__(self):
        Driver.__init__(self)

        #Read configuration file content
        self.configReader = PoemonitorConfigReader()
        self.configData = self.configReader.readFile(CONFIG_FILE_NAME)

        #Create one request queue for each switch and set their connetion status as disconnected
        for i in range(0, self.configReader.getNumberOfSwitchesFrom(self.configData)):
            self.listOfQueues.append(Queue())
            self.connectionStatusList.append(False)

        #Event object used for periodically read the PVs values
        self.event = Event()

        #Define and start the scan thread
        self.scan = Thread(target = self.scanThread)
        self.scan.setDaemon(True)
        self.scan.start()

        #Define and start all the process threads
        for i in range(0,len(self.listOfQueues)):
            th = Thread(target = self.processThread, args=[i])
            th.setDaemon(True)
            th.start()

    def scanThread(self):

        #Insert request for recovering last selection PVs values
        for queueId in range(0,len(self.listOfQueues)):
            self.listOfQueues[queueId].put({'request_type':'UPDATE_SELECTION_PVS'})

        #Periodically inserts read requests into each request queue
        while(True):
            #DEBUG
            print(self.connectionStatusList)
            for i in self.listOfQueues:
                i.put({'request_type':'READ_POE_PORT_STATUS'})
                #DEBUG
                print(i.qsize())
            self.event.wait(SCAN_DELAY)

    def processThread(self,queueId):
        #Initialize cookie for session control
        cookie = None

        while(True):

            #===========================================================#
            #==                 Try to login on switch                ==#
            #===========================================================#

            try:
                loginData = self.configReader.getLoginDataFrom(queueId,self.configData)
                #REST API request URL
                apiUrl ='http://'+ loginData['ip'] +':'+ loginData['port'] +'/rest/v3/'

                #Finish last session if it still existing
                try:
                    r = requests.request(method='delete',url=apiUrl + 'login-sessions',cookies=cookie,timeout=REQ_TIMEOUT)
                except requests.exceptions.ReadTimeout:
                    raise requests.exceptions.ConnectionError

                #REST API connection initialization
                r = requests.request(method='post',url=apiUrl + 'login-sessions', json={
                    'userName':loginData['username'],
                    'password':loginData['password']
                    },timeout=REQ_TIMEOUT)
                cookie = dict(r.json())
                self.connectionStatusList[queueId] = True

            except requests.exceptions.ConnectionError:
                print('Login Failed...')
                self.connectionStatusList[queueId] = False

            #===========================================================#
            #==      Process request when connected to switch         ==#
            #===========================================================#

            if self.connectionStatusList[queueId] == True :
                try:
                    while(True):
                         request = self.listOfQueues[queueId].get(block=True)

                         #Execute requests

                         #========Request for recovering PoE status from switch ports========
                         if request['request_type'] == 'READ_POE_PORT_STATUS':

                             #For each registered device linked to switch on configuration file
                             for device in self.configReader.getDevicesFrom(queueId,self.configData):

                                 try:
                                     #Request POE port status using switch's REST API
                                     r = requests.request(method='get',url=apiUrl + 'ports/'+device['port']+'/poe/stats',cookies=cookie,timeout=REQ_TIMEOUT)
                                 except requests.exceptions.ReadTimeout:

                                     #Set indicative alarms for signalizing problem on PVs value due to disconnnection
                                     self.setParamStatus(device['name']+':PwrState-Sts', Alarm.SCAN_ALARM, Severity.INVALID_ALARM)
                                     self.setParamStatus(device['name']+':PwrState-Raw', Alarm.SCAN_ALARM, Severity.INVALID_ALARM)
                                     self.updatePVs()

                                     #As the Sirius network is powerful and has a big bandwidth, we should not have problems related to timeouts,
                                     #so it's considered any timeout in a request as connection loss
                                     raise requests.exceptions.ConnectionError

                                 #Discard bad requests responses(It happens sometimes during switch boot as some services starts before others)
                                 if r.status_code == requests.codes.ok :
                                     r = dict(r.json())

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

                         #========Request for enabling/disabling PoE on switch ports========

                         elif request['request_type'] == 'CHANGE_POE_PORT_STATUS' :
                             if request['value'] == 0 :
                                 command = {'cmd':'no interface '+request['port']+' power-over-ethernet'}
                             else:
                                  #Request state update on switch
                                  command = {'cmd':'interface '+request['port']+' power-over-ethernet'}

                             try:
                                   #Request state update on switch
                                   r = requests.request(method='post',url=apiUrl + 'cli',data=json.dumps(command),cookies=cookie,timeout=REQ_TIMEOUT)

                             except requests.exceptions.ReadTimeout:

                                   #Set indicative alarms for signalizing problem on PVs value due to disconnnection
                                   self.setParamStatus(device['name']+':PwrState-Sel', Alarm.WRITE_ALARM, Severity.INVALID_ALARM)
                                   self.updatePVs()

                                   #As the Sirius network is powerful and has a big bandwidth, we should not have problems related to timeouts
                                   #so it's considered any timeout in a request as connection loss
                                   raise requests.exceptions.ConnectionError

                             #Discard bad requests responses(It happens sometimes during switch boot as some services starts before others)
                             if r.status_code == requests.codes.ok :

                                 #PV update
                                 self.setParam(request['reason'],request['value'])
                                 self.updatePVs()

                         #========Request for recovering selection pv values and initialize them========

                         elif request['request_type'] == 'UPDATE_SELECTION_PVS':

                              #Recover selection ṔVs last value
                              deviceNames = self.configReader.getAllDeviceNamesFrom(self.configData)
                              for i in deviceNames:
                                  #Update PVs values
                                  self.setParam(i + ':PwrState-Sel',self.getParam(i + ':PwrState-Sel'))
                                  self.updatePVs()

                #===========================================================#
                #==                    Connection lost                    ==#
                #===========================================================#

                except requests.exceptions.ConnectionError:
                    self.connectionStatusList[queueId] = False
                    print('Connection Lost...')

            #==============================================================#
            #==      Process requests when disconnected to switch        ==#
            #==============================================================#

            else:
                request = self.listOfQueues[queueId].get(block=True)

                #Set indicative alarms for signalizing disconnected PVs depending on the request type

                #Unsuccessful scan request
                if request['request_type'] == 'READ_POE_PORT_STATUS':
                    for device in self.configReader.getDevicesFrom(queueId,self.configData):
                        self.setParamStatus(device['name']+':PwrState-Sts', Alarm.SCAN_ALARM, Severity.INVALID_ALARM)
                        self.setParamStatus(device['name']+':PwrState-Raw', Alarm.SCAN_ALARM, Severity.INVALID_ALARM)
                        self.updatePVs()
                #Unsuccessful write request
                elif request['request_type'] == 'CHANGE_POE_PORT_STATUS':
                    device = request['reason']
                    self.setParamStatus(device, Alarm.WRITE_ALARM, Severity.INVALID_ALARM)
                    self.updatePVs()
                #Unsuccessful update selector Pvs request
                else:
                    deviceNames = self.configReader.getAllDeviceNamesFrom(self.configData)
                    for deviceName in deviceNames:
                        self.setParamStatus(deviceName+':PwrState-Sel', Alarm.STATE_ALARM, Severity.INVALID_ALARM)
                        self.updatePVs()

    def write(self,reason,value):

        #Get queue ID
        deviceName = reason.split(':')
        queueId = self.configReader.getQueueIdByDeviceNameFrom(deviceName[0],self.configData)

        #Get Device port
        devicePort = self.configReader.getDevicePortByDeviceNameFrom(queueId,deviceName[0],self.configData)

        #Create request
        request = {'request_type':'CHANGE_POE_PORT_STATUS','reason':reason,'port':devicePort,'value':value}
        #Check if PV has write permission
        if deviceName[1] == 'PwrState-Sel':

            self.setParam(reason,value)

            #Only insert request for valid PV names
            self.listOfQueues[queueId].put(request)
        else:
            return False

#Main routine
if __name__ == '__main__':

    #======PVs initialization======

    configReader = PoemonitorConfigReader()
    configData = configReader.readFile(CONFIG_FILE_NAME)

    prefix = 'Teste:'
    pvdb = {}
    #Recover all PV names from configuration file
    deviceNames = configReader.getAllDeviceNamesFrom(configData)

    #This configuration reader is not usefull anymore
    del configReader
    #Define all the PVs that is going to be served by the IOC
    for deviceName in deviceNames:
        pvdb[deviceName + ':PwrState-Sts'] = {'type'  :   'enum','enums' :   ['Off','On']}
        pvdb[deviceName + ':PwrState-Raw'] = {'type'  :   'string'}
        pvdb[deviceName + ':PwrState-Sel'] = {'type'  :   'enum','enums' :   ['Off','On']}

    #======IOC initialization======

    #Create PVs and start monitor threads
    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = PoemonitorDriver()


    # process CA transactions
    while True:
        server.process(0.1)
