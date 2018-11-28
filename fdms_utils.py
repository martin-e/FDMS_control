# -*- coding: utf-8 -*-
"""
@author: eschenm
"""

import logging
import sys
import os
import time


class LoggerError(Exception):
    pass


def startLogger(logPath='.', level=logging.NOTSET):
    if not os.path.exists(logPath):
        raise LoggerError('path does not exist: %s' % logPath)
    logFilename = time.strftime('%Y%m%dT%H%M%S_fdms.log')
    LOG_FILE = os.path.join(logPath, logFilename)
    print('Logging to %s' % LOG_FILE)
    FORMAT = '%(asctime)s %(levelname)s %(filename)s %(funcName)s: %(message)s'
    logging.basicConfig(format=FORMAT,
                        datefmt='%Y%m%dT%H%M%S',
                        level=level,
                        filename=LOG_FILE,
						filemode='a')
    logging.info('Started logging')

def createDailydir(datapath):
    today = time.strftime('%Y%m%d')
    dailydir = os.path.join(datapath, today)
    new_dir_logmessage = ''
    if not os.path.exists(dailydir):
        os.mkdir(dailydir)
        print('created new directory %s' % dailydir)
    return dailydir
