#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
#Class to read poemonitor-ioc switches configure file
class PoemonitorSwitchesConfigReader():
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
    def getDevicesByIpFrom(self,ip,fileData):
        for switch in fileData["switches"]:
            if(ip == switch["login_data"]["ip"]):
                return switch["devices"]
            return None

#Class to read poemonitor-ioc rooms configure file
class PoemonitorRoomsConfigReader():
    def readFile(self,fileName):
        with open(fileName,'r') as f:
            fileData = json.loads(f.read())
        return fileData
    def getSwitchesByRoomIdFrom(self,roomId,fileData):
        for room in fileData["rooms"]:
            if room["id"] == roomId:
                return room["switches"]
        return None
