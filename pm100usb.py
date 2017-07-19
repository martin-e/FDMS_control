'''M. Eschen, 2017

class to control a Thorlabs PM100USB power meter via the 
NI VISA library. By default, a single device 
connected will be interfaced.'''

import pyvisa
import sys
import struct
import logging

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
        self._connectToDevice()
        self._getPmInfo()
        self.prepareSettings()

    def __del__(self):
        if self.isConnected:
            try:
                self.close()
            except:
                pass
                
    def _connectToDevice(self):
        device = self._findPowermeter()
        if len(device) == 0:
            msg = 'powermeter not found'
            logging.error(msg)
            raise PowermeterError(msg)
        self.pm100usb_dev = self.rm.open_resource(device)
        self.isConnected = True
        logging.debug('connected PM100USB')

    def close(self):
        if self.isConnected:
            self.pm100usb_dev.close()
            self.isConnected = False
            logging.info('disconnected PM100USB powermeter')
        else:
            print('connection to powermeter already closed')
            logging.debug('attempt to close already disconnected PM100USB')

    def _findPowermeter(self):
        devices = self.rm.list_resources(self.resourceString)
        if devices:
            for line in str(devices).splitlines():
                logging.debug('found powermeter: %s' % line)
            if len(devices) > 1:
                msg = 'more than one powermeter found!'
                logging.error(msg)
                raise PowermeterError(msg)
            else:
                return devices[0]
        return devices

    def _getPmInfo(self):
        # first get power meter info
        idn = self.pm100usb_dev.ask('*IDN?')
        [t, modelCode, serialnr, firmwareVersion] = idn.strip().split(',')
        self.pm100usb_data = dict()
        self.pm100usb_data['modelCode'] = modelCode
        self.pm100usb_data['serialnr'] = serialnr
        self.pm100usb_data['firmwareVersion'] = firmwareVersion
        logging.info('PM100USB powermeter data:')
        for (k,  v) in self.pm100usb_data.items():
            logging.info('\t%s:  %s' % (k,  str(v)))
        # next get power meter sensor info
        self.sensor_data = dict()
        info = self.pm100usb_dev.ask('SYST:SENS:IDN?')
        [sensModel, serialNr, calDate, sensorType, subtype, flags] = info.strip().split(',')
        self.sensor_data['model'] = sensModel
        self.sensor_data['serialNr'] = serialNr
        self.sensor_data['calDate'] = calDate
        self.sensor_data['type'] = sensorType
        self.sensor_data['subtype'] = subtype
        self.sensor_data['responseValue'] = float(self.pm100usb_dev.ask('SENS:CORR:POW:THER:RESP?')) # in V/W
        logging.info('PM100USB sensor head data:')
        for (k,  v) in self.sensor_data.items():
            logging.info('\t%s:  %s' % (k,  str(v)))
       
    def prepareSettings(self):
        self.pm100usb_dev.write('SYST:LFR 50')            # set to 50 Hz
        self.pm100usb_dev.write('INPUT:ADAPTER:TYPE THER') # sets thermopile default detector type
        self.pm100usb_dev.write('SENS:CORR:WAV %d' % self.pm100usb_ini['wavelength']) # 10.6 um wavelenth
        logging.info('set powermeter wavelength correction to %d nm' % self.pm100usb_ini['wavelength'])
        self.pm100usb_dev.write('SENS:AVER:COUNT %d' % self.pm100usb_ini['averages']) # averaging
        logging.info('set powermeter averaging to %d samples' % self.pm100usb_ini['averages'])
        self.pm100usb_dev.write('SENS:POW:RANG:AUTO ON')  # autorange
        self.pm100usb_dev.write('SENS:POW:UNIT W')
        self.pm100usb_dev.write('SENS:POW:REF:STAT OFF')
        self.pm100usb_dev.write('INPUT:THER:ACCELERATOR OFF')
        self.pm100usb_dev.write('CONF:POW')  #prepare for power measurement
        self.isConfigured = True
        logging.info('powermeter configured for use')

    def readPower(self):
        if self.isConfigured:
            power = self.pm100usb_dev.ask('READ?')
            logging.debug('measured power: %s' % power)
            return float(power)
        else:
            msg = 'powermeter is not configured, run prepareSettings() first'
            logging.error(msg)
            raise PowermeterError(msg)
        
