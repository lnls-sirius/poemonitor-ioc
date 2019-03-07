#!/usr/bin/python
# -*- coding: utf-8 -*-

#source_1 = http://docs.python-requests.org/en/master/api/#requests.Response
#source_2 = https://support.hpe.com/hpsc/doc/public/display?sp4ts.oid=7074783&docLocale=en_US&docId=emr_na-c05373669
#source_3 = https://www.w3schools.com/python/python_json.asp

import json             #Library for JSON manipulation
import requests         #Library for making HTTP requests
from time import sleep

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
#Request poe port status from all switch ports
service = 'poe/ports/stats'

r = req.request('get',service,cookie)
#Print data
r = dict(r.json())
for v in r['port_poe_stats']:
    print('Port: ' + v['port_id'] + '   status: ' + v['poe_detection_status'])

'''
