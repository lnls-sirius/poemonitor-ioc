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

#Configuration filename
CONFIG_FILE_NAME = 'poemonitor.config'

#Delay, in seconds, to insert a new read request into a queue
SCAN_DELAY = 1

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
                'userName':username,
                'password':password,
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

    def logout(self):
        try:
            service = 'login-sessions'
            r = request('delete',service)
        except:
            print('Logout attempt failed')
            return r

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

    def getQueueIdByDeviceName(self,deviceName,fileData):
        for i in range(0, len(r['switches'])):
            for j in r['switches'][i]['devices']:
                if j['name'] == 'T1':
                    return i
        return False

#Class responsible for reacting to PV read/write requests
class PoemonitorDriver(Driver):

    ListOfQueues = []

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

        #Periodically inserts read requests into each request queue
        while(True):
            for i in self.ListOfQueues:
                i.put(['READ_POE_PORT_STATUS'])
                #DEBUG
                print(i.qsize())
            self.event.wait(SCAN_DELAY)

    #Responsável por tratar('consumir') cada requisição dentro da fila. Cada fila tera sua própria
    #Thread executando essa função.
    def processThread(self,queueId):

        try:
            loginData = self.configReader.getLoginDataFrom(queueId,self.configData)
            #REST API connection initialization
            req = ArubaApiRequester(loginData['ip'],loginData['port'])
            r = req.login(loginData['username'],loginData['password'])

            while(True):
                 request = self.ListOfQueues[queueId].get(block=True)

                 #Execute requests
                 if(request[0] == 'READ_POE_PORT_STATUS'):

                     #For each device registered linked to switch on configuration file
                     for device in self.configReader.getDevicesFrom(queueId,self.configData):

                         #Request POE port status using switch's REST API
                         r = req.request('get','ports/'+device['port']+'/poe/stats')
                         r = dict(r.json())

                         #DEBUG
                         #print('updated PVs     queueID = ' + str(queueId))
                         print('Port: ' + r['port_id'] + '   status: ' + r['poe_detection_status'])

                         #Update PVs values
                         self.setParam(device['name']+':PwrState-Raw',r['poe_detection_status'])

                         if(r['poe_detection_status'] == 'PPDS_DELIVERING'):
                             self.setParam(device['name']+':PwrState-Sts',1)
                         else:
                             self.setParam(device['name']+':PwrState-Sts',0)
                         self.updatePVs()

        except Exception as e:
            print("Exception thrown by queue's "+queueId+"process thread\nException: "+e)
            req.logout()


    def write(self,reason,value):

        if reason == 'T1:PwrState-Sel':
            ############ISSO DEVE IR PARA O PROCESS THREAD
            self.setParam('T1:PwrState-Sel',value)#######
            self.updatePVs()#################
            ##################################
            #INSERIR NA QUEUE RESPECTIVA O VALOR a ser escrito,
            #e a porta a ser desativada
        elif reason == 'T2:PwrState-Sel':
            ############ISSO DEVE IR PARA O PROCESS THREAD
            self.setParam('T2:PwrState-Sel',value)########
            self.updatePVs()##########################
            ######################################
            #INSERIR NA QUEUE RESPECTIVA O VALOR a ser escrito,
            #e a porta a ser desativada
        else:
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
