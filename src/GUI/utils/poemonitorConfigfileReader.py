#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
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
    def getDevicesFrom(self,queueId,filData):
        return fileData['switches'][queueId]['devices']
    def getQueueIdByDeviceName(self,deviceName,fileData):
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
