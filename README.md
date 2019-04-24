# poemonitor-ioc

IOC for monitoring power-over-ethernet(PoE) ports status from Aruba switches used on Sirius network infrastructure

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

Currently there are two version of this IOC. One version created for being used on network infrastructures where it's switches are without any kind of login authentication and the other exactly for the opposite, where there are login authentication configured on the switches. In this repository you can find either the graphical user interface (GUI) created for being used by Sirius operation room.

All files needed to make any of the applications run properly are on each project directory inside this repository, so for running any of the applications it's possible to clone this repository and execute the IOC scripts using python 3 or the GUI using PyDM or download only the files inside each application respective directory and run it.

### Prerequisites

#### IOC

For running the IOC application it's needed to have installed before the following python modules:

* python3 - The IOC was tested using python 3.6.5
* [requests](https://2.python-requests.org//en/master/) - Version 2.18.4 -> Used for making HTTP requests to the REST API from [Aruba switches](https://www.arubanetworks.com/products/networking/switches/) used on Sirius network infrastructure
* [EPICS base](https://epics.anl.gov/)
* [pcaspy](https://pcaspy.readthedocs.io/en/latest/) - Version 0.7.2 -> Used for creating EPICS PVs, scanning it's values and alarming functioning problems

#### GUI

For running the GUI application it's needed to have installed before the following python modules:

* [PyQt](https://www.qt.io/qt-for-python) - Used for creating application screens with python (Qt Designer is really helpful for accelerating screen development, so it's really encoraged to install it and use it)
* [PyDM](https://slaclab.github.io/pydm/) - Version 1.6.5 -> Used on the integration of EPICS to screens created using Qt(It's also possible to use PyDM widgets on Qt Designer)

## Deployment on Sirius

This application was deployed on Sirius infrastructure using [Docker](https://www.docker.com/). All docker files used on this project and it's respective documentation  are stored at https://github.com/lnls-sirius/docker-poemonitor.
