# -*- coding: utf-8 -*-
"""
@author: eschenm
"""

import logging
import sys
import time


class DimpleShootingError(Exception):
    pass


class DimpleShooting():
    def __init__(self, powermeter_ini, awg_ini, dimple_shooting_ini, powermeter, awg):
        self.powermeter = powermeter
        self.awg = awg
        self.powermeter_ini = powermeter_ini
        self.awg_ini = awg_ini
        self.dimple_shooting_ini = dimple_shooting_ini
        self.defaultHeight = 0
        if awg.isArmed == False:
            print('AWG is not armed')
            logging.warning('AWG is not armed')
        if powermeter.isConfigured == False:
            print('powermeter is not yet configured')
            logging.warning('powermeter is not yet configured')

    def prepareShot(self, **kwargs):
        '''prepareShot(width=150E-6, height=5.0, nr_pulses=10, period=1E-3)
        
        by default the values stored in the dimple_shooting section of fdms.ini are used
        width:      [float] pulse width in s
        height:     [float] pulse height 0 and 10V
        nrPulses:   [int] number of pulses
        period:     [float] multiple pulse period time in s
        '''

        txt = ['', 'This value is taken from the ini file']

        defaultWidth = self.dimple_shooting_ini['width']
        width = kwargs.get('width', defaultWidth)
        msg = 'using value for pulse width: %.3Es %s' % (width, txt[kwargs.get('width') is None])
        print(msg)
        logging.info(msg)

        cycles = int(kwargs.get('nr_pulses', self.dimple_shooting_ini['nr_pulses']))
        msg = 'number of pulses: %d %s' % (cycles, txt[kwargs.get('nr_pulses') is None])
        print(msg)
        logging.info(msg)

        defaultPeriod = self.dimple_shooting_ini['period']
        period = kwargs.get('period', defaultPeriod)
        msg = 'using value for (pulse train) period: %.3Es %s' % (period, txt[kwargs.get('period') is None])
        if cycles > 1:
            print(msg)
        logging.info(msg)

        height = kwargs.get('height', self.dimple_shooting_ini['default_height'])
        msg = 'using value for pulse height: %.4fV %s' % (height, txt[kwargs.get('height') is None])
        print(msg)
        logging.info(msg)
        self.awg.setIntensity(height)
        self.defaultHeight = height
        self.awg.prepareBurst(period, width, cycles)
        
    def shoot(self, correctPower=True):
        if self.awg.isArmed is False:
            raise DimpleShootingError('cannot shoot laser pulse, make sure shoot.prepareShot() has been run with correct parameters!!')
        currentPower = self.powermeter.readPower()
        msg = 'Measured actual powermeter value: %.3fW' % (currentPower)
        print(msg)
        logging.info(msg)
        if correctPower:
            correctedHeight = self.defaultHeight * (self.dimple_shooting_ini['default_power'] / currentPower)
            msg = 'Corrected pulse height is %.3EV' % (correctedHeight)
            print(msg)
            logging.info(msg)
            self.awg.setIntensity(correctedHeight)
        try:
            self.awg.sendBurst()
        except err as Error:
            msg = 'error during sending burst: %s' % err
            logging.error(msg)
            raise DimpleShootingError(msg)
        finally:
            # change pulse height setting back to non-powermeter corrected height value in case the next pulse wil be fired without height correction
            if correctPower:
                self.awg.setIntensity(self.defaultHeight)
                
    def prepareShotWithoutArm(self, **kwargs):
        # METHOD ASSUMES OUTPUTS ARE ENABLED!!!
        '''prepareShot(width=150E-6, height=5.0, nr_pulses=10, period=1E-3)
        
        by default the values stored in the dimple_shooting section of fdms.ini are used
        width:      [float] pulse width in s
        height:     [float] pulse height 0 and 10V
        nrPulses:   [int] number of pulses
        period:     [float] multiple pulse period time in s
        '''

        logging.info('enabled AWG outputs')
        time.sleep(1)
        
        txt = ['', 'This value is taken from the ini file']

        defaultWidth = self.dimple_shooting_ini['width']
        width = kwargs.get('width', defaultWidth)
        msg = 'using value for pulse width: %.3Es %s' % (width, txt[kwargs.get('width') is None])
        print(msg)
        logging.info(msg)

        cycles = int(kwargs.get('nr_pulses', self.dimple_shooting_ini['nr_pulses']))
        msg = 'number of pulses: %d %s' % (cycles, txt[kwargs.get('nr_pulses') is None])
        print(msg)
        logging.info(msg)

        defaultPeriod = self.dimple_shooting_ini['period']
        period = kwargs.get('period', defaultPeriod)
        msg = 'using value for (pulse train) period: %.3Es %s' % (period, txt[kwargs.get('period') is None])
        if cycles > 1:
            print(msg)
        logging.info(msg)

        height = kwargs.get('height', self.dimple_shooting_ini['default_height'])
        msg = 'using value for pulse height: %.4fV %s' % (height, txt[kwargs.get('height') is None])
        print(msg)
        logging.info(msg)
        self.awg.setIntensity(height)
        self.defaultHeight = height
        self.awg.prepareBurstWithoutArm(period, width, cycles)
        
    def shootWithoutArm(self, correctPower=True):
        # METHOD ASSUMES OUTPUTS ARE ENABLED!!!
        
        currentPower = self.powermeter.readPower()
        msg = 'Measured actual powermeter value: %.3fW' % (currentPower)
        print(msg)
        logging.info(msg)
        if correctPower:
            correctedHeight = self.defaultHeight * (self.dimple_shooting_ini['default_power'] / currentPower)
            msg = 'Corrected pulse height is %.3EV' % (correctedHeight)
            print(msg)
            logging.info(msg)
            self.awg.setIntensity(correctedHeight)
        try:
            self.awg.sendBurstWithoutArm()
        except err as Error:
            msg = 'error during sending burst: %s' % err
            logging.error(msg)
            raise DimpleShootingError(msg)
        finally:
            # change pulse height setting back to non-powermeter corrected height value in case the next pulse wil be fired without height correction
            if correctPower:
                self.awg.setIntensity(self.defaultHeight)
