# -*- coding: utf-8 -*-
"""
Created on Sat Jun 10 22:45:46 2017

@author: eschenm
"""
from configparser import ConfigParser
import logging

def parseInifile(file):
    parser = ConfigParser()
    parser.read(file)
    logging.debug('read ini settings')

    fdms = dict()
    bools = ('MEASURE_SURFACE', 'SHOOT_DIMPLE')
    for option in bools:
        fdms[option] = parser.getboolean('fdms', option)
    
    # this section starts all connections
    # piezo pid control
    piezo = dict()
    floats = ('offset', 'pvperfringe', 'pvmin', 'pvmax', 'maxError', )
    for option in floats:
        piezo[option] = float(parser.get('piezo', option))
    piezo['pid'] = tuple([float(val) for val in parser.get('piezo', 'pid').split(',')])

    # reading camera ini settings
    camera = dict()
    floats = ('framerate', 'integrationTime', )
    ints = ('nrBits', 'fm7Mode', )
    for option in floats:
        camera[option] = float(parser.get('camera', option))
    for option in ints:
        camera[option] = int(parser.get('camera', option))
    camera['roi'] = [int(val) for val in parser.get('camera', 'roi').split(',')]

    # reading awg ini settings
    awg = dict()
    ints = ('channel', )
    strings = ('load', )
    for option in ints:
        awg[option] = int(parser.get('awg', option))
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
    floats = ('interval', 'length', 'default_power', )
    ints = ('nr_pulses', )
    for option in floats:
        dimple_shooting[option] = float(parser.get('dimple_shooting', option))
    for option in ints:
        dimple_shooting[option] = int(parser.get('dimple_shooting', option))
    
    return fdms, piezo, camera, phase_stepping, powermeter, awg, dimple_shooting
