# -*- coding: utf-8 -*-
"""
Small script which records the position signal from the piezo strain gauge.
Created on Fri Oct 21 14:16:02 2016

@author: eschenm
"""

import time
import labjack


duration = 10  # number of seconds to record position

u3 = labjack.LabJackU3()

starttime = time.time()
nw = time.localtime(starttime)
timestr = ("%04d%02d%02dT%02d%02d%02d" % (nw[0], nw[1], nw[2], nw[3], nw[4], nw[5]))
filename = ("%s_position.log" % timestr)
logfile = open(filename, 'w')
print('logging piezo position to %s' % filename)
logfile.write('%s ms  Position\n' % timestr)

tm = time.time()
while tm < starttime+duration:
    nw = time.localtime(tm)
    ms =  round((tm%1)*1000) # nr of milliseconds
    pos = u3.device.getAIN(0)
    timestr = ("%04d%02d%02dT%02d%02d%02d" % (nw[0], nw[1], nw[2], nw[3], nw[4], nw[5]))
    logline = ("%s %03d %+.5f\n" % (timestr, ms, pos))
    logfile.write(logline)
    tm = time.time()
    
logfile.flush()
logfile.close()
print('logfile %s closed' % logfile.name)
