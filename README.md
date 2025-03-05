# TOBB ETÜ ELE495 - Capstone Project

# Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Acknowledgements](#acknowledgements)

## Introduction
This project aims to enable an autonomous vehicle to detect the location of an antenna broadcasting on the 433MHz band with the help of YTR (Yet Another Tracking Receiver) and navigate towards it.

## Features
- Autonomous Signal Tracking: The vehicle autonomously tracks the 433MHz signal using YTR and locates the antenna, stopping autonomously when it is within 70cm of the transmitter.
- Real-time User Interface: A user interface displays the vehicle’s real-time heading, position, and signal strength (dB).
- Time Efficiency: The vehicle reaches the transmitter's location within 2 minutes.
## Hardware
- Raspberry Pi 4 Model B, Arduino Nano, 433MHz Yagi-Uda Antenna, 433MHz Omnidirectional Antenna, RTL-SDR, SMA Connector, Coaxial Cable (50 Ohm), Li-ion Batteries (3 units), Power Bank (20W Output Power), Motor Driver (L298N), Car Kit, Accelerometer.
- Raspberry Os
## Applications:
  - Autonomous Navigation: Can be used in autonomous vehicles or robots for precise navigation based on signal detection and tracking.
  - Signal Detection and Localization: Ideal for applications in search and rescue, where finding a specific signal or transmitter is crucial.
  -Wireless Communication Testing: Useful for testing and measuring signal strength in different environments for wireless communication systems.
  -Antenna Positioning: Can be employed in antenna alignment and positioning applications to optimize signal reception or broadcasting.
## Services 
- Custom Signal Tracking Solutions: Provide tailored signal tracking systems for various industries, including telecommunications and security.
- Autonomous System Integration: Integrate autonomous vehicle control systems for navigation based on signal tracking for research or commercial applications.
- Signal Strength Monitoring: Offer real-time monitoring services for signal strength measurement across large areas or specific zones.
- Testing and Calibration: Provide services to test and calibrate wireless devices, antennas, and SDR systems to ensure optimal performance.

## Installation
- Install Raspberry Pi OS.
- Assign pins for the motor driver and accelerometer on the Raspberry Pi.
- Assemble the vehicle kit with Raspberry Pi, motor driver, accelerometer, and power bank.
- Build a Yagi-Uda antenna suitable for 433MHz.
- The dimensions of the Yagi-Uda antenna are provided in the image below.
- Mount the antenna on the car’s top parallel to the ground. Solder one half of the dipole to the positive side of the coaxial cable and the other half to the ground side.
- Install the Raspberry Pi RTL-SDR library and retrieve the algorithm from main.py.
- Perform tests by transmitting on 433MHz using the Arduino Nano and the omnidirectional antenna.
- Create the user interface.
```bash
# Example commands
git clone https://github.com/username/project-name.git
cd project-name
```

## Usage
Install Required Libraries before running the project, make sure all necessary dependencies are installed on your Raspberry Pi. pyrtlsdr, smbus2, Rpi.GPIO.
Connect the Raspberry Pi and motor driver to the vehicle kit.
Assemble the Yagi-Uda antenna as per the provided dimensions.
Ensure the 433MHz RTL-SDR is properly connected and configured.
To start the tracking process, execute the main Python file:

bash
python main.py
The vehicle will begin searching for the 433MHz signal. It will rotate 360 degrees, measuring signal strength and moving towards the direction of the highest signal.

The real-time user interface will display on your Raspberry Pi screen, showing:

Vehicle’s current position and heading.
Signal strength (in dB).
The vehicle will autonomously stop once it reaches within 70cm of the transmitter.

If you need to stop the vehicle manually at any point, press CTRL+C in the terminal.

If you wish to change the parameters (e.g., sample rate, gain, frequency), modify the config.py files in the respective directories (Navigator.py, Sdr_module.py).
## Screenshots
Include screenshots of the project in action to give a visual representation of its functionality. You can also add videos of running project to YouTube and give a reference to it here. 

## Acknowledgements
Raspberry Pi Foundation, RTL-SDR Project, Yagi-Uda Antenna Design Resources, Open-Source Community. 

[Resource]https://www.raspberrypi.org/  
[Resource]https://www.rtl-sdr.com/  
[Resource]https://www.arduino.cc/  
[Resource]https://en.wikipedia.org/wiki/Yagi-Uda_antenna  
[Contributor 1](https://github.com/(https://github.com/SirAlperen))
[Contributor 2](https://github.com/user1)
[Contributor 3](https://github.com/user1)
[Contributor 4](https://github.com/user1)
[Contributor 5](https://github.com/user1)

