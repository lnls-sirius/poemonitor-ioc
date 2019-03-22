#!/usr/bin/python
# -*- coding: utf-8 -*-

#source_1 = http://docs.python-requests.org/en/master/api/#requests.Response
#source_2 = https://support.hpe.com/hpsc/doc/public/display?sp4ts.oid=7074783&docLocale=en_US&docId=emr_na-c05373669
#source_3 = https://www.w3schools.com/python/python_json.asp
#source_4 = https://docs.python.org/3/library/json.html#module-json
#source_5 = https://docs.python.org/3/library/queue.html
#source_6 = https://docs.python.org/3.4/library/threading.html
#source_7 = https://www.tutorialspoint.com/python/python_files_io.htm
#source_8 - https://www.youtube.com/watch?v=pmIm7GeOZds

import json
import requests         #Library for making HTTP requests
import threading
from time import sleep
from pcaspy import Driver, SimpleServer #Library creation and manipulation of EPICS PVs
from queue import Queue

#Configuration filename
CONFIG_FILE_NAME = 'poemonitor.config'

#Delay, in seconds, to insert a new read request into a queue
SCAN_DELAY = 1
#Maximum number of request retries for considering connection lost
MAX_RETRIES = 3
#Request queue limit size for avoiding uncontrolled growth
QUEUE_SIZE_LIMIT = 100

#PVs defenitions
prefix = 'TESTE:'
pvdb = {
    #PV base name
    'T1:PwrState-Sts' : {
        #PV atributes
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
    'T1:PwrState-Sel' : {
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    },
    'T2:PwrState-Sel' : {
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    }
}

#Class to read poemonitor-ioc configure file
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
                if j['name'] == 'T1':
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

    ListOfQueues = []
    connected = False
    def  __init__(self):
        super(PoemonitorDriver, self).__init__()

        #Read configuration file content
        self.configReader = PoemonitorConfigReader()
        self.configData = self.configReader.readFile(CONFIG_FILE_NAME)

        #Create one request queue for each switch
        for i in range(0, self.configReader.getNumberOfSwitchesFrom(self.configData)):
            self.ListOfQueues.append(Queue())

        #Event object used for periodically read the PVs values
        self.event = threading.Event()

        #Define and start the scan thread
        self.scan = threading.Thread(target = self.scanThread)
        self.scan.setDaemon(True)
        self.scan.start()

        #Define and start all the process threads
        for i in range(0,len(self.ListOfQueues)):
            th = threading.Thread(target = self.processThread, args=[i])
            th.setDaemon(True)
            th.start()

    def scanThread(self):
        '''
        self.event.wait(SCAN_INIT_DELAY)

        #Set initial value for writable PVs
        deviceNames = self.configReader.getAllDeviceNamesFrom(self.configData)
        for i in deviceNames:
            #Update PVs values
            sts = self.getParam(i + ':PwrState-Sel')
            self.setParam(i + ':PwrState-Sel',sts)
        '''
        #Periodically inserts read requests into each request queue
        while(True):
            for i in self.ListOfQueues:
                #Control for not exceeding QUEUE_SIZE_LIMIT
                if(i.qsize() < QUEUE_SIZE_LIMIT):
                    i.put({'request_type':'READ_POE_PORT_STATUS'})
                #DEBUG
                print(i.qsize())
            self.event.wait(SCAN_DELAY)

    #Thread executando essa função.
    def processThread(self,queueId):
        #Initialize cookie for session control
        cookie = None
        #Initialize connection state flag
        connected = False

        while(True):
            try:
                loginData = self.configReader.getLoginDataFrom(queueId,self.configData)
                #REST API request URL
                apiUrl ='http://'+ loginData['ip'] +':'+ loginData['port'] +'/rest/v3/'

                #Logout
                ##if cookie != None:
                    #DEBUG
                    ##print('Cookie')
                r = requests.request(method='delete',url=apiUrl + 'login-sessions',cookies=cookie)

                #REST API connection initialization
                r = requests.request(method='post',url=apiUrl + 'login-sessions', json={
                    'userName':loginData['username'],
                    'password':loginData['password']
                    })
                cookie = dict(r.json())
                connected = True
            except requests.exceptions.ConnectionError:
                print('Login Failed...')
                connected = False

            if(connected == True):
                try:
                    retries = 0
                    while(True):
                         request = self.ListOfQueues[queueId].get(block=True)

                         #Execute requests
                         if request['request_type'] == 'READ_POE_PORT_STATUS':

                             #For each device registered linked to switch on configuration file
                             for device in self.configReader.getDevicesFrom(queueId,self.configData):

                                 #Retry request control loop
                                 while (retries < MAX_RETRIES):
                                     try:
                                         #Request POE port status using switch's REST API
                                         r = requests.request(method='get',url=apiUrl + 'ports/'+device['port']+'/poe/stats',cookies=cookie,timeout=3)
                                         r = dict(r.json())
                                         break
                                     except requests.exceptions.ReadTimeout:
                                         retries += 1
                                 #In case of N_OF_RETRIES fails, consider connection lost
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

                         elif request['request_type'] == 'CHANGE_POE_PORT_STATUS' :
                             if request['value'] == 0 :
                                 #Request state update on switch
                                 command = {'cmd':'no interface '+request['port']+' power-over-ethernet'}
                                 r = requests.request(method='post',url=apiUrl + 'cli',data=json.dumps(data),cookies=cookie)

                                 #PV update
                                 self.setParam(request['reason'],request['value'])
                                 self.updatePVs()
                             else:
                                  #Request state update on switch
                                  command = {'cmd':'interface '+request['port']+' power-over-ethernet'}
                                  r = requests.request(method='post',url=apiUrl + 'cli',data=json.dumps(data),cookies=cookie)

                                  #PV update
                                  self.setParam(request['reason'],request['value'])
                                  self.updatePVs()
                except requests.exceptions.ConnectionError:
                    print('Connection Lost...')

    def write(self,reason,value):

        #Get queue ID
        deviceName = reason.split(':')
        queueId = self.configReader.getQueueIdByDeviceNameFrom(deviceName[0],self.configData)

        #Get Device port
        devicePort = self.configReader.getDevicePortByDeviceNameFrom(queueId,deviceName[0],self.configData)

        #Create request
        request = {'request_type':'CHANGE_POE_PORT_STATUS','reason':reason,'port':devicePort,'value':value}

        #Check if PV has write permission
        if reason == 'T1:PwrState-Sel' or reason == 'T2:PwrState-Sel':

            #Only insert request for valid PV names
            self.ListOfQueues[queueId].put(request)
        else:
            return False

#Main routine
if __name__ == '__main__':

    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = PoemonitorDriver()

    # process CA transactions
    while True:
        server.process(0.1)

'''
#Request poe port status from all switch ports
service = 'poe/ports/stats'

r = req.request('get',service,cookie)
#Print data
r = dict(r.json())
for v in r['port_poe_stats']:
    print('Port: ' + v['port_id'] + '   status: ' + v['poe_detection_status'])

'''
