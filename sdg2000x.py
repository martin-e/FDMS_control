# -*- coding: utf-8 -*-
'''M. Eschen, 2017

class to control a Siglent SDG2000X series AWG via the
NI VISA library. Using the appropriate connection string
either USB or LAN can be used. By default, a single device
connected via USB will be interfaced.

Channel 1 MUST be connected to the digital input of the RF driver
Channel 2 MUST be connected to analog input #1 of the RF driver
INCORRECT CONNECTIONS LIKELY RESULT IN PERMANENT DAMAGE TO THE SETUP!!!

@author: eschenm
'''

import pyvisa
import sys
import struct
import time
import logging

class AwgError(Exception):
    pass


log = logging.getLogger('SDG2000')
logging.getLogger('pyvisa').setLevel(logging.WARNING)

class Sdg2000x():
    def __init__(self, awg_ini, resourceName='', ):
        self.awg_ini = awg_ini
        self.resourceString = 'USB?*::0xF4EC::0xEE38::?*::INSTR'
        self.isConnected = False
        self.isArmed = False
        if resourceName:
            self.resourceString = resourceName
        self.rm = pyvisa.ResourceManager()
        self.connectToDevice()
        self.getAwgInfo()
        self.prepareSettings()

    def __del__(self):
        if self.isConnected:
            log.warning('disconnecting AWG withoud closing first')
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
        log.info('AWG connected')
        self.awgDev.timeout = 5000

    def close(self):
        if self.isConnected:
            self.setIntensity(0)
            self.setOutput(2,False)
            self.setOutput(1,False)
            self.awgDev.close()
            self.isConnected = False
            log.info('AWG disconnected')
        else:
            print('connection to AWG is already closed')
            log.debug('attempt to close already disconnected AWG')

    def findAwg(self):
        devices = self.rm.list_resources(self.resourceString)
        log.debug('found awg\'s: %s' % str(devices))
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
        log.debug('AWG id: %s' % idn)

    def prepareSettings(self):
        self.awgDev.write('*RST')   # reset to factory defaults
        time.sleep(0.25)
        self.awgDev.write('BUZZ OFF')
        self.setOutput(2, False)
        self.setOutput(1, False)
        self.setLoad(1, self.awg_ini['load1'])
        self.setLoad(2, self.awg_ini['load2'])
        self.awgDev.write('C1:OUTP PLRT, NOR')
        self.awgDev.write('C2:OUTP PLRT, NOR')
        # set waveform for Channel 2 to DC offset
        self.awgDev.write('C2:BSWV WVTP, DC')
        self.awgDev.write('C2:BSWV OFST, 0.0V')
        self.setOutput(2,False)
        self.awgDev.write('C1:BSWV WVTP, PULSE')
        self.awgDev.write('C1:BSWV LLEV, 0V')
        self.awgDev.write('C1:BSWV HLEV, 0.1V')
        self.awgDev.write('C1:BTWV STATE, ON')
        self.awgDev.write('C1:BTWV TRSR, MAN')        
        self.setOutput(1,True)
        

    def setLoad(self, channel, load):
        if str(load).lower() == 'hiz':
            load = load.upper()
        elif int(load) >= 50 and int(load) <= 100000:
            load = str(int(load))
        elif int(load) > 100000:
            load = 'HIZ'
        else:
            log.error('AWG: specified invalid output load')
            raise AwgError('AWG invalid output load')
        if channel in (1, 2):
                self.awgDev.write('C%d:OUTP LOAD, %s' % (channel, str(load)))
                log.debug('AWG enabled channel %d' % channel)
        else:
            log.error('AWG: specified invalid output channel')
            raise AwgError('invalid channel')
        

    def setIntensity(self, intensity):
        if intensity < 0 or intensity > 10:
            msg = 'intensity outside range 0 to 10 Volt!'
            log.error(msg)
            raise AwgError(msg)
        self.awgDev.write('C2:BSWV OFST, %.3fV' % intensity)

    def prepareBurst(self, period, width, cycles):
        # height for sending TTL pulse to the digital input
        height = 4.5
        self.awgDev.write('C1:BSWV WVTP, PULSE')
        self.awgDev.write('C1:BSWV LLEV, 0V')
        self.awgDev.write('C1:BSWV HLEV, %.4fV' % height)
        self.awgDev.write('C1:BSWV PERI, %.5E'  % period)
        self.awgDev.write('C1:BSWV WIDTH, %.5E' % width)
        self.awgDev.write('C1:BSWV DLY, 0')
        self.awgDev.write('C1:BSWV RISE, 8.4E-9S')
        self.awgDev.write('C1:BSWV FALL, 8.4E-9S')
        self.awgDev.write('C1:BTWV STATE, ON')
        self.awgDev.write('C1:BTWV TRSR, MAN')
        self.awgDev.write('C1:BTWV GATE_NCYC, NCYC')
        self.awgDev.write('C1:BTWV TIME, %d' % cycles)
        self.isArmed = True
        self.duration = cycles * period
        msg ='AWG armed: width=%.3Es, nr of cycles=%d, period=%.3Es and TTL height=%.3E' % (width, cycles, period, height)
        print(msg)
        logging.info(msg)

    def sendBurst(self):
        if not self.isArmed:
            raise AwgError('awg is not armed')
        try:
            self.setOutput(2,True)
            time.sleep(0.25)
            self.getOutput(2)
            self.awgDev.write('C1:BTWV MTRIG')
            log.info('triggered AWG')
            time.sleep(self.duration+0.4)
            self.setOutput(2,False)
        except Exception as e:
            msg = 'error during attempt to shoot laser, disarm. Error: %s' % e
            print(msg)
            log.warning(msg)
        self.setOutput(2,False)
        self.isArmed = False
        log.info('disarmed AWG')

    def prepareBurstWithoutArm(self, period, width, cycles):
        # METHOD ASSUMES OUTPUTS ARE ENABLED!!!
        # height for sending TTL pulse to the digital input
        height = 4.5
        self.setOutput(2,False)
        self.awgDev.write('C1:BSWV WVTP, PULSE')
        self.awgDev.write('C1:BSWV LLEV, 0V')
        self.awgDev.write('C1:BSWV HLEV, %.4fV' % height)
        self.awgDev.write('C1:BSWV PERI, %.5E'  % period)
        self.awgDev.write('C1:BSWV WIDTH, %.5E' % width)
        self.awgDev.write('C1:BSWV DLY, 0')
        self.awgDev.write('C1:BSWV RISE, 8.4E-9S')
        self.awgDev.write('C1:BSWV FALL, 8.4E-9S')
        self.awgDev.write('C1:BTWV STATE, ON')
        self.awgDev.write('C1:BTWV TRSR, MAN')
        self.awgDev.write('C1:BTWV GATE_NCYC, NCYC')
        self.awgDev.write('C1:BTWV TIME, %d' % cycles)
        try:
            int(self.awgDev.query('*OPC?'))
        except:
            pass
        self.duration = cycles * period + width
        msg ='AWG prepared: width=%.3Es, nr of cycles=%d, period=%.3Es and TTL height=%.3E' % (width, cycles, period, height)
        print(msg)
        logging.info(msg)
        time.sleep(1)
        self.setOutput(2,True)
        time.sleep(1)

    def sendBurstWithoutArm(self):
        # METHOD ASSUMES OUTPUTS ARE ENABLED!!!
        try:
            self.awgDev.write('C1:BTWV MTRIG')
            log.info('triggered AWG')
            time.sleep(self.duration+0.1)
        except Exception as e:
            msg = 'error during attempt to shoot laser. Error: %s' % e
            print(msg)
            log.warning(msg)
        self.isArmed = False
        log.info('disarmed AWG')

    def setOutput(self, channel, state):
        if type(state) is not bool:
            raise AwgError('invalid state, boolean expected')
        if channel in (1, 2):
            if state:
                self.awgDev.write('C%d:OUTP ON' % channel)
                log.debug('AWG enabled channel %d' % channel)
            else:
                if channel == 1 and self.getOutput(2):
                    msg = 'first turn of channel 2 before turning off channel 1!!!'
                    log.error(msg)
                    raise AwgError(msg)
                self.awgDev.write('C%d:OUTP OFF' % channel)
                log.debug('AWG disabled channel %d' % channel)
        else:
            raise AwgError('invalid channel')

    def getOutput(self, channel):
        # returns True when Output is enabled and False if not
        if channel in (1, 2):
            answer = self.awgDev.ask('C%d:OUTP?' % channel)
            log.debug('AWG channel %d status: %s' % (channel, str(answer)))
            if len(answer) > 12:
                state = answer.split(',')[0][8:]
                if state == 'OFF':
                    return False
                elif state == 'ON':
                    return True
                else:
                    msg = 'invalid state answer'
                    log.error(msg)
                    raise AwgError(msg + ': ' + answer)
        else:
            msg = 'invalid channel: %s' % str(channel)
            log.error(msg)
            raise AwgError(msg)
    

if __name__ == '__main__':
    
    awg = Sdg2000x()
    time.sleep(1)
    print(awg.awginfo.model)
    print(awg.awginfo.serialNr)
    print(awg.awginfo.fwVersion)
    #awg.close()
