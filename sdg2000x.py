'''M. Eschen, 2017

class to control a Siglent SDG2000X series AWG via the
NI VISA library. Using the appropriate connection string
either USB or LAN can be used. By default, a single device
connected via USB will be interfaced. '''

import pyvisa
import sys
import struct
import time
import logging

if sys.version_info > (3,):
    class AwgError(Exception):
        pass
else:
    class AwgError(StandardError):
        pass

class Sdg2000x():
    # define constants
    # hardcoded connection string which assumes only a single AWG is detected

    def __init__(self, awg_ini, resourceName='', ):
        self.awg_ini = awg_ini
        self.resourceString = 'USB?*::0xF4EC::0xEE38::?*::INSTR'
        self.isConnected = False
        if resourceName:
            self.resourceString = resourceName
        self.rm = pyvisa.ResourceManager()
        self.connectToDevice()
        self.getAwgInfo()
        self.prepareSettings()

    def __del__(self):
        if self.isConnected:
            logging.warning('disconnecting AWG withoud closing first')
            try:
                self.close()
            except:
                pass

    def connectToDevice(self):
        device = self.findAwg()
        if device == []:
            raise AwgError('AWG not found')
        self.awgDev = self.rm.open_resource(device)
        self.isConnected = True
        logging.info('AWG connected')

    def close(self):
        if self.isConnected:
            self.setOutput(1,False)
            self.setOutput(2,False)
            self.awgDev.close()
            self.isConnected = False
            logging.info('AWG disconnected')
        else:
            print('connection to AWG is already closed')
            logging.debug('attempt to close already disconnected AWG')

    def findAwg(self):
        devices = self.rm.list_resources(self.resourceString)
        logging.debug('found awg\'s: %s' % str(devices))
        if devices:
            if (len(devices)) > 1:
                raise AwgError('more than one AWG found!')
            else:
                return devices[0]

    def getAwgInfo(self):
        self.awginfo = struct
        idn = self.awgDev.ask('*IDN?').strip()
        [mfg, model, serialNr, fwVersion] = idn.split(',')
        self.awginfo.model = model
        self.awginfo.serialNr = serialNr
        self.awginfo.fwVersion = fwVersion
        logging.debug('AWG id: %s' % idn)

    def prepareSettings(self):
        self.awgDev.write('*RST')   # reset to factory defaults
        time.sleep(0.25)
        self.awgDev.write('BUZZ OFF')
        self.setLoad(self.awg_ini['channel'], self.awg_ini['load'])
        self.awgDev.write('C%d:OUTP PLRT, NOR' % self.awg_ini['channel'])

    def setLoad(self, channel, load):
        if str(load).lower() == 'hiz':
            load = load.upper()
        elif int(load) >= 50 and int(load) <= 100000:
            load = str(int(load))
        elif int(load) > 10000:
            load = 'HIZ'
        else:
            logging.error('AWG: specified invalid output load')
            raise AwgError('AWG invalid output load')
        if channel in (1, 2):
                self.awgDev.write('C%d:OUTP LOAD, %s' % (channel, str(load)))
                logging.debug('AWG enabled channel %d' % channel)
        else:
            logging.error('AWG: specified invalid output channel')
            raise AwgError('invalid channel')
        
    def prepareBurst(self, period, width, height, cycles):
        self.setOutput(1, False)
        self.awgDev.write('C%d:BSWV WVTP, PULSE' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BSWV LLEV, 0V' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BSWV HLEV, %.4fV' % (self.awg_ini['channel'], height))
        self.awgDev.write('C%d:BSWV PERI, %.5E'% (self.awg_ini['channel'], period))
        self.awgDev.write('C%d:BSWV WIDTH, %.5E' % (self.awg_ini['channel'], width))
        self.awgDev.write('C%d:BSWV DLY, 0' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BSWV RISE, 8.4E-9S' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BSWV FALL, 8.4E-9S' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BTWV STATE ON' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BTWV TRSR MAN' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BTWV GATE_NCYC, NCYC' % self.awg_ini['channel'])
        self.awgDev.write('C%d:BTWV TIME, %d' % (self.awg_ini['channel'], cycles))
        self.setOutput(self.awg_ini['channel'], True)
        logging.info('AWG armed: period=%.5Es, width=%.5Es, height=%.4E, cycles=%d' % (period, width, height, cycles))

    def sendBurst(self):
        self.awgDev.write('C%d:BTWV MTRIG' % self.awg_ini['channel'])
        logging.info('triggered AWG')

    def setOutput(self, channel, state):
        if type(state) is not bool:
            raise AwgError('invalid state, boolean expected')
        if channel in (1, 2):
            if state:
                self.awgDev.write('C%d:OUTP ON' % channel)
                logging.debug('AWG enabled channel %d' % channel)
            else:
                self.awgDev.write('C%d:OUTP OFF'%channel)
                logging.debug('AWG disabled channel %d' % channel)
        else:
            raise AwgError('invalid channel')

if __name__ == '__main__':
    awg = Sdg2000x()
    time.sleep(1)
    print(awg.awginfo.model)
    print(awg.awginfo.serialNr)
    print(awg.awginfo.fwVersion)
    awg.close()
