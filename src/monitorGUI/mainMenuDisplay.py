#!/usr/bin/python3

#import os
#print(os.getcwd())
#import sys

#Changing working directory
#print(os.getcwd())
#os.chdir('../..')
#print(os.getcwd())

#Configure python project directory structure
#sys.path.append(path.join(
#path.dirname(path.abspath(__name__)),"../../"))

import json
from qtpy import QtCore
from pydm import Display
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget)
from pydm.widgets import PyDMEmbeddedDisplay
from pydm.utilities import connection
from paths import get_abs_path,MAIN_MENU_UI,STATUS_MONITOR_PY
#import withApiLogin

class MainMenuDisplay(Display):
    def __init__(self, parent=None, args=[], macros=None):
        super(MainMenuDisplay, self).__init__(parent=parent, args=args, macros=None)

        self.rdb_SalaConectividade.filenames.append(get_abs_path(STATUS_MONITOR_PY))
        self.rdb_SalaConectividade.openInNewWindow = True

    def ui_filename(self):
        return MAIN_MENU_UI

    def ui_filepath(self):
        return get_abs_path(MAIN_MENU_UI)
