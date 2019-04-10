#!/usr/bin/python3

from os import sys,path
#Insert new path on enviroment variable for being able to import packages from upper folders
#Inserting .../src
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import poemonitorConfigfileReader

import json
from qtpy import QtCore,QtGui
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication)
from pydm.widgets import PyDMLabel,PyDMByteIndicator,PyDMPushButton
from pydm.utilities import connection
from paths import get_abs_path,STATUS_MONITOR_UI,SWITCHES_CONFIG,ROOMS_CONFIG

class MonitorDisplay(Display):
    def __init__(self, parent=None, args=[], macros=None):
        super(MonitorDisplay, self).__init__(parent=parent, args=args, macros=None)

        #Read data from configuration files
        switchesConfigReader = poemonitorConfigfileReader.PoemonitorSwitchesConfigReader()
        roomsConfigReader = poemonitorConfigfileReader.PoemonitorRoomsConfigReader()

        switchesFileData = switchesConfigReader.readFile(SWITCHES_CONFIG)
        roomsFileData = roomsConfigReader.readFile(ROOMS_CONFIG)
        print(roomsFileData)
        #Create dinamic monitoring screen based on number of devices on chosen room
        for switch in roomsConfigReader.getSwitchesByRoomIdFrom(1,roomsFileData):
            print(switch)
            for device in switchesConfigReader.getDevicesByIpFrom(switch["ip"],switchesFileData):
                if device != None:
                    print(device["name"])
                    print("\n")
                    self.table.insertRow(self.table.rowCount())
                    self.insertDeviceMonitorLine(device["name"])


        '''
        #DEBUG
        for device in switchesConfigReader.getAllDeviceNamesFrom(switchesFileData):
            self.table.insertRow(self.table.rowCount())
            self.insertDeviceMonitorLine(device)
        '''

    def ui_filename(self):
        return STATUS_MONITOR_UI

    def ui_filepath(self):
        return get_abs_path(STATUS_MONITOR_UI)

    #Insert PV monitor widgets on table row
    def insertDeviceMonitorLine(self,pvName):

        row = self.table.rowCount() - 1

        #Set each widget properties and insert on respective table row

        #Device name label creation
        self.table.setColumnWidth(0,150)
        w = QLabel()
        w.setText(pvName)
        w.setAlignment(QtCore.Qt.AlignCenter)

        self.table.setCellWidget(row,0,w)


        #Status byte indicator creation
        w = PyDMByteIndicator(init_channel='ca://'+pvName+'-Sts')
        w.circles = True
        w.showLabels = False
        w.onColor = QtGui.QColor(0,255,0)
        w.offColor = QtGui.QColor(255,0,0)
        w.alarmSensitiveBorder = True

        self.table.setCellWidget(row,1,w)

        #Raw status label creation
        self.table.setColumnWidth(2,150)
        w = PyDMLabel(init_channel='ca://'+pvName+'-Raw')
        w.setAlignment(QtCore.Qt.AlignCenter)

        self.table.setCellWidget(row,2,w)

        #Turn On push button creation
        w = PyDMPushButton(label='Turn On',init_channel='ca://'+pvName+'-Sel',pressValue=1)
        w.alarmSensitiveContent = True
        self.table.setCellWidget(row,3,w)

        #Turn Off push button creation
        w = PyDMPushButton(label='Turn Off',init_channel='ca://'+pvName+'-Sel',pressValue=0)
        w.alarmSensitiveContent = True
        self.table.setCellWidget(row,4,w)
