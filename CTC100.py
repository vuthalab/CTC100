import re
import serial
import time

class CTC100:
    """
    An extremely simple class to read values from the CTC100
    Prorammable Temperature Controller.

    How to use::

        >>> import CTC100
        >>> c = CTC100.CTC100("/dev/ttyACM0")
        >>> c.read(1)
        300.841

    Author: Wesley Cassidy
    Date: 26 April 2018
    """

    def __init__(self, address):
        """
        Pass the USB Serial port the CTC100 is attached to (usually of
        the form /dev/ttyACM*).
        """

        self.device = serial.Serial(address, timeout=0)

    def write(self, command):
        """
        Write a command to the CTC100 over serial, then wait for the
        response.
        """

        self.device.write((command+"\n").encode()) # \n terminates commands

        # The response to a command is always terminated by a
        # \r\n, so keep polling the input buffer until we read
        # one.
        t1 = time.time()
        response = self.device.read()
        while len(response) == 1 or response[-2:] != "\r\n":
            response += self.device.read()
            t2 = time.time()
            if (t2 - t1) > 0.1:
                break
        return response
        
    def get_variable(self, var):
        """
        Read a parameter of the CTC100. This function is mostly for
        convenience, but does include some input formatting to prevent
        simple bugs.
        """
        
        var = var.replace(" ", "") # Remove spaces from the variable name. They're optional and can potentially cause problems
        return self.write("{}?".format(var))
        
    def set_variable(self, var, val):
        """
        Set a parameter of the CTC100. This function is mostly for
        convenience, but does include some input formatting to prevent
        simple bugs.
        """
        
        var = var.replace(" ", "") # Remove spaces from the variable name. They're optional and can potentially cause problems
        val = "({})".format(val) # Wrap argument in parentheses, just in case. This prevents an argument containing a space from causing unexpected issues
        return self.write("{} = {}".format(var, val))
        
    def increment_variable(self, var, val):
        """
        Add an amount to a parameter of the CTC100. This function is
        mostly for convenience, but does include some input formatting
        to prevent simple bugs.
        """
        
        var = var.replace(" ", "") # Remove spaces from the variable name. They're optional and can potentially cause problems
        val = "({})".format(val) # Wrap argument in parentheses, just in case. This prevents an argument containing a space from causing unexpected issues
        return self.write("{} += {}".format(var, val))

    def setAlarm(self, channel, Tmin, Tmax):
        
        #Enables alarm with 4 beeps on a channel for a given range
        
        if not isinstance(channel, str): #Sets string for channel
            channel = "In{}".format(channel)
            
        self.set_variable("{}.alarm.sound".format(channel),  "4 beeps") #Sets alarm to 4 beeps
        
        self.set_variable("{}.alarm.min".format(channel), str(Tmin)) #Sets minimum Temperature
        self.set_variable("{}.alarm.max".format(channel), str(Tmax)) #Set maximum Temperature
        
        response = self.set_variable("{}.alarm.mode".format(channel), "Level") # Turns alarm on
        
        return response
        
    def disableAlarm(self, channel):
        
        if not isinstance(channel, str): #Sets string for channel
            channel = "In{}".format(channel)
        
        repsonse = response = self.set_variable("{}.alarm.mode".format(channel), "Off") # Turns alarm off
    
    def read(self, channel):
        """
        Read the value of one of the input channels. If the channel's
        name has been changed from the default or you wish to read the
        value of an output channel, the full name must be passed as a
        string. Otherwise, an integer will work.
        """

        if not isinstance(channel, str): #Sets string for channel
            channel = "In{}".format(channel)
            
        response = self.get_variable("{}.value".format(channel))
        
        # Extract the response using a regex in case verbose mode is on
        match = re.search(r"[-+]?\d*\.\d+", response.decode("utf-8"))
        
        if match is not None:
            return float(match.group())
        else:
            raise RuntimeError("Unable to read from channel {}".format(channel))
    
    def enableHeater(self):
        self.write("outputEnable on")
        
    def disableHeater(self):
        self.write("outputEnable off")
    
    def enablePID(self, channel):
        #PID parameters should be set correctly using the autotuning step first
        self.enableHeater()
        self.set_variable("Out{}.PID.Mode".format(channel), "On") 

    def disablePID(self,channel):
        self.disableHeater()
        self.set_variable("Out{}.PID.Mode".format(channel), "Off") 
    
    def read_setpoint(self, channel):
        return self.read("Out{}.PID.setpoint".format(channel))
    
    def write_setpoint(self, channel, setpoint):
        # setpoint is in units of Kelvin
        return self.set_variable("Out{}.PID.setpoint".format(channel), setpoint)
        
    def tunePID(self, channel, StepY, Lag):
        '''
        Enables the PID loop tuning procedure on the CTC100. Lag is the time (in seconds)
        the heater will be turned on for the tuning procedure. StepY is the power the
        heater will apply (in Watts) over the duration of Lag. StepY and Lag should be chosen 
        such that the sample's temperature will increase by at least a factor of 10 over this time.
        NOTE: The temperature of the object should be stable before tuning.
        '''
        self.set_variable("Out{}.Tune.StepY".format(channel), StepY)
        self.set_variable("Out{}.Tune.Lag".format(channel), Lag)
        
        
        self.enableHeater() #enable heater so tuning can occur
        self.set_variable("Out{}.Tune.Type".format(channel), "Auto") #Most logical tuning mode
        self.set_variable("Out{}.Tune.Mode".format(channel), "Auto") #Begins tuning procedure
        
        time.sleep(Lag)
        if self.get_variable("Out{}.PID.Mode".format(channel)).decode('utf-8') == "On\r\n":
            print("The PID tuning was successful! The parameters have been updated")
            self.disablePID(channel) #Turn off PID since it automatically turns on
            self.write('menu 4') #Effectively presses okay on the screen
        else:
            print("The PID tuning failed! Try a higher value for StepY, Lag, or both.")
        
        