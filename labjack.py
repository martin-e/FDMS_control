import LabJackPython, u3, struct

class LabJackError(Exception):
    pass

def toDouble(buffer):
    """
    Name: toDouble(buffer)
    Args: buffer, an array with 8 bytes
    Desc: Converts the 8 byte array into a floating point number.
    """
    bufferBytes = bytes(buffer[:8])
    dec, wh = struct.unpack('<Ii', bufferBytes)
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
        self.connectToFirstDevice()
        self.device.setDOState(self.U3_DIO_PIN)    # configure 
        #self.device.configIO(FIOAnalog=(self.U3_ADC_PIN + 1))  #configure ADCPin as analog in
        self.device.configAnalog(self.U3_ADC_PIN)  #configure ADCPin as analog in

    def __del__(self):
        if self.isConnected:
            try:
                self.disconnect()
            except:
                pass

    def connectToFirstDevice(self):
        if len(LabJackPython.listAll(self.deviceType)) > 0:
            self.device = u3.U3()
            self.calibrationData = self.device.getCalibrationData()
            self.isConnected = True
        else:
            raise LabJackError("no labjack U3 found")
            
    def disconnect(self):
        self.device.close()
        self.isConnected = True
    
class Piezo():
    def __init__(self, u3device, voltage = 0.0):
        self.u3device = u3device
        self.voltage = voltage
        if not self.u3device.isConnected:
            raise LabJackError("no device connected")
        self.getCalConstants()
        self.setVoltage(voltage)

    def getCalConstants(self):
        # request LJTick DAC calibration constants
        data = self.u3device.device.i2c(self.u3device.EEPROM_ADDRESS, [64], NumI2CBytesToReceive=36, SDAPinNum = self.u3device.sdaPin, SCLPinNum = self.u3device.sclPin)
        response = data['I2CBytes']
        self.u3device.aOffset = toDouble(response[8:16])
        self.u3device.aSlope = toDouble(response[0:8])

    def getVoltage(self):
        return self.voltage

    def setVoltage(self, voltage):
        self.voltage = voltage
        if not self.u3device.isConnected:
            raise LabJackError("no device connected")
        (hiBit, loBit) = self.voltageToBits(voltage)
        self.u3device.device.i2c(self.u3device.DAC_ADDRESS, [48, hiBit, loBit], SDAPinNum = self.u3device.sdaPin, SCLPinNum = self.u3device.sclPin)
        self.voltage = voltage

    def setPiezoBitval(self, bitval):
        if not self.u3device.isConnected:
            raise LabJackError("no device connected")
        loBit = int(bitval%256)
        hiBit = int(bitval/256)
        self.u3device.device.i2c(self.DAC_ADDRESS, [48, hiBit, loBit], SDAPinNum = self.u3device.sdaPin, SCLPinNum = self.u3device.sclPin)
        self.voltage = self.bitvalToVoltage(hiBit, loBit)

    def voltageToBitval(self, voltage):
        return int(voltage*self.u3device.aSlope)+self.u3device.aOffset

    def voltageToBits(self, voltage):
        bitval = self.voltageToBitval(voltage)
        loBit = int(bitval%256)
        hiBit = int(bitval/256)
        return (hiBit, loBit)

    def bitvalToVoltage(self, hiBit, loBit):
        bitval = hiBit*256 + loBit
        voltage = (bitval - self.u3device.aSlope) / self.u3device.aOffset
        return voltage

class Adc():
    def __init__(self, u3device):
        self.u3device = u3device
        if not self.u3device.isConnected:
            raise LabJackError("no device connected")
    
    def readValue(self):
        voltage = self.u3device.device.getAIN(self.u3device.U3_ADC_PIN)
        # voltage = self.u3device.device.binaryToCalibratedAnalogVoltage(bitval[0])
        return voltage
        
class Pulser():
    def __init__(self, u3device, dio_val = 0):
        self.dio_val = dio_val
        self.u3device = u3device
        if not self.u3device.isConnected:
            raise LabJackError("no device connected")
        self.setOutput(dio_val)
    
    def setOutput(self, dio_val):
        self.u3device.device.setDIOState(self.u3device.U3_DIO_PIN, bool(dio_val))

    def getOutput(self):
        return self.u3device.device.getDIOState(self.u3device.U3_DIO_PIN)
        
    def pulse(self, length):
        # creates pulse on DIO pin of specified length in ms
        # up to 32 ms it is in multiples of 128 us, from 32 
        # ms it is divided in a pause in multiples of 16 ms 
        # followed by the remaining pause in multiples of 
        # 128 us.
        # function returns the actual pulse length in ms

        pin = self.u3device.U3_DIO_PIN
        if length < 256*0.128:
            waitS = int(round(length/0.128))
            wait1 = u3.WaitShort(waitS)
            waittime = waitS*0.128
        else:
            waitL = int(length/16.384)
            wait2 = u3.WaitLong(waitL)
            waittime = waitL*16.384
            waitS = int(round((length - waittime)/0.128))
            wait1 = u3.WaitShort(waitS)
            waittime = waitL*16.384 + waitS*0.128

        sethigh = u3.BitStateWrite(pin, 1)
        setlow = u3.BitStateWrite(pin, 0)
        if length < 256*0.128:
            self.u3device.device.getFeedback(sethigh, wait1, setlow)
        else:
            self.u3device.device.getFeedback(sethigh, wait1, wait2, setlow)
        return waittime