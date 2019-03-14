#!/usr/bin/python
# -*- coding: utf-8 -*-

#source_1 = http://docs.python-requests.org/en/master/api/#requests.Response
#source_2 = https://support.hpe.com/hpsc/doc/public/display?sp4ts.oid=7074783&docLocale=en_US&docId=emr_na-c05373669
#source_3 = https://www.w3schools.com/python/python_json.asp
#source_4 = https://docs.python.org/3/library/json.html#module-json
#source_5 = https://docs.python.org/3/library/queue.html
#source_6 = https://docs.python.org/3.4/library/threading.html
#source_7 = https://www.tutorialspoint.com/python/python_files_io.htm

import json
import requests         #Library for making HTTP requests
import threading
from time import sleep
from pcaspy import Driver, SimpleServer #Library creation and manipulation of EPICS PVs
from queue import Queue

#Login Data
USERNAME = 'controle'
PASSWORD = 'teste'

#Switch Address Data
IP = '10.129.0.100'
PORT = '80'

#Configuration filename
CONFIG_FILE_NAME = "poemonitor.config"

#Delay, in seconds, to insert a new read request into a queue
SCAN_DELAY = 1

#PVs defenitions
prefix = 'TESTE:'
pvdb = {
    #PV base name
    'T1' : {
        #PV atributes
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    },
    'T2' : {

        'type'  :   'enum',
        'enums' :   ['Off','On'],
    },
    'STATUS' : {
        'type'  :   'string'
    }
}

#Class to perform requests for an Aruba switch via it's REST API
class ArubaApiRequester():

    #Constructor
    def __init__(self,ip,port):
        self.apiIp = ip
        self.apiPort = port
        self.apiUrl = 'http://'+ self.apiIp +':'+ self.apiPort +'/rest/v1/'

    #Functions
    def login(self,username,password):
        try:
            service = 'login-sessions'
            r = requests.post(self.apiUrl + '' + service,json={
                "userName":username,
                "password":password,
                })
            self.cookie = dict(r.json())
            return r
        except:
            print('Login attempt failed')
            return r

    def request(self,httpMethod,service):
        try:
            if(httpMethod == 'get'):
                r = requests.get(self.apiUrl + '' + service,cookies=self.cookie)
                return r
            elif(httpMethod == 'post'):
                r = requests.post(self.apiUrl + '' + service,cookies=self.cookie)
                return r
            elif(httpMethod == 'put'):
                r = requests.put(self.apiUrl + '' + service,cookies=self.cookie)
                return r
            elif(httpMethod == 'delete'):
                r = requests.delete(self.apiUrl + '' + service,cookies=self.cookie)
                return r
        except:
            print('Request failed')
            return r

#Class to read poemonitor-ioc configure file
class PoemonitorConfigReader():

    def readFile(self,fileName):
        with open(fileName,'r') as f:
            fileData = json.loads(f.read())
        return fileData

    def getNumberOfSwitchesFrom(self,fileData):
        return len(fileData["switches"])

#Class responsible for reacting to PV read/write requests
class PoemonitorDriver(Driver):

    ListOfQueues = []

    def  __init__(self):
        super(PoemonitorDriver, self).__init__()

        #REST API connection initialization
        req = ArubaApiRequester(IP,PORT)
        r = req.login(USERNAME,PASSWORD)
        self.cookie = dict(r.json())

        #Read configuration file content
        configReader = PoemonitorConfigReader()
        self.configData = configReader.readFile(CONFIG_FILE_NAME)

        #Create one request queue for each switch
        for i in range(0, configReader.getNumberOfSwitchesFrom(self.configData)):
            self.ListOfQueues.append(Queue())

        #Event object used for periodically read the PVs values
        self.event = threading.Event()

        #Define and start the scan thread
        self.scan = threading.Thread(target = self.scanThread)
        self.scan.setDaemon(True)
        self.scan.start()

        #Define and start all the process threads
        self.processList = []
        for i in range(0,len(self.ListOfQueues)):
            th = threading.Thread(target = self.processThread, args=[i])
            th.setDaemon(True)
            th.start()
            self.processList.append(th)

    def scanThread(self):

        #Periodically inserts read requests into each request queue
        while(True):
            for i in self.ListOfQueues:
                i.put(["READ_POE_PORT_STATUS"])
                print(i.qsize())
            self.event.wait(SCAN_DELAY)

    def processThread(self,queueId):

        '''
        while(True):
            for i in self.ListOfQueues:
                print(i.qsize())
            self.event.wait(4)

        #################LOOP DE CONSUMO################
        '''
        while(True):
             request = self.ListOfQueues[queueId].get(block=True)

             #if(request[0] == "READ_POE_PORT_STATUS"):
                 #print("Updated PVs     queueID = " + str(queueId))



        '''
        #Request poe port status of one port
        service = 'ports/3/poe/stats'
        r = req.request('get',service)
        r = dict(r.json())

        print('Port: ' + r['port_id'] + '   status: ' + r['poe_detection_status'])

        if(r['poe_detection_status'] == 'PPDS_DELIVERING'):
            self.setParam('T1', 1)
        else:
            self.setParam('T1',0)

        self.setParam('T2', 0)
        self.setParam('STATUS',r['poe_detection_status'])
        '''

        #Responsável por tratar('consumir') cada requisição dentro da fila. Cada fila tera sua própria
        #Thread executando essa função.
        print()


    def write(self,reason,value):
        #Write Permission
        if reason == 'T1':
            self.setParam('T1',value)
        #Write Prohibition
        elif reason == 'T2' or reason == 'STATUS':
            return False

'''
#Clear session data - Logout request
service = 'login-sessions'
r = req.request('delete',service)
'''
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
