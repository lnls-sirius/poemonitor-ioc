#!/usr/bin/python
# -*- coding: utf-8 -*-

#source_1 = http://docs.python-requests.org/en/master/api/#requests.Response
#source_2 = https://support.hpe.com/hpsc/doc/public/display?sp4ts.oid=7074783&docLocale=en_US&docId=emr_na-c05373669
#source_3 = https://www.w3schools.com/python/python_json.asp
#source_4 = https://docs.python.org/3/library/json.html#module-json
#source_5 = https://docs.python.org/3/library/queue.html
#source_6 = https://docs.python.org/3.4/library/threading.html
#source_7 = https://www.tutorialspoint.com/python/python_files_io.htm

import json             #Library for JSON manipulation+
import requests         #Library for making HTTP requests
import threading
from time import sleep
from pcaspy import Driver, SimpleServer #Library for PV creation and manipulation
from ast import literal_eval #Command for transforming string into dictionary

#Login Data
USERNAME = 'controle'
PASSWORD = 'teste'

#Switch Address Data
IP = '10.129.0.100'
PORT = '80'

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

#Class responsible for reacting to PV read/write requests
class PoemonitorDriver(Driver):

    def  __init__(self):
        super(PoemonitorDriver, self).__init__()

        #====== REST API Connection Initialization =========

        req = ArubaApiRequester(IP,PORT)

        r = req.login(USERNAME,PASSWORD)
        cookie = dict(r.json())

        ###############################CRIAR AS THREADS DE CONTROLE###########################################

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

        def write(self,reason,value):
            #Write Permission
            if reason == 'T1':
                self.setParam('T1',value)
            #Write Prohibition
            elif reason == 'T2' or reason == 'STATUS':
                return False

        def scanSwitchesThread():
            print()
            #Para cada switch existente dentre os devices do arquivos de configuração
            #criar uma fila(Queue) de comandos e uma thread para tratar o consumo desses recursos
            #Essas threads são responsaveis por inserir em suas respectivas filas todas as requisições
            #de escrita(PUT) enviadas pelos clientes e inserir periodicamente requisições de leitura(GET)
            #dos dados para manter o dado sempre atualizado

        def processThread():
            print()

            #Responsável por tratar('consumir') cada requisição dentro da fila. Cada fila tera sua própria
            #Thread executando essa função.

        #################################################################

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
