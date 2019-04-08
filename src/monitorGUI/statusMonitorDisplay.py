#!/usr/bin/python3

import os
print(os.getcwd())
#from os import path
#import sys
#Configure python project directory structure
#sys.path.append(path.join(
#    path.dirname(path.abspath(__name__)),"../../"))
#print(sys.path)

import json
from qtpy import QtCore
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget)
from pydm.widgets import PyDMEmbeddedDisplay
from pydm.utilities import connection
from paths import get_abs_path,MAIN_MENU_UI,STATUS_MONITOR_UI

class MonitorDisplay(Display):
    def __init__(self, parent=None, args=[], macros=None):
        super(MonitorDisplay, self).__init__(parent=parent, args=args, macros=None)

    def ui_filename(self):
        return STATUS_MONITOR_UI

    def ui_filepath(self):
        return get_abs_path(STATUS_MONITOR_UI)
