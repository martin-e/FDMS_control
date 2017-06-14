# -*- coding: utf-8 -*-
"""
Class for creating dimples
Created on Mon Jun 12 12:08:32 2017

@author: eschenm
"""

import logging, sys, os
import numpy as np

if sys.version_info > (3,):
    class DimpleShootingError(Exception):
        pass
else:
    class DimpleShootingError(StandardError):
        pass

class DimpleShooting():
    def __init__(self, powermeter_ini, awg_ini, dimple_shooting_ini, powermeter, awg, ):
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
        optional kwargs: (period, width, height, cycles)
        '''
        period = kwargs.get('period', self.dimple_shooting_ini['pulse'] + self.dimple_shooting_ini['length'])
        currentPower = self.powermeter.readPower()
        width = kwargs.get('width', self.dimple_shooting_ini['length'])
        cycles = kwargs.get('cycles', self.dimple_shooting_ini['nr_pulses'])
        height = currentPower / self.dimple_shooting_ini['default_power'] * self.dimple_shooting_ini['height'])
        self.awg.prepareBurst(period, width, height, cycles)

    def shoot(self):
        self.awg.sendBurst()