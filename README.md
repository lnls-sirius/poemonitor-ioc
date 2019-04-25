# poemonitor-ioc

IOC for monitoring power-over-ethernet(PoE) ports status from Aruba switches used on Sirius network infrastructure.

## PVs generated by this IOC

    **_<prefix>:PwrState-Raw_** -> This PV stores the raw status value received from the request made to the switch REST API and it's a read-only PV. The following are the possible values for this PV:

    * **Searching**: The port is trying to detect a PD connection.
    * **Delivering**: The port is delivering power to a PD.
    * **Disabled**: On the indicated port, either PoE support is disabled or PoE power is enabled but the PoE module does not have enough power available to supply the port's power needs.
    * **Fault**: The switch detects a problem with the connected PD.
    * **Other Fault**: The switch has detected an internal fault that prevents it from supplying power on that port.

    **_<prefix>:PwrState-Sts_** -> This PV is a translation of the 5 possible states of _PwrState-Raw_ PV to a binary state On (1) or Off (0) and it's a read-only PV.

    **_<prefix>:PwrState-Sel_** -> This is the only writable PV and it's used for turning on (1) or off (0) it's respective port.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

Currently there are two version of this IOC. One version created for being used on network infrastructures where it's switches are without any kind of login authentication and the other exactly for the opposite, where there are login authentication configured on the switches. In this repository you can find either the graphical user interface (GUI) created for being used by Sirius operation room.

All files needed to make any of the applications run properly are on each project directory inside this repository, so for running any of the applications it's possible to clone this repository and execute the IOC scripts using python 3 or the GUI using PyDM or download only the files inside each application respective directory and run it.

## Prerequisites

### IOC

For running the IOC application it's needed to have installed before the following python modules:

* python3 - The IOC was tested using python 3.6.5
* [requests](https://2.python-requests.org//en/master/) - Version 2.18.4 -> Used for making HTTP requests to the REST API from [Aruba switches](https://www.arubanetworks.com/products/networking/switches/) used on Sirius network infrastructure
* [EPICS base](https://epics.anl.gov/)
* [pcaspy](https://pcaspy.readthedocs.io/en/latest/) - Version 0.7.2 -> Used for creating EPICS PVs, scanning it's values and alarming functioning problems

### GUI

For running the GUI application it's needed to have installed before the following python modules:

* [PyQt](https://www.qt.io/qt-for-python) - Used for creating application screens with python (Qt Designer is really helpful for accelerating screen development, so it's really encoraged to install it and use it)
* [PyDM](https://slaclab.github.io/pydm/) - Version 1.6.5 -> Used on the integration of EPICS to screens created using Qt(It's also possible to use PyDM widgets on Qt Designer)

## Deployment on Sirius

This application was deployed on Sirius infrastructure using [Docker](https://www.docker.com/). All docker files used on this project and it's respective documentation  are stored at https://github.com/lnls-sirius/docker-poemonitor.

## Deploying an updated IOC version IOC

Deploy a IOC version update is pretty easy due to the way the Docker image for running this IOC on Sirius has been built. During the Docker image build a volume is created at the directory where the IOC file is, this makes possible for the image to access files from the host machine, that is, access the IOC script and run it. Considering that, the only change that is needed to update the IOC version, is stop the actual image from running, exchange the IOC script files into the directory where the image volume has been created and restart the image, this way the image will start to run the new IOC version.

It's important to notice that any change on the localization of the IOC makes necessary to update the place where the docker volume is created, that is, change the Docker configuration file used for creating the image, rebuild the image for it to start considering the new path to the IOC file when mounting it's volume, otherwise a "file not found" error might happen.

## Project documentation

All Documentation related to the infrastructure in which the project was applied, how does the IOC works, configuration file(patterns and adding/excluding registers) and other information can be found at the directory _IOC Diagrams_.
