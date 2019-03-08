#!/usr/bin/python
# -*- coding: utf-8 -*-

#source_1 = http://docs.python-requests.org/en/master/api/#requests.Response
#source_2 = https://support.hpe.com/hpsc/doc/public/display?sp4ts.oid=7074783&docLocale=en_US&docId=emr_na-c05373669
#source_3 = https://www.w3schools.com/python/python_json.asp

import json             #Library for JSON manipulation
import requests         #Library for making HTTP requests
from time import sleep
from pcaspy import Driver, SimpleServer #Library for PV creation and manipulation

#Login Data
userName = 'controle'
password = 'teste'

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

#PVs defenitions
prefix = 'TESTE:'
pvdb = {
    #PV base name
    'T1' : {
    #PV atributes
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    },
    #PV base name
    'T2' : {
        #PV atributes
        'type'  :   'enum',
        'enums' :   ['Off','On'],
    }
}

#Class responsible for reacting to PV read/write requests
class poeMonitorDriver(Driver):

    def  __init__(self):
        super(poeMonitorDriver, self).__init__()

        #====== REST API Connection Initialization =========

        req = ArubaApiRequester('10.129.0.100','80')

        r = req.login(userName,password)
        cookie = dict(r.json())

        ###############################DEVE INSERIR ISSO EM UMA THREAD###########################################

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

        def write(self,reason,value):
            #Write Permission
            if(reason == 'T1'):
                self.setParam('T1',value)
            #Write Prohibition
            elif(reason == 'T2'):
                return False

        #################################################################3
'''
#Creating a ArubaApiRequester object
req = ArubaApiRequester('10.129.0.100','80')

r = req.login(userName,password)
cookie = dict(r.json())

#Request poe port status from one 1 port
service = 'ports/1/poe/stats'
r = req.request('get',service)
r = dict(r.json())
print('Port: ' + r['port_id'] + '   status: ' + r['poe_detection_status'])

service = 'ports/2/poe/stats'
r = req.request('get',service)
r = dict(r.json())
print('Port: ' + r['port_id'] + '   status: ' + r['poe_detection_status'])

service = 'ports/3/poe/stats'
r = req.request('get',service)
r = dict(r.json())
print('Port: ' + r['port_id'] + '   status: ' + r['poe_detection_status'])

#Clear session data - Logout request
service = 'login-sessions'
r = req.request('delete',service)
'''
#Main routine
if __name__ == '__main__':

    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = poeMonitorDriver()

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
