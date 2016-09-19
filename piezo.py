import LabJackPython, u3, struct


class LabJackError(StandardError):
    pass

def toDouble(buffer):
    """
    Name: toDouble(buffer)
    Args: buffer, an array with 8 bytes
    Desc: Converts the 8 byte array into a floating point number.
    """
    if type(buffer) == type(''):
        bufferStr = buffer[:8]
    else:
        bufferStr = ''.join(chr(x) for x in buffer[:8])
    dec, wh = struct.unpack('<Ii', bufferStr)
    return float(wh) + float(dec)/2**32

class LabJackU3():
    # define constants
    EEPROM_ADDRESS = 0x50
    DAC_ADDRESS = 0x12
    deviceType = 3         # LabJack U3
    def __init__(self, DACpin = 4, DIOpin = 6, ADCpin = 0):
        self.U3_DAC_PIN = DACpin  # FIO5 for piezo
        self.U3_DIO_PIN = DIOpin  # FIO6 for laser pulse
        self.U3_ADC_PIN = ADCpin  # FIO0 for piezo feedback signal
        self.sclPin = self.U3_DAC_PIN
        self.sdaPin = self.sclPin + 1
        self.isConnected = False
        # connect to Labjack U3 and get cal constants
        self.connectToFirstDevice()
        
    def __del__(self):
        if self.isConnected:
            try:
                self.disconnect()
            except:
                pass

    def connectToFirstDevice(self):
        if len(LabJackPython.listAll(self.deviceType)) > 0:
            self.device = u3.U3()
            self.isConnected = True
        else:
            raise LabJackError("no labjack U3 found")
            
    def disconnect(self):
        self.device.close()
        self.isConnected = True
    
class Piezo():
    def __init__(self, u3, voltage = 0.0):
        self.u3 = u3
        self.voltage = voltage
        if not self.u3.isConnected:
            raise LabJackError("no device connected")
        self.getCalConstants()
        self.setVoltage(voltage)
        
    def getVoltage(self):
        return self.voltage

    def getCalConstants(self):
        if not self.u3.isConnected:
            raise LabJackError("no device connected")
        # request calibration constants
        data = self.u3.device.i2c(self.u3.EEPROM_ADDRESS, [64], NumI2CBytesToReceive=36, SDAPinNum = self.u3.sdaPin, SCLPinNum = self.u3.sclPin)
        response = data['I2CBytes']
        self.aOffset = toDouble(response[8:16])
        self.aSlope = toDouble(response[0:8])
        
    def setVoltage(self, voltage):
        self.voltage = voltage
        if not self.u3.isConnected:
            raise LabJackError("no device connected")
        (hiBit, loBit) = self.voltageToBits(voltage)
        self.u3.device.i2c(self.u3.DAC_ADDRESS, [48, hiBit, loBit], SDAPinNum = self.u3.sdaPin, SCLPinNum = self.u3.sclPin)
        self.voltage = self.bitvalToVoltage(hiBit, loBit)

    def setPiezoBitval(self, bitval):
        if not self.u3.isConnected:
            raise LabJackError("no device connected")
        loBit = int(bitval%256)
        hiBit = int(bitval/256)
        self.u3.device.i2c(self.DAC_ADDRESS, [48, hiBit, loBit], SDAPinNum = self.u3.sdaPin, SCLPinNum = self.u3.sclPin)
        self.voltage = self.bitvalToVoltage(hiBit, loBit)

    def voltageToBitval(self, voltage):
        return int(voltage*self.aSlope)+self.aOffset

    def voltageToBits(self, voltage):
        bitval = self.voltageToBitval(voltage)
        loBit = int(bitval%256)
        hiBit = int(bitval/256)
        return (hiBit, loBit)

    def bitvalToVoltage(self, hiBit, loBit):
        bitval = hiBit*256 + loBit
        voltage = (bitval - self.aSlope) / self.aOffset
        return voltage

class Adc():
    #def __init__(self, u3):
    #if not self.u3.isConnected:
    #    raise LabJackError("no device connected")
    pass
    
class Pulse():
    #def __init__(self, u3, dio_val = 0):
    #self.dio = dio
    #if not self.u3.isConnected:
    #    raise LabJackError("no device connected")
    #self.setOutput(dio_val)
    pass