
# -*- coding: utf-8 -*-
"""
Class for performing measurements on and analysis of surfaces
Created on Mon Jun 12 12:08:32 2017

@author: eschenm
"""

import logging
import sys
import os
import time
import h5py
import numpy as np


class MeasureSurfaceError(Exception):
    pass


class Phase_stepping():
    def __init__(self, piezo_ini, phase_stepping_ini, cam, ctrl, datapath):
        self.piezo_ini = piezo_ini
        self.phase_stepping_ini = phase_stepping_ini
        self.cam = cam
        self.ctrl = ctrl
        self.datapath = datapath

    def recordSurface(self):
        (image, meta) = self.cam.get_image()
        meta = self.cam.decode_meta_data(meta)
        pixformat = self.cam._ini['nrBits']
        if pixformat == 8:
            dtype = np.uint8
        elif pixformat == 16:
            dtype = np.uint16
        else:
            msg = 'unsupported number of bits: %d' % pixformat
            logging.error(msg)
            raise MeasureSurfaceError(msg)
        hdfDtype = dtype

        filename = time.strftime('%Y%m%dT%H%M%S_interferograms.hdf5')
        HDF5_FILE = os.path.join(self.datapath, filename)
        logging.info('Saving image data to %s' % HDF5_FILE)
        print('Saving image data to %s' % HDF5_FILE)
        try:
            f = h5py.File(HDF5_FILE, "w")
            imageStack = f.create_dataset("images",
                (self.phase_stepping_ini['nrSteps'], self.phase_stepping_ini['nrImages'], meta['height'], meta['width']), 
                dtype=hdfDtype, 
                compression='gzip', 
                compression_opts=9)
            timeStampStack = f.create_dataset("timestamps",
                (self.phase_stepping_ini['nrSteps'], self.phase_stepping_ini['nrImages']), 
                dtype=np.float64)
        except:
            logging.error('could not open hdf5 file %s' % HDF5_FILE)
            raise MeasureSurfaceError('error during creating HDF5 file')
        
        setpoints = []
        pvs = []
        for ii in range(self.phase_stepping_ini['nrSteps']):
            setpoints.append(self.piezo_ini['offset'] + ii*self.phase_stepping_ini['stepSize'])
        for ii in range(self.phase_stepping_ini['nrSteps']):
            self.ctrl.setSetpoint(setpoints[ii])
            logging.debug('go to setpoint %.3f' % setpoints[ii])
            time.sleep(0.15)
            self.waitForPosition(timeout=1)
            pvs.append(self.ctrl.getPv())
            logging.info('PID setpoint: %.4f current position: %.4f' % (setpoints[ii], pvs[-1]))
            if abs(setpoints[ii] - pvs[-1]) > self.piezo_ini['maxError']:        
                msg = 'current position %f deviates more from setpoint %f than tolerated!' % (pvs[-1], setpoints[ii])
                logging.warning(msg)
                print(msg)
                time.sleep(1)
                pvs.pop()
                pvs.append(self.ctrl.getPv())
                msg = 'after additional 1 second wait time: PID setpoint: %.4f current position: %.4f' % (setpoints[ii], pvs[-1])
                logging.info(msg)
                print(msg)
            # record number of images and store in hdf5 file
            print('step {}/{} - recording {} images: '.format(ii+1, self.phase_stepping_ini['nrSteps'], self.phase_stepping_ini['nrImages']), end = '')
            for jj in range(self.phase_stepping_ini['nrImages']):
                (image, meta_data) = self.cam.get_image()
                meta = self.cam.decode_meta_data(meta_data)
                imageStack[ii,jj,...] = image
                timeStampStack[ii,jj] = meta['timestamp']
                print('{}'.format(jj+1), end=' ')
            print('\n')
            logging.info('recorded %d images at step %d' % (jj+1, ii+1))         
    
        # set pid controller back to start position
        self.ctrl.setSetpoint(self.piezo_ini['offset'])
    
        # store some housekeeping data
        imageStack.attrs['filename'] = np.string_(filename)
        imageStack.attrs['setpoints'] = setpoints
        imageStack.attrs['pvs'] = pvs
        imageStack.attrs['numSteps'] = ii+1
        imageStack.attrs['numImages'] = jj+1
        imageStack.attrs['wavelength'] = self.phase_stepping_ini['wavelength']
        
        f.flush()
        f.close()
        logging.debug('closed hdf5 file')
        return HDF5_FILE
    
    def waitForPosition(self, timeout=2):
        start = time.time()
        to = True
        while time.time() < (start + timeout):
            if self.ctrl.getError() > self.piezo_ini['maxError']:
                time.sleep(0.020)
            else:
                to = False
                break
        if to:
            msg = 'timeout while waiting for PID controller to reach position'
            print(msg)
            logging.warning(msg)
            