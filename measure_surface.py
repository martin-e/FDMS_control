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
            time.sleep(0.08)
            pvs.append(self.ctrl.getPv())
            logging.debug('PID setpoint: %.4f current position: %.4f' % (setpoints[ii], pvs[-1]))
            if (setpoints[ii] - pvs[-1]) > self.piezo_ini['maxError']:        
                logging.warning('current position deviates more from setpoint than tolerated!')
                print('current position deviates more from setpoint than tolerated!')
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
    
    def analyzeSurfaceProfile(self, filename):
        logging.info('starting analysis of file %s'  % os.path.split(filename)[1])
        if not os.path.exist(filename):
            logging.error('file %s not found for analysis' % filename)
            raise MeasureSurfaceError('file %s not found for analysis' % filename)
        try:
            f=open(filename)
        except:
            logging.error('could not open file %s' % filename)
            raise MeasureSurfaceError('could not open file %s' % filename)

        f.close()

        '''
        source: Wyant_Phase-Shifting-Interferometry.pdf
        
        phase for four phase steps:
        phase_4 = atan((-img[1] + img[3]) / (img[0] - img[2]))
        contrast_4 = sqrt(2)*(((img[0] - img[2])**2) + (img[1] - img[3])**2) / (img[0] + img[1] + img[2] + img[3])
        phase for five phase steps:
        phase_5 = atan(7*(img[1] - img[3]) / (-4*img[0] + img[1] + 6*img[2] + img[3] - 4*img[4])
        contrast_5 = sqrt(49*(img[1] - imgimg[3])**2 + (-4*img[0] + img[1] + 6*img[2] + img[3] -4*img[4])**2) / (2*img[0] + 3*img[1] + 4*img[2] + 3*img[3] + 2*img[4])
        phase for five phase steps:
        phase_5 = atan(7*(img[1] - img[3]) / (-4*img[0] + img[1] + 6*img[2] + img[3] - 4*img[4])
        contrast_5 = sqrt(49*(img[1] - img[3])**2 + (-4*img[0] + img[1] + 6*img[2] + img[3] -4*img[4])**2) / (2*img[0] + 3*img[1] + 4*img[2] + 3*img[3] + 2*img[4])
        Schwider-Hariharan for five steps:
        phase_5_SH = atan(-(2*(img[1] - img[2])) / (img[0] - 2*img]2] + img[4]))
        contrast_5_SH = 2*sqrt(4*(img[1] - img[3])**2 + (img[0] -2*img[2] + img[4])**2) / (img[0] + 2*(img[1] + img[2] + img[3]) + img[4])
        phase for six phase steps:
        phase_6 = atan(img[] img[] img[] img[] img[] img[] )
        phase for seven phase steps:
        phase_7 = atan((4*(img[1] - 2*img[3] + img[5])) / (-img[0] + 7*img[2] - 7*img[4] + img[6]))

        '''