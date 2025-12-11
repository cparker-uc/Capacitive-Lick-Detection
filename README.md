# Capacitive Lickometry System
### Created for the Timme Lab at University of Cincinnati
### Author: Christopher Parker

This repository contains the Python code for running our capacitive lickometry system.

## Installation

I haven't spent as much time making this easily installable as I'd like to yet, sorry! I manage my Python
environments with pyenv-virtualenv on the command line: https://github.com/pyenv/pyenv-virtualenv

To install the environment, I run:
pyenv virtualenv 3.13 lickometry # creates a new environment called lickometry on Python 3.13
pyenv activate lickometry
pip install -r requirements.txt

Then to run the system, just use the command jupyter-lab and navigate to the DataRecording.ipynb notebook.
