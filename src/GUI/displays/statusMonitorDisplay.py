#!/usr/bin/python3

from os import sys,path
#Insert new path on enviroment variable for being able to import packages from upper folders
#Inserting .../src
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import poemonitorConfigfileReader

import json
from qtpy import QtCore
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget)
from pydm.widgets import PyDMLabel,PyDMByteIndicator,PyDMPushButton
from pydm.utilities import connection
from paths import get_abs_path,MAIN_MENU_UI,STATUS_MONITOR_UI

class MonitorDisplay(Display):
    def __init__(self, parent=None, args=[], macros=None):
        super(MonitorDisplay, self).__init__(parent=parent, args=args, macros=None)

        configReader = poemonitorConfigfileReader

        self.table.insertRow(0)
        self.insertDeviceLine("teste")

    def ui_filename(self):
        return STATUS_MONITOR_UI

    def ui_filepath(self):
        return get_abs_path(STATUS_MONITOR_UI)

    #Insert PV monitor widgets on table row
    def insertDeviceLine(self,pvName):

        row = self.table.rowCount() - 1

        self.table.setCellWidget(row,0,PyDMLabel())

        self.table.setCellWidget(row,1,PyDMByteIndicator())

        self.table.setCellWidget(row,2,PyDMLabel())

        self.table.setCellWidget(row,3,PyDMPushButton())

        self.table.setCellWidget(row,4,PyDMPushButton())
