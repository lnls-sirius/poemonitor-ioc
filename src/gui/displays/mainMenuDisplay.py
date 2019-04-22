#!/usr/bin/python
# -*- coding: utf-8 -*-

#Developer: Paulo Baraldi Mausbach
#LNLS - Brazilian Synchrotron Light Source Laboratory

import json
from qtpy import QtCore
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget)
from pydm.widgets import PyDMEmbeddedDisplay
from pydm.utilities import connection
from paths import get_abs_path,MAIN_MENU_UI,STATUS_MONITOR_DISPLAY
from statusMonitorDisplay import MonitorDisplay

class MainMenuDisplay(Display):

    def __init__(self, parent=None, args=[], macros=None):
        super(MainMenuDisplay, self).__init__(parent=parent, args=args, macros=None)

    def ui_filename(self):
        return MAIN_MENU_UI

    def ui_filepath(self):
        return get_abs_path(MAIN_MENU_UI)
