# -*- coding: utf-8 -*-
"""
@author: eschenm
"""

import logging
from configparser import ConfigParser

def getDatapath(file):    
    parser = ConfigParser()
    parser.read(file)
    return parser.get('fdms', 'measure_datapath')

def parseInifile(file):
    log = logging.getLogger('iniparser')
    parser = ConfigParser()
    parser.read(file)

    fdms = dict()
    bools = ('MEASURE_SURFACE', 'SHOOT_DIMPLE', 'PLOT_SAVE', 'PLOT_SHOW', )
    strings = ('measure_datapath', )
    for option in bools:
        fdms[option] = parser.getboolean('fdms', option)
    for option in strings:
        fdms[option] = parser.get('fdms', option)
    
    # this section starts all connections
    # piezo pid control
    piezo = dict()
    floats = ('offset', 'pvperfringe', 'pvmin', 'pvmax', 'maxError', )
    for option in floats:
        piezo[option] = float(parser.get('piezo', option))
    piezo['pid'] = tuple([float(val) for val in parser.get('piezo', 'pid').split(',')])

    # reading camera ini settings
    camera = dict()
    floats = ('framerate', 'exposureTime', )
    ints = ('nrBits', )
    for option in floats:
        camera[option] = float(parser.get('camera', option))
    for option in ints:
        camera[option] = int(parser.get('camera', option))

    # reading awg ini settings
    # channel 1 MUST be connected to the digital input of the RF driver
    # channel 2 MUST be connected to analog input #1 of the RF driver
    # INCORRECT CONNECTIONS LIKELY RESULT IN PERMANENT DAMAGE TO THE SETUP!!!
    awg = dict()
    strings = ('load1', 'load2', )
    for option in strings:
        awg[option] = parser.get('awg', option)
    
    # reading powermeter ini settings
    powermeter = dict()
    ints = ('wavelength', 'averages', )
    for option in ints:
        powermeter[option] = int(parser.get('powermeter', option))

    # reading phase stepping ini settings
    phase_stepping = dict()
    floats = ('stepSize', 'wavelength', )
    ints = ('nrSteps', 'nrImages', )
    for option in floats:
        phase_stepping[option] = float(parser.get('phase_stepping', option))
    for option in ints:
        phase_stepping[option] = int(parser.get('phase_stepping', option))

    # reading dimple shooting settings
    dimple_shooting = dict()
    floats = ('period', 'width', 'default_power', 'default_height')
    ints = ('nr_pulses', )
    for option in floats:
        dimple_shooting[option] = float(parser.get('dimple_shooting', option))
    for option in ints:
        dimple_shooting[option] = int(parser.get('dimple_shooting', option))
    
    inis = ('fdms', 'piezo', 'camera', 'phase_stepping', 'powermeter', 'awg', \
            'dimple_shooting')
    for ini in inis:
        log.info('%s ini settings:' % ini.upper())
        for (k, v) in locals()[ini].items():
            log.info('\t%s:  %s' %(k, str(v)))
        
    return (fdms, piezo, camera, phase_stepping, powermeter, awg, \
            dimple_shooting)
