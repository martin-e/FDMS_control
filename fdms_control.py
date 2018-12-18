# -*- coding: utf-8 -*-
"""
Top level file for FIBER DIMPLE MANUFACTUING SETUP control

Using this sofware the setup can either measure the profile of a fiber or 
fire a controlled laser pulse onto the fiber.

(Copyright) M. Eschen - 2017 - 2019
"""

import time
import sys
import os
import logging
import fdms_utils as utils
import iniparser
import analyze_surface


class FdmsError(Exception):
    pass


INIFILE = 'fdms.ini'
LOGLEVEL = logging.DEBUG
datapath = iniparser.getDatapath(INIFILE)
dailydir = utils.createDailydir(datapath)
print('storing logfile and measurement data in directory: %s' % dailydir)

utils.startLogger(logPath=dailydir, level=LOGLEVEL)
(fdms_ini, piezo_ini, camera_ini, phase_stepping_ini, \
 powermeter_ini, awg_ini, dimple_shooting_ini) = \
  iniparser.parseInifile(INIFILE)


log = logging.getLogger('fdms_control')

log.info('PIEZO ini settings:')
for (k, v) in piezo_ini.items():
    log.info('\t%s:  %s' %(k, str(v)))

log.info('CAMERA ini settings:')
for (k, v) in camera_ini.items():
    log.info('\t%s:  %s' %(k, str(v)))

log.info('PHASE STEPPING ini settings:')
for (k, v) in phase_stepping_ini.items():
    log.info('\t%s:  %s' %(k, str(v)))

log.info('POWERMETER ini settings:')
for (k, v) in powermeter_ini.items():
    log.info('\t%s:  %s' %(k, str(v)))

log.info('AWG ini settings:')
for (k, v) in awg_ini.items():
    log.info('\t%s:  %s' %(k, str(v)))
    
log.info('DIMPLE SHOOTING ini settings:')
for (k, v) in dimple_shooting_ini.items():
    log.info('\t%s:  %s' %(k, str(v)))
    
MEASURE_SURFACE = fdms_ini['MEASURE_SURFACE']
SHOOT_DIMPLE = fdms_ini['SHOOT_DIMPLE']
PLOT_SAVE = fdms_ini['PLOT_SAVE'] 
PLOT_SHOW = fdms_ini['PLOT_SHOW']

if MEASURE_SURFACE:
    import camera
    import pidControl
    import measure_surface

    log.info('setting up connections for measuring surface')
    u3 = pidControl.connectU3()
    parameters = {'pid': piezo_ini['pid'],
                  'setpoint': piezo_ini['offset'], 
                  'ovMin': -0.5,
                  'ovMax': 10.0,
                  'pausetime': 0.005,}
    ctrl = pidControl.PidController(u3, **parameters)
    ctrl.start()
    log.info('started PID loop')
    # wait for pid loop to stabilize
    start = time.time()
    while abs(ctrl.getError()) > piezo_ini['maxError']:
        if (time.time() - start) > 5:
            log.error('piezo not within errormargin after initialisation')
            log.warning('piezo not at setpoint after initialisation')
        time.sleep(0.1)
    
    cam = camera.CameraClient(camera_ini)
    
    measure = measure_surface.Phase_stepping(piezo_ini, phase_stepping_ini, cam, ctrl, dailydir)

if SHOOT_DIMPLE:
    import sdg2000x
    import pm100usb
    import dimple_shooting

    log.info('setting up connections for shooting dimples')
    awg = sdg2000x.Sdg2000x(awg_ini)
    powermeter = pm100usb.Pm100usb(powermeter_ini)
    
    shoot = dimple_shooting.DimpleShooting(powermeter_ini, awg_ini, dimple_shooting_ini, powermeter, awg)
    
msg = 'all hardware now connected'
log.info(msg)
print(msg)

# create dimple shooting class instance :
#    dimple = dimple_shooting.ShootDimple(dimple_shooting_ini, awg, powermeter)

def stopFdms():
    # closing connections
    log.info('shutting down application')
    if MEASURE_SURFACE:
        try:
            global ctrl
            ctrl.terminate()
            del ctrl
        except:
            pass
        finally:
            log.debug('pid loop stopped')

        try:
            global u3
            del u3
            log.debug('labjack disconnected')
        except:
            pass
        finally:
            pass

        try:
            global cam
            cam.close()
        except:
            pass
        finally:
            pass
        
    if SHOOT_DIMPLE:
        try:
            global powermeter
            powermeter.close()
        except:
            pass
        finally:
            pass
        
        try:
            global awg
            awg.close()
        except:
            pass
        finally:
            pass
    
    log.info('stop log')
    logging.shutdown()
    print('\n\nWARNING:  Restart python session before continuing with dimple shooting. Otherwise logging will not be stored!\n\n')
