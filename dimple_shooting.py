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
        self._powermeter = powermeter
        self.awg = awg
        self.powermeter_ini = powermeter_ini
        self.awg_ini = awg_ini
        self.dimple_shooting_ini = dimple_shooting_ini
        if not powermeter.isConfigured:
            msg = 'powermeter is not yet configured'
            print(msg)
            logging.error(msg)
            raise DimpleShootingError(msg)
        if not awg.isConfigured:
            msg = 'AWG is not yet configured'
            logging.error(msg)
            raise DimpleShootingError(msg)

    def sendShot(self, powerCorrection,  **kwargs):
        '''
        default values for kwargs: (period=5E-6, width=1E-6, height=5V, nr_pulses=1)
        '''

        period = kwargs.get('period', self.dimple_shooting_ini['pulse'] + self.dimple_shooting_ini['length'])
        if kwargs.get('period', None):
            msg = 'using non-standard value for (pulse train) period: %E.3s' % period
            print(msg)
            logging.info(msg)
        else:
            msg = 'using non-standard value for (pulse train) period: %E.3s' % period
            logging.info(msg)
            
        width = kwargs.get('width', self.dimple_shooting_ini['width'])
        if kwargs.get('width', None):
            msg = 'using non-standard value for pulse width: %E.3s' % width
            print(msg)
            logging.info(msg)
        else:
            msg = 'using non-standard value for pulse width: %E.3s' % width
            logging.info(msg)

        nr_pulses = int(kwargs.get('nr_pulses', self.dimple_shooting_ini['nr_pulses']))
        if kwargs.get('nr_pulses', None):
            msg = 'using non-standard value for number of pulses: %d' % int(nr_pulses)
            print(msg)
            logging.info(msg)
        else:
            msg = 'using standard value for number of pulses: %d' % int(nr_pulses)
            logging.info(msg)

        height = kwargs.get('height', self.dimple_shooting_ini['height'])
        if kwargs.get('height', None):
            msg = 'using non-standard value for number of pulse height: %.4fV' % height
            print(msg)
            logging.info(msg)
        else:
            msg = 'using standard value for number of pulse height: %.4fV' % height
            logging.info(msg)
        if powerCorrection:
            logging.info('apply power measurement correction')
            actualPower = self._powermeter.readPower()
            power_correction_factor = actualPower / self.dimple_shooting_ini['default_power']
            logging.info('Apply power correction factor: %.3f' % power_correction_factor)
            height = power_correction_factor * height
            msg = 'pulse height after correction for laser output power: %.4fV' % height
            print(msg)
            logging.info(msg)
            
        self.awg.prepareNextBurst(period, width, height, nr_pulses)
        self.awg.sendBurst()
