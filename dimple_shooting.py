# -*- coding: utf-8 -*-
"""
@author: eschenm
"""

import logging
import sys

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
        optional kwargs: (period=5E-6, width=1E-6, height=5V, nr_pulses=1)
        '''
        defaultPeriod = (self.dimple_shooting_ini['pulse'] + self.dimple_shooting_ini['length'])
        period = kwargs.get('period', default=defaultPeriod)
        if kwargs.get('period') is None:
            msg = 'using non-default value for (pulse train) period: %E.3s' % period
            print(msg)
            logging.debug(msg)

        defaultWidth = self.dimple_shooting_ini['width']
        width = kwargs.get('width', default=defaultWidth)
        if kwargs.get('width') is None:
            msg = 'using non-default value for pulse width: %E.3s' % width
            print(msg)
            logging.debug(msg)

        defaultNrPulses = self.dimple_shooting_ini['nr_pulses']
        cycles = int(kwargs.get('nr_pulses', default=defaultNrPulses))
        if kwargs.get('nr_pulses') is None:
            msg = 'using non-default value for number of pulses: %d' % int(nr_pulses)
            print(msg)
            logging.debug(msg)

        actualPower = self.powermeter.readPower()
        height = kwargs.get('height', default=(currentPower / self.dimple_shooting_ini['default_power'] * self.dimple_shooting_ini['height']))
        if kwargs.get('height') is None:
            msg = 'using non-default value for number of pulse height: %.4fV' % height
            print(msg)
            logging.debug(msg)
        self.awg.setIntensity(height)
        self.awg.prepareBurst(period, width, cycles)
        
    def shoot(self):
        self.awg.sendBurst()