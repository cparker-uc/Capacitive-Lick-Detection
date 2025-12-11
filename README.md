# Capacitive Lickometry System
### Created for the Timme Lab at University of Cincinnati
### Author: Christopher Parker

This repository contains the Python code for running our capacitive lickometry system.

## Installation

I haven't spent as much time making this easily installable as I'd like to yet, sorry! 

First, if you're on Windows (which is what we are using to make things easy on undergrads/grad students
who need to run the system), you'll have to install drivers for the FT232H boards. The recommended 
method is Zadig, and we roughly followed the steps outlined here: https://learn.adafruit.com/circuitpython-on-any-computer-with-ft232h/windows

Next, I manage my Python environments with pyenv-virtualenv on the command line: https://github.com/pyenv/pyenv-virtualenv

To install the environment, I run:
```
pyenv virtualenv 3.13 lickometry # creates a new environment called lickometry on Python 3.13
pyenv activate lickometry
pip install -r requirements.txt
```
Once the environment is configured and active, you'll need to set serial numbers for the FT232H boards
so we can tell which is which even if the USB plugs get shuffled (which would change the ftdi://... address,
and could cause confusion). I've included the script set_ft232h_serial.py for this purpose. The FT232H boards
should be plugged in ONE AT A TIME and the script can be run as follows:
```
python set_ft232h_serial.py FT232H0 # FT232H0 is the new serial number for the board
```
I have used the serial numbers FT232H0 through FT232H3 in our lab (and hence in the DataRecording.ipynb notebook),
so you can either use the same serials or modify the notebook. To change the serial numbers used, you'll need to
modify the serial_number_sensor_map dictionary to tell the system which cages go with which board.

Then to run the system, just use the command jupyter-lab and navigate to the DataRecording.ipynb notebook.
