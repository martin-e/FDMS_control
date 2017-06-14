# -*- coding: utf-8 -*-
"""
Class for creating dimples
Created on Mon Jun 12 12:08:32 2017

@author: eschenm
"""

import logging, sys

if sys.version_info > (3,):
    class DimpleShootingError(Exception):
        pass
else:
    class DimpleShootingError(StandardError):
        pass

class DimpleShooting():
    def __init__(self, powermeter_ini, awg_ini, dimple_shooting_ini, powermeter, awg):
        self.powermeter = powermeter
        self.awg = awg
        self.powermeter_ini = powermeter_ini
        self.awg_ini = awg_ini
        self.dimple_shooting_ini = dimple_shooting_ini
        if awg.isArmed == False:
            print('AWG is not armed')
            logging.warning('AWG is not armed')
        if powermeter.isConfigured == False:
            print('powermeter is not yet configured')
            logging.warning('powermeter is not yet configured')

    def prepareShot(self, **kwargs):
        '''
        optional kwargs: (period=5E-6, width=1E-6, height=5V, cycles=1)
        '''
        period = kwargs.get('period', self.dimple_shooting_ini['pulse'] + self.dimple_shooting_ini['length'])
        if kwargs.get('period', None):
            msg = 'using non-standard value for (pulse train) period: %E.3s' % period
            print(msg)
            logging.debug(msg)
        
        width = kwargs.get('width', self.dimple_shooting_ini['length'])
        if kwargs.get('width', None):
            msg = 'using non-standard value for pulse width: %E.3s' % width
            print(msg)
            logging.debug(msg)

            cycles = int(kwargs.get('cycles', self.dimple_shooting_ini['nr_pulses']))
        if kwargs.get('cycles', None):
            msg = 'using non-standard value for number of pulses: %d' % int(cycles)
            print(msg)
            logging.debug(msg)

        currentPower = self.powermeter.readPower()
        height = kwargs.get('height', (currentPower / self.dimple_shooting_ini['default_power'] * self.dimple_shooting_ini['height']))
        if kwargs.get('height', None):
            msg = 'using non-standard value for number of pulse height: %.4fV' % int(cycles)
            print(msg)
            logging.debug(msg)
        self.awg.prepareBurst(period, width, height, cycles)

    def shoot(self):
        self.awg.sendBurst()