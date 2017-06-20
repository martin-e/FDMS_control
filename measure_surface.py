# -*- coding: utf-8 -*-
"""
Class for performing measurements on and analysis of surfaces
Created on Mon Jun 12 12:08:32 2017

@author: eschenm
"""

import logging, sys, os, time, h5py
import numpy as np
import PyCapture2

if sys.version_info > (3,):
    class MeasureSurfaceError(Exception):
        pass
else:
    class MeasureSurfaceError(StandardError):
        pass

class Phase_stepping():
    def __init__(self, piezo_ini, phase_stepping_ini, cam, ctrl, datapath):
        self.piezo_ini = piezo_ini
        self.phase_stepping_ini = phase_stepping_ini
        self.cam = cam
        self.ctrl = ctrl
        self.datapath = datapath

    def recordSurface(self):
        try:
            self.cam.startCapture()
        except PyCapture2.Fc2error as err:
            if sys.version_info > (3,):
                msg = 'Error from camera: %s' % err.decode()
            else:
                msg = 'Error from camera: %s' % err
            logging.warning(msg)
            print(msg)
        time.sleep(0.1)
        image = self.cam.retrieveBuffer()
        pixformat = image.getPixelFormat()
        if pixformat == PyCapture2.PIXEL_FORMAT.MONO8:
            dtype=np.uint8
            hdfDtype = dtype
        elif pixformat == PyCapture2.PIXEL_FORMAT.MONO16:
            dtype=np.uint16
            hdfDtype = dtype
        else:
            for format in dir(PyCapture2.PIXEL_FORMAT):
                if getattr(PyCapture2.PIXEL_FORMAT, format) == pixformat:
                    break
            msg = 'unsupported image format: %s' % format
            logging.error(msg)
            raise MeasureSurfaceError(msg)

        filename = time.strftime('%Y%m%dT%H%M%S_interferograms.hdf5')
        HDF5_FILE = os.path.join(self.datapath, filename)
        logging.info('Saving image data to %s' % HDF5_FILE)
        print('Saving image data to %s' % HDF5_FILE)
        try:
            f = h5py.File(HDF5_FILE, "w")
            imageStack = f.create_dataset("images",(self.phase_stepping_ini['nrSteps'], self.phase_stepping_ini['nrImages'], image.getRows(), image.getCols()), dtype = hdfDtype)
            timeStampStack = f.create_dataset("timestamps",(self.phase_stepping_ini['nrSteps'], self.phase_stepping_ini['nrImages']), dtype = np.float64)
        except:
            logging.error('could not open hdf5 file %s' % HDF5_FILE)
            raise MeasureSurfaceError('error during creating HDF5 file')
        
        setpoints = []
        pvs = []
        for ii in range(self.phase_stepping_ini['nrSteps']):
            setpoints.append(self.piezo_ini['offset'] + ii*self.phase_stepping_ini['stepSize'])
        for ii in range(self.phase_stepping_ini['nrSteps']):
            self.ctrl.setSetpoint(setpoints[ii])
            time.sleep(0.25)
            self.waitForPosition(0.5)
            pvs.append(self.ctrl.getPv())
            logging.debug('PID setpoint: %.4f current position: %.4f' % (setpoints[ii], pvs[-1]))
            if abs(setpoints[ii] - pvs[-1]) > self.piezo_ini['maxError']:        
                msg = 'current position %f deviates more from setpoint %f than tolerated!' % (pvs[-1], setpoints[ii])
                logging.warning(msg)
                print(msg)
            # record number of images and store in hdf5 file
            for jj in range(self.phase_stepping_ini['nrImages']):
                image = self.cam.retrieveBuffer()
                data = self.cam.getImageData(image)
                imageArray = np.fromstring(data, dtype)
                imageStack[ii,jj,...] = imageArray.reshape([self.cam.fm7Settings.height, self.cam.fm7Settings.width])
                timeStampStack[ii,jj] = self.cam.getImageTimestamp(image)
            logging.debug('recorded %d images at step %d' % (jj+1, ii+1))         
    
        # set pid controller back to start position
        self.ctrl.setSetpoint(self.piezo_ini['offset'])
    
        # store some housekeeping data
        imageStack.attrs['filename'] = np.string_(filename)
        imageStack.attrs['setpoints'] = setpoints
        imageStack.attrs['pvs'] = pvs
        imageStack.attrs['numSteps'] = ii+1
        imageStack.attrs['numImages'] = jj+1
        
        f.flush()
        f.close()
        logging.debug('closed hdf5 file')
        self.cam.stopCapture()
    
    def waitForPosition(self, timeout=10):
        start = time.time()
        timeout = True
        while time.time() < (start + timeout):
            if self.ctrl.getError() > self.piezo_ini['maxError']:
                time.sleep(0.020)
            else:
                timeout = False
                break
        if timeout:
            msg = 'timeout while waiting for PID controller to reach position'
            print(msg)
            logging.warning(msg)
            