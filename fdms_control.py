# -*- coding: utf-8 -*-
"""
Routine for recording piezo calibration
M. Eschen - (C) 2017
"""

import time, sys, os, logging
import logger, pidControl, camera, sdg2000x, pm100usb, measure_surface
from iniparser import parseInifile

if sys.version_info > (3,):
    class FdmsError(Exception):
        pass
else:
    class FdmsError(StandardError):
        pass

INIFILE = 'fdms.ini'
LOGLEVEL = logging.DEBUG
datapath = '.\data'  #this is the dir in which daily dirs are created
today = time.strftime('%Y%m%d')
datapath = os.path.join(datapath, today)
if not os.path.exists(datapath):
    os.mkdir(datapath)
    logging.debug('created new directory %s' % datapath)

logger.startLogger(logPath=datapath, level = LOGLEVEL)

(piezo_ini, camera_ini, phase_stepping_ini, dimple_shooting_ini, powermeter_ini, awg_ini) = parseInifile(INIFILE)

u3 = pidControl.connectU3()
parameters = {'pid': piezo_ini['pid'],
              'setpoint': piezo_ini['offset'], 
              'ovMin': -0.5,
              'ovMax': 10.0,
              'pausetime': 0.005,}
ctrl = pidControl.PidController(u3, **parameters)
ctrl.start()
logging.log('pid', 'started PID loop')
# wait for pid loop to stabilize
time.sleep(0.25)
if ctrl.getError > piezo_ini['maxError']:
    logging.error('piezo not within errormargin after initialisation')
    raise FdmsError('piezo not at setpoint after initialisation')

cam = camera.Camera(camera_ini)
awg = sdg2000x.Sdg2000x(awg_ini)
powermeter = pm100usb.Pm100usb(powermeter_ini)

logging.info('all hardware now connected')

# measure_surface = measure_surface.Phase_stepping(piezo_ini, phase_stepping_ini, cam, ctrl, datapath)
# create dimple shooting class instance :
#    dimple = dimple_shooting.ShootDimple(dimple_shooting_ini, awg, powermeter)


def stopFdms():
    # closing connections
    logging.info('shutting down application')
    try:
        ctrl.terminate()
    finally:
        pass
    try:
        cam.close()
    finally:
        pass
    try:
        powermeter.close()
    finally:
        pass
    try:
        awg.close()
    finally:
        pass
    
    logging.info('stop log')
    logging.shutdown()



