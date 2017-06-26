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

def startLogger(logPath = '.', level = logging.NOTSET):
    if not os.path.exists(logPath):
        raise LoggerError('path does not exist: %s' % logPath)
    logFile = time.strftime('%Y%m%dT%H%M%S_fdms.log')
    LOG_FILE = os.path.join(logPath, logFile)
    print('Logging to %s' % LOG_FILE)
    FORMAT = '%(asctime)s.%(msecs)03d %(levelname)s %(filename)s %(funcName)s: %(message)s'
    logging.basicConfig(format=FORMAT,
                        datefmt='%Y%m%dT%H%M%S',
                        filename=LOG_FILE,
                        level=level, )
    logging.info('Started logging')

