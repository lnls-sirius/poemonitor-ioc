#!/usr/bin/python3
import os
import platform

IS_LINUX = (os.name == 'posix' or platform.system() == 'Linux')

def get_abs_path(relative):
    """
    relative = relative path with base at python/
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative)

#=============================================#
#                 Display + UI                #
#=============================================#

MAIN_MENU_UI = "../../ui/mainMenu.ui"

STATUS_MONITOR_PY = "statusMonitorDisplay.py"
STATUS_MONITOR_UI = "../../ui/statusMonitor.ui"
