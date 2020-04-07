# CTC100
Python Code for controlling the SRS Cryogenic Temperature Controller
## How to use
```python
>>> from CTC100 import CTC100
>>> temperature_controller = CTC100('/dev/ttyUSB0') #Older controller might use /ttyACM 

>>> temperature.read(1) #Read temperature on channel 1
301.221

>>> temperature_controller.read("Out1") #Read output power on channel 1
0.000

>>> temperature_controller.tunePID(1, 5, 60) #Tune PID for controlling temperature of aluminum at room temperature
"The PID tuning was successful! The parameters have been updated"

>>> temperature_controller.enableHeater()
>>> temperature_controller.write_setpoint(303) #Updates setpoint
```
