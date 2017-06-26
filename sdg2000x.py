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
    def __init__(self, awg_ini, resourceName='', ):
        self.awg_ini = awg_ini
        self.resourceString = 'USB?*::0xF4EC::0xEE38::?*::INSTR'
        self.isConnected = False
        self.isConfigured = False
        self.isArmed = False
        if resourceName:
            self.resourceString = resourceName
        self.rm = pyvisa.ResourceManager()
        self._connectToDevice()
        self._getAwgInfo()
        self._prepareSettings()
        self.isConfigured = True

    def __del__(self):
        if self.isConnected:
            logging.warning('disconnecting AWG withoud closing first')
            try:
                self.close()
            except:
                pass

    def _connectToDevice(self):
        device = self._findAwg()
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

    def _findAwg(self):
        devices = self.rm.list_resources(self.resourceString)
        if devices:
            if (len(devices) > 1):
                msg = 'more than one AWG found!'
                logging.info(msg)
                raise AwgError('more than one AWG found!')
            device = devices[0]
            logging.debug('found awg: %s' % device)
            return device
        else:
            logging.debug('AWG not found')

    def _getAwgInfo(self):
        self.awginfo = dict()
        idn = self.awgDev.ask('*IDN?').strip()
        [mfg, model, serialNr, fwVersion] = idn.split(',')
        self.awginfo['model'] = model
        self.awginfo['serialNr'] = serialNr
        self.awginfo['fwVersion'] = fwVersion
        logging.debug('AWG id: %s' % idn)

    def _prepareSettings(self):
        self.awgDev.write('*RST')   # reset to factory defaults
        time.sleep(0.25)
        self.awgDev.write('BUZZ OFF')
        (self.channel,  load) = (self.awg_ini['channel'], self.awg_ini['load'])
        self.setLoad(self.channel,  load)
        self.awgDev.write('C%d:OUTP PLRT, NOR' % self.channel)
        logging.debug('AWG: channel %d polarity to normal and load to %s' % (self.channel,  str(load)))

    def setLoad(self, channel, load):
        if str(load).lower() == 'hiz':
            load = load.upper()
        elif int(load) >= 50 and int(load) <= 100000:
            load = str(int(load))
        elif int(load) > 100000:
            load = 'HIZ'
        else:
            msg = 'AWG: specified invalid output load in ini file: %s' % load
            logging.error(msg)
            raise AwgError(msg)
        if channel in (1, 2):
                self.awgDev.write('C%d:OUTP LOAD, %s' % (channel, str(load)))
                logging.debug('AWG enabled channel %d' % channel)
        else:
            msg = 'AWG: specified invalid output channel in ini file: %d' % channel
            logging.error(msg)
            raise AwgError(msg)
        
    def prepareNextBurst(self, period, width, height, cycles):
        self.setOutput(self.channel, False)
        self.awgDev.write('C%d:BSWV WVTP, PULSE' % self.channel)
        self.awgDev.write('C%d:BSWV LLEV, 0V' % self.channel)
        self.awgDev.write('C%d:BSWV HLEV, %.4fV' % (self.channel, height))
        self.awgDev.write('C%d:BSWV PERI, %.5E'% (self.channel, period))
        self.awgDev.write('C%d:BSWV WIDTH, %.5E' % (self.channel, width))
        self.awgDev.write('C%d:BSWV DLY, 0' % self.channel)
        self.awgDev.write('C%d:BSWV RISE, 8.4E-9S' % self.channel)
        self.awgDev.write('C%d:BSWV FALL, 8.4E-9S' % self.channel)
        self.awgDev.write('C%d:BTWV STATE ON' % self.channel)
        self.awgDev.write('C%d:BTWV TRSR MAN' % self.channel)
        self.awgDev.write('C%d:BTWV GATE_NCYC, NCYC' % self.channel)
        self.awgDev.write('C%d:BTWV TIME, %d' % (self.channel, cycles))
        self.setOutput(self.channel, True)
        self.isArmed = True
        self.duration = cycles * period
        logging.info('AWG armed: period=%.5Es, width=%.5Es, height=%.4E, cycles=%d' % (period, width, height, cycles))

    def sendBurst(self):
        if not self.isArmed:
            raise AwgError('awg is not armed, cannot trigger burst signal')
        self.awgDev.write('C%d:BTWV MTRIG' % self.channel)
        logging.info('triggered AWG')
        time.sleep(self.duration)
        self.setOutput(self.channel, False)
        self.isArmed = False
        logging.info('disarmed AWG')

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
    print(awg.awginfo['model'])
    print(awg.awginfo['serialNr'])
    print(awg.awginfo['fwVersion'])
    (period,  width,  height,  cycles) = (1E-4,  12E-6,  7.5,  1)
    # prepareBurst(period, width, height, cycles)
    #  sendBurst()
    awg.close()
