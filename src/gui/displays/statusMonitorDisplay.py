#!/usr/bin/python
# -*- coding: utf-8 -*-

#Developer: Paulo Baraldi Mausbach
#LNLS - Brazilian Synchrotron Light Source Laboratory

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

        #Define roomId to be monitored based on display instantiation passed value
        self.roomId = int(sys.argv[2])
        #Read data from configuration files
        self.switchesConfigReader = poemonitorConfigfileReader.PoemonitorSwitchesConfigReader()
        self.roomsConfigReader = poemonitorConfigfileReader.PoemonitorRoomsConfigReader()

        self.switchesFileData = self.switchesConfigReader.readFile(SWITCHES_CONFIG)
        self.roomsFileData = self.roomsConfigReader.readFile(ROOMS_CONFIG)

        #Dinamically set window title
        self.roomName = self.roomsConfigReader.getRoomNameByIdFrom(self.roomId,self.roomsFileData)
        self.setWindowTitle(self.roomName + ' - Power-Over-Ethernet Monitor ')

        #Create dinamic monitoring screen based on number of devices on chosen room
        for switch in self.roomsConfigReader.getSwitchesByRoomIdFrom(self.roomId,self.roomsFileData):
            for device in self.switchesConfigReader.getDevicesByIpFrom(switch["ip"],self.switchesFileData):

                if device != None:
                    self.insertDeviceMonitorRow(switch["ip"],device["name"])

            #Insert blank row for differ switches informations
            self.insertNewRow()

        #Remove last inserted row
        self.table.removeRow(self.table.rowCount()-1)

    def ui_filename(self):
        return STATUS_MONITOR_UI

    def ui_filepath(self):
        return get_abs_path(STATUS_MONITOR_UI)

    def insertNewRow(self):
        #Insert new row
        self.table.insertRow(self.table.rowCount())
        #Select last inserted row
        return self.table.rowCount() - 1

    #Insert PV monitor widgets on table row
    def insertDeviceMonitorRow(self,switchIp,pvName):

        row = self.insertNewRow()

        #Set each widget properties and insert on respective table row

        #Swich Ip Label
        w = QLabel()
        w.setText(switchIp)
        w.setAlignment(QtCore.Qt.AlignCenter)
        self.table.setCellWidget(row,0,w)

        #Device name label creation
        self.table.setColumnWidth(1,150)
        w = QLabel()
        w.setText(pvName)
        w.setAlignment(QtCore.Qt.AlignCenter)

        self.table.setCellWidget(row,1,w)

        #Status byte indicator creation
        w = PyDMByteIndicator(init_channel='ca://'+pvName+':PwrState-Sts')
        w.circles = True
        w.showLabels = False
        w.onColor = QtGui.QColor(0,255,0)
        w.offColor = QtGui.QColor(255,0,0)
        w.alarmSensitiveBorder = True
        w.alarmSensitiveContent = True
        self.table.setCellWidget(row,2,w)

        #Raw status label creation
        self.table.setColumnWidth(3,150)
        w = PyDMLabel(init_channel='ca://'+pvName+':PwrState-Raw')
        w.alarmSensitiveBorder = True
        w.setAlignment(QtCore.Qt.AlignCenter)

        self.table.setCellWidget(row,3,w)

        #Turn On push button creation
        w = PyDMPushButton(label='Turn On',init_channel='ca://'+pvName+':PwrState-Sel',pressValue=1)
        w.alarmSensitiveContent = True
        self.table.setCellWidget(row,4,w)

        #Turn Off push button creation
        w = PyDMPushButton(label='Turn Off',init_channel='ca://'+pvName+':PwrState-Sel',pressValue=0)
        w.alarmSensitiveContent = True
        self.table.setCellWidget(row,5,w)
