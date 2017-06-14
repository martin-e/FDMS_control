# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 14:16:02 2016

@author: eschenm
"""

import time
from threading import Thread
from threading import Lock


class PidController(Thread):    
    def __init__(self, u3, pid=None, setpoint=0.0, ovMin=0.0, ovMax=10.0, pausetime=0.1, debug=False, logging=True):
        '''constructor '''
        Thread.__init__(self)
        self.lock = Lock()
        self._u3 = u3
        self._setpoint = setpoint
        self._ovMin = float(ovMin)
        self._ovMax = float(ovMax)
        self._prevError = 0
        self._currtm = time.time()
        self._prevtm = self._currtm
        self._pausetime = pausetime
        self._Ci = 0
        self._continue = True
        self._displayStatus = False
        self._pidInterval = []
        self._pidLoopCnt = 0
        self._pidLoopLen = 50
        self._readSamples = 5
        if pid is None:
            self.setPid((0, 0, 0))    
        else:
            self.setPid(pid)
        if debug:
            self._displayStatus = True
        if logging:
            nw = time.localtime(time.time())
            timestr = ("%04d%02d%02dT%02d%02d%02d" % (nw[0], nw[1], nw[2], nw[3], nw[4], nw[5]))
            filename = ("%s_piezo.log" % timestr)
            self._logfile = open(filename, 'w')
            print('logging piezo output to %s' % filename)
            self._logfile.write('%s ms  P     I       D      SP     Pv      Error  Output    Ci\n' % timestr)
        else:
            self._logfile = None
    
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        rtxt = "piezo control PID loop:\n"
        if self.isAlive():
            rtxt = rtxt + "\tstatus: running\n"
        else:
            rtxt = rtxt + "\tstatus: not running\n"
        rtxt = rtxt + "PID parameters:"
        pid = self.getPid()
        rtxt = rtxt + ("\tKp:%.3f Ki:%.3f Kd:%.3f\n" % (pid[0], pid[1], pid[2]))
        if self.isAlive():
            rtxt = rtxt + "setpoint: %.4f\n" % self.getSetpoint()
            rtxt = rtxt + "pv:       %.4f\n" % self.getPv()
            rtxt = rtxt + "error:    %.4f\n" % self.getError()
            rtxt = rtxt + "output:   %.4f\n" % self.getOutput()
            rtxt = rtxt + "Ci:       %.4f\n" % self.getCi()
            rtxt = rtxt + "Control freq: %.2f\n" % self.getPidLoopFrequency()
        return rtxt
        
    def logStats(self):
        if self._logfile:
            (sp, pid) = (self.getSetpoint(), self.getPid())
            if self.isAlive():
                (pv, er, ov, ci) = (self.getPv(), self.getError(), self.getOutput(), self.getCi())
            else:
                (pv, er, ov, ci) = (self.getPv(), 0., self.getOutput(), 0.)
            tm = time.time()
            nw = time.localtime(tm)
            ms =  round((tm%1)*1000) # nr of milliseconds
            timestr = ("%04d%02d%02dT%02d%02d%02d" % (nw[0], nw[1], nw[2], nw[3], nw[4], nw[5]))
            logline = ("%s %03d %.3f %.3f %.3f %+.3f %+.4f %+.4f %+.4f %+.4f\n" % (timestr, ms, pid[0], pid[1], pid[2], sp, pv, er, ov, ci))
            self._logfile.write(logline)
        return

    def stopLog(self):
        if self._logfile:
            if not self._logfile.closed:
                self._logfile.flush()
                self._logfile.close()
                print('logfile %s closed' % self._logfile.name)
            else:
                print('logfile already closed')

    def updatePidLoopInterval(self, interval):
        self.lock.acquire()
        if len(self._pidInterval) < self._pidLoopLen:
            self._pidInterval.append(interval)
        else:
            if self._pidLoopCnt == self._pidLoopLen:
                self._pidLoopCnt = 0
            self._pidInterval[self._pidLoopCnt] = interval
        self._pidLoopCnt += 1
        self.lock.release()
        
    def getPidLoopFrequency(self):
        self.lock.acquire()
        total = 0.0
        for value in self._pidInterval:
            total = total + value
        freq = self._pidLoopLen/total
        self.lock.release()
        return freq

    def getPid(self):
        self.lock.acquire()
        try:
            pid = (self._Kp, self._Ki, self._Kd)
        finally:
            self.lock.release()
        return pid

    def setPid(self, pid):
        self.lock.acquire()
        try:
            self._Kp = pid[0]
            self._Ki = pid[1]
            self._Kd = pid[2]
            self._Ci = 0
        finally:
            self.lock.release()
		
    def getSetpoint(self):
        self.lock.acquire()
        try:
            setpoint = self._setpoint
        finally:
            self.lock.release()
        return setpoint
        
    def setSetpoint(self, setpoint):
        self.lock.acquire()
        try:
            self._setpoint = setpoint
        finally:
            self.lock.release()
            
    def getPv(self):
        self.lock.acquire()
        try:
            pv = 0.0
            for ii in range(self._readSamples):
                pv += self._u3.adc.readValue()
            pv /= self._readSamples
        finally:
            self.lock.release()
        return pv

    def getCi(self):
        self.lock.acquire()
        try:
            ci = self._Ci
        finally:
            self.lock.release()
        return ci
		
    def terminate(self):
        self.lock.acquire()
        try:
            self._continue = False
        finally:
            self.lock.release()

    def calculateControlVariable(self, error):
        self._currtm = time.time()                # get t
        dt = self._currtm - self._prevtm          # get delta t
        de = error - self._prevError              # get delta error
        Cp = self._Kp * error                     # proportional term
        self._Ci += error * dt                    # integral term
        if abs(self._Ci) > 0.1:
            self._Ci = 0
        Cd = 0
        if dt > 0:                                # no div by zero
            Cd = de/dt                            # derivative term
        self._prevtm = self._currtm               # save t for next pass
        self._prevError = error                   # save t-1 error
        return (Cp + (self._Ki * self._Ci) + (self._Kd * Cd), dt)

    def getError(self):
        self.lock.acquire()
        try:
            setpoint = self._setpoint
            pv = self._u3.adc.readValue()
        finally:
            self.lock.release()
        return (setpoint - pv)

    def setOutput(self, value):
        if value > self._ovMax:
            value = self._ovMax
        if value < self._ovMin:
            value = self._ovMin
        self.lock.acquire()
        try:
            self._u3.piezo.setVoltage(value)
        finally:
            self.lock.release()
            
    def getOutput(self):
        self.lock.acquire()
        try:
            voltage = self._u3.piezo.getVoltage()
        finally:
            self.lock.release()
        return voltage
            
    def printStatus(self):
        print(self.__repr__())
        
    def run(self):
        n=0
        self.lock.acquire()
        try:
            self._Ci = 0
        finally:
            self.lock.release()

        while self._continue:
            error = self.getError()
            (self._output, interval) = self.calculateControlVariable(error)
            self.updatePidLoopInterval(interval)
            if self._output > self._ovMax:
                self._output = self._ovMax
            if self._output < self._ovMin:
                self._output = self._ovMin
            if self._displayStatus and n > 5/self._pausetime:
                self.printStatus()
                n=0
            #self.setOutput(self._output)
            self.setOutput(self._output)
            #n += 1
            #time.sleep(self._pausetime)
            if self._logfile:
                self.logStats()
        print("exiting pid control, set piezo voltage to 0.0")
        self.setOutput(0.0)
        self.logStats()
        time.sleep(0.5)
        self.logStats()
        self.stopLog()
                
    def laserPulse(self, length):
        self.lock.acquire()
        try:
            waittime = self._u3.pulser.pulse(length)
        finally:
            self.lock.release()         
        return waittime

    def laserGetOutputValue(self):
        self.lock.acquire()
        try:
            output = self._u3.pulser.getOutput()
        finally:
            self.lock.release()
        return output
    
    def __del__(self):
        try:
            self.terminate()
            self._u3.disconnect()
        finally:
            try:
                self.stopLog()
            finally:
                pass
        
if __name__ == '__main__':
    import labjack
    try:
        u3 = labjack.LabJackU3()
        u3.piezo = labjack.Piezo(u3)
        u3.adc = labjack.Adc(u3)
        u3.pulser = labjack.Pulser(u3)
        parameters = {'pid' : (1.2, 4e2, 0.002), 'setpoint' : 0.4, 'ovMin' : -0.5, 'ovMax' : 10.0, 'pausetime' : 0.005}
        ctrl = PidController(u3, debug=False, **parameters)
        ctrl.setPid([1,400,0.002])
        # ctrl.start()
        # [print("%.3f %+.3f %+.3f %+.3f %+.3E %.2f" % (time.clock(), ctrl.getSetpoint(), ctrl.getPv(), ctrl.getError(), 1e2*ctrl.getCi(), ctrl.getPidLoopFrequency())) for a in range(50)]; ctrl.setSetpoint(0.85); [print("%.3f %+.3f %+.3f %+.3f %+.3E %.2f" % (time.clock(), ctrl.getSetpoint(), ctrl.getPv(), ctrl.getError(), 1e2*ctrl.getCi(), ctrl.getPidLoopFrequency())) for a in range(100)]; ctrl.setSetpoint(0.35); [print("%.3f %+.3f %+.3f %+.3f %+.3E %.2f" % (time.clock(), ctrl.getSetpoint(), ctrl.getPv(), ctrl.getError(), 1e2*ctrl.getCi(), ctrl.getPidLoopFrequency())) for a in range(100)]; ctrl.setSetpoint(0.7); [print("%.3f %+.3f %+.3f %+.3f %+.3E %.2f" % (time.clock(), ctrl.getSetpoint(), ctrl.getPv(), ctrl.getError(), 1e2*ctrl.getCi(), ctrl.getPidLoopFrequency())) for a in range(100)];
        print("enter    ctrl.terminate()   to halt")
        
    except:
        print ("could not start pid loop")
