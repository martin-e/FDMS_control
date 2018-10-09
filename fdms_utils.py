# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 13:09:11 2017

@author: eschenm
"""

import logging, sys, os, time

# define error class compatible with python 2.7 and 3.X
if sys.version_info > (3,):
    class LoggerError(Exception):
        pass
else:
    class LoggerError(StandardError):
        pass

def startLogger(logPath='.', level=logging.NOTSET):
    if not os.path.exists(logPath):
        raise LoggerError('path does not exist: %s' % logPath)
    logFile = time.strftime('%Y%m%dT%H%M%S_fdms.log')
    LOG_FILE = os.path.join(logPath, logFile)
    print('Logging to %s' % LOG_FILE)
    FORMAT = '%(asctime)s %(levelname)s %(filename)s %(funcName)s: %(message)s'
    log = logging.getLogger('fdms_utils')
    log.setLevel(level)
    # create file handler
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(level)
    formatter = logging.Formatter(FORMAT)
    fh.setFormatter(formatter)
    # add the handler to the logger
    log.addHandler(fh)
    log = logging.getLogger('spam_application')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    log.addHandler(ch)


    '''logging.basicConfig(format=FORMAT,
                        datefmt='%Y%m%dT%H%M%S',
                        level=level,)
                        filename=LOG_FILE,
						filemode='w')'''
    log.info('Started logging')

def createDailydir(datapath):
    today = time.strftime('%Y%m%d')
    dailydir = os.path.join(datapath, today)
    new_dir_logmessage = ''
    if not os.path.exists(dailydir):
        os.mkdir(dailydir)
        print('created new directory %s' % dailydir)
    return dailydir
