'''M. Eschen, 2017

class to control a Thorlabs PM100USB power meter via the 
NI VISA library. By default, a single device 
connected will be interfaced.'''

import pyvisa, sys, struct, logging

if sys.version_info > (3,):
    class PowermeterError(Exception):
        pass
else:
    class PowermeterError(StandardError):
        pass

class Pm100usb():
    def __init__(self, pm100usb_ini, resourceName=''):
        # define constants
        self.resourceString = 'USB?*::0x1313::0x8072::?*::INSTR'
        self.pm100usb_ini = pm100usb_ini
        self.isConnected = False
        self.isConfigured = False
        if resourceName:
            self.resourceString = resourceName
        self.rm = pyvisa.ResourceManager()
        self.connectToDevice()
        self.getPmInfo()
        self.prepareSettings()

    def __del__(self):
        if self.isConnected:
            try:
                self.close()
            except:
                pass
                
    def connectToDevice(self):
        device = self.findPowermeter()
        if device == []:
            raise PowermeterError('powermeter not found')
        self.pm100usb = self.rm.open_resource(device)
        self.isConnected = True
        logging.debug('connected PM100USB')

    def close(self):
        if self.isConnected:
            self.pm100usb.close()
            self.isConnected = False
            logging.info('disconnected PM100USB')
        else:
            print('connection to powermeter already closed')
            logging.debug('attempt to close already disconnected PM100USB')

    def findPowermeter(self):
        devices = self.rm.list_resources(self.resourceString)
        logging.debug('found powermeters: %s' % str(devices))
        if devices:
            if len(devices)>1:
                raise PowermeterError('more than one powermeter found!')
            else:
                return devices[0]

    def getPmInfo(self):
        # first get power meter info
        idn = self.pm100usb.ask('*IDN?')
        [t, modelCode, serialnr, firmwareVersion] = idn.strip().split(',')
        self.powermeter = struct
        self.powermeter.pm100usb = struct
        self.powermeter.pm100usb.modelCode = modelCode
        self.powermeter.pm100usb.serialnr = serialnr
        self.powermeter.pm100usb.firmwareVersion = firmwareVersion
        logging.debug('PM100USB id: %s' % str(idn))

        # next get power meter sensor info
        self.powermeter.sensor = struct
        info = self.pm100usb.ask('SYST:SENS:IDN?')
        [sensModel, serialNr, calDate, type, subtype, flags] = info.strip().split(',')
        self.powermeter.sensor.model = sensModel
        self.powermeter.sensor.serialNr = serialNr
        self.powermeter.sensor.calDate = calDate
        self.powermeter.sensor.responseValue = float(self.pm100usb.ask('SENS:CORR:POW:THER:RESP?')) # in V/W
        logging.debug('PM100USB info: %s' % str(info))
        
    def prepareSettings(self):
        self.pm100usb.write('SYST:LFR 50')            # set to 50 Hz
        self.pm100usb.write('INPUT:ADAPTER:TYPE THER') # sets thermopile default detector type
        self.pm100usb.write('SENS:CORR:WAV %d' % self.pm100usb_ini['wavelength']) # 10.6 um wavelenth
        self.pm100usb.write('SENS:AVER:COUNT %d' % self.pm100usb_ini['averages']) # averaging
        self.pm100usb.write('SENS:POW:RANG:AUTO ON')  # autorange
        self.pm100usb.write('SENS:POW:UNIT W')
        self.pm100usb.write('SENS:POW:REF:STAT OFF')  # no 
        self.pm100usb.write('INPUT:THER:ACCELERATOR OFF')
        self.pm100usb.write('CONF:POW')  #prepare for power measurement
        self.isConfigured = True
        logging.debug('powermeter configured for use')

    def readPower(self):
        power = self.pm100usb.ask('READ?')
        logging.debug('measured power: %s' % power)
        return float(power)
        