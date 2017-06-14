# -*- coding: utf-8 -*-
"""
Top level file for recording
M. Eschen - (C) 2017
"""

import time, sys, os, logging
import logger
import analyze_surface

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

(fdms_ini, piezo_ini, camera_ini, phase_stepping_ini, \
 powermeter_ini, awg_ini, dimple_shooting_ini) =  parseInifile(INIFILE)

MEASURE_SURFACE = fdms_ini['MEASURE_SURFACE']
SHOOT_DIMPLE = fdms_ini['SHOOT_DIMPLE']

analyzer = analyze_surface.AnalyzeSurface(datapath)

if MEASURE_SURFACE:
    import camera, pidControl, measure_surface

    logging.info('setting up connections for measuring surface')
    u3 = pidControl.connectU3()
    parameters = {'pid': piezo_ini['pid'],
                  'setpoint': piezo_ini['offset'], 
                  'ovMin': -0.5,
                  'ovMax': 10.0,
                  'pausetime': 0.005,}
    ctrl = pidControl.PidController(u3, **parameters)
    ctrl.start()
    logging.info('started PID loop')
    # wait for pid loop to stabilize
    start = time.time()
    while abs(ctrl.getError()) > piezo_ini['maxError']:
        if (time.time() - start) > 5:
            logging.error('piezo not within errormargin after initialisation')
            raise FdmsError('piezo not at setpoint after initialisation')
        time.sleep(0.1)
    
    cam = camera.Camera(camera_ini)
    
    measure = measure_surface.Phase_stepping(piezo_ini, phase_stepping_ini, cam, ctrl, datapath)

if SHOOT_DIMPLE:
    import sdg2000x, pm100usb, dimple_shooting

    logging.info('setting up connections for shooting dimples')
    awg = sdg2000x.Sdg2000x(awg_ini)
    powermeter = pm100usb.Pm100usb(powermeter_ini)
    
    shoot = dimple_shooting.DimpleShooting(powermeter_ini, awg_ini, dimple_shooting_ini, powermeter, awg)
    
    msg = 'all hardware now connected'
    logging.info(msg)
    print(msg)

# create dimple shooting class instance :
#    dimple = dimple_shooting.ShootDimple(dimple_shooting_ini, awg, powermeter)

def stopFdms():
    # closing connections
    logging.info('shutting down application')
    if MEASURE_SURFACE:
        try:
            ctrl.terminate()
            del ctrl
        finally:
            pass
        try:
            cam.close()
        finally:
            pass
    if SHOOT_DIMPLE:
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
