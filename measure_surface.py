# -*- coding: utf-8 -*-
"""
Class for performing measurements on and analysis of surfaces
Created on Mon Jun 12 12:08:32 2017

@author: eschenm
"""

import logging, sys, os, time, h5py
import numpy as np

import pyflycap

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
        self.cam.startCapture()
        image = self.cam.createImage()
        time.sleep(0.1)
        image = self.cam.retrieveBuffer(image)
        if pyflycap.fc2PixelFormat(image.pixFormat).name == 'FC2_PIXEL_FORMAT_MONO8':
            dtype=np.uint8
            hdfDtype = dtype
            #hdfDtype = 'i8'
        else:
            dtype=np.uint16
            hdfDtype = dtype
            # hdfDtype = 'i16'
        filename = time.strftime('%Y%m%dT%H%M%S_interferograms.hdf5')
        HDF5_FILE = os.path.join(self.datapath, filename)
        logging.info('Saving image data to %s' % HDF5_FILE)
        print('Saving image data to %s' % HDF5_FILE)
        try:
            f = h5py.File(HDF5_FILE, "w")
            imageStack = f.create_dataset("images",(self.phase_stepping_ini['nrSteps'], self.phase_stepping_ini['nrImages'], self.cam.fm7Settings.height, self.cam.fm7Settings.width,), dtype = hdfDtype)
        except:
            logging.error('could not open hdf5 file %s' % HDF5_FILE)
            raise MeasureSurfaceError('error during creating HDF5 file')
        
        setpoints = []
        pvs = []
        for ii in range(self.phase_stepping_ini['nrSteps']):
            setpoints.append(self.piezo_ini['offset'] + ii*self.phase_stepping_ini['stepSize'])
        for ii in range(self.phase_stepping_ini['nrSteps']):
            self.ctrl.setSetpoint(setpoints[ii])
            time.sleep(0.2)
            pvs.append(self.ctrl.getPv())
            logging.debug('PID setpoint: %.4f current position: %.4f' % (setpoints[ii], pvs[-1]))
            if abs(setpoints[ii] - pvs[-1]) > self.piezo_ini['maxError']:        
                msg = 'current position %f deviates more from setpoint %f than tolerated!' % (pvs[-1], setpoints[ii])
                logging.warning(msg)
                print(msg)
            # record number of images and store in hdf5 file
            for jj in range(self.phase_stepping_ini['nrImages']):
                imageData = self.cam.getImageData(image)
                imageArray = np.fromstring(imageData, dtype)
                imageStack[ii,jj,...] = imageArray.reshape([self.cam.fm7Settings.height, self.cam.fm7Settings.width])
            logging.debug('recorded %d images at step %d' % (jj, ii))         
    
        # set pid controller back to start position
        self.ctrl.setSetpoint(self.piezo_ini['offset'])
    
        # store some housekeeping data
        imageStack.attrs['filename'] = np.string_(filename)
        imageStack.attrs['setpoints'] = setpoints
        imageStack.attrs['pvs'] = pvs
        imageStack.attrs['numSteps'] = ii
        imageStack.attrs['numImages'] = jj
        
        f.flush()
        f.close()
        logging.debug('closed hdf5 file')
        self.cam.stopCapture()
    
