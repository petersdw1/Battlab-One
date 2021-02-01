# BattLab-One
A New Tool for Estimating and Optimizing Battery Life for Your Next Internet of Things Project

  - Battlab-One Quick Start Guide

  - BattLab_One_Production_Rev_A.py - Python Application Code for Production version 1.01

  - Production_Rev_A.sch - Schematic in Eagle

  - Production_Rev_A..brd - PCB Layout in Eagle

  - MSP430Firmware.c - Firmware code for the MSP430 for Production Version 1.01

  - BOM_Production_Rev_A - Bill of Materials for Battlab-One Production Rev A

  - 98-bluebird-labs.rules - Linux udev rules for Battlab-One

  See more at www.bluebird-labs.com
  
  ![image](https://user-images.githubusercontent.com/4383161/106499339-170c2800-6486-11eb-8046-a9a886a15f75.png)

# Development

This project uses pipenv to take care of setting up a virtual environment as well as managing the dependencies needed.

1. Install pipenv as describe here https://pypi.org/project/pipenv/
2. Start a terminal and change to the root folder of this project.
3. Run pipenv to setup the environment: `pipenv install --dev`
4. Start the pipenv shell: `pipenv shell`
5. Start the application: `python BattLab_One_V1.0.6.py`



