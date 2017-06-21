# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 20:20:37 2017

@author: eschenm
"""

import os, sys, h5py, logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import scipy.optimize as opt
from skimage.restoration import unwrap_phase
from twoD_Gaussian import twoD_GaussianWithTilt
from scipy.ndimage.measurements import center_of_mass

analysis_wavelenth = 635E-9

class fdmsImage():
    def __init__(self, filename):
        '''
        Opens and reads hdf5 file stored by FDMS control software

        image = fdmsImage(pathToHdf5File)
        image.analyzeSurface(roi=(410,390, 400, 400))
        
        image.plotInterferograms()
        image.plotContrast()
        image.plotPhase()
        image.plotUnwrappedPhase()
        image.plotHeight()
        '''
        
        logging.debug('start analysis of file %s' % filename)
        if os.path.isfile(filename):
            filepath = os.path.realpath(filename)
        else:
            logging.error('file %s not found for analysis' % filepath)
            raise Exception('file %s not found for analysis' % filepath)
        logging.info('reading file %s'  % filepath)
        
        try:
            with h5py.File(filepath,  "r") as hdf5File:
                self.filename = os.path.split(filepath)[1]
                self.filename = filepath
                
                logging.debug('file opened for reading')
                # read contents of hdf5 file
                
                self.images = hdf5File['images'][:,:,:,:]
                self.timestamps = hdf5File['timestamps'][:,:]
                self.setpoints  = hdf5File['images'].attrs['setpoints']
                self.pvs        = hdf5File['images'].attrs['pvs']
                self.numImages  = hdf5File['images'].attrs['numImages']
                self.numSteps   = hdf5File['images'].attrs['numSteps']
                self.filename   = hdf5File['images'].attrs['filename']
        except Exception as error:
            logging.error('error during reading file %s: %s' % (filepath, error))
            raise Exception(error)


    def analyzeSurface(self, useNrOfSteps=None, roi=None, scale=0.1172E-6):
        ''' 
        Calculates height profile from stored surface interferogram.
        useNrOfSteps=N  specify if only the first N images are to be used for 
                        analysis
        roi=(T,L,H,W)   specify ROI as (left, top, width, height) Default is 
                        whole image
        scale=F         dimension of image pixel in the fiber plane. Default is 
                        117 nm with the Mitutoyo 50X and 200 mm tube lens and 
                        5.86 µm detector pixels
        '''
        
        if useNrOfSteps:
            self.numStepAnalysis = useNrOfSteps
        else:
            self.numStepAnalysis = self.numSteps

        if self.numStepAnalysis > self.numSteps:
            self.numStepAnalysis = self.numSteps
            msg = 'stored file only contains %d interferograms!' % self.numSteps
            logging.warning(msg)
            print(msg)
        if roi:
            self.roi = roi
            # simple checks for input sanity
            msg = ''
            if roi[0] < 0 | roi[2] < 0:
                msg = 'invalid ROI settings, negative position is illegal!'
            if roi[0] + roi[2] > np.shape(self.images)[2]:
                msg = 'ROI (horizontal offset + width) exceeds image width'
            if roi[1] + roi[3] > np.shape(self.images)[2]:
                msg = 'ROI (vertical offset + height) exceeds image height'
            if msg:
                logging.error(msg)
                raise Exception(msg)
        self.scale = scale
        
        # average multiple images
        self.averagedImages = np.mean(self.images[:,0:1,...],1)  # werkt
        img = self.averagedImages
        if self.numStepAnalysis == 5:
            # phase
            nom = (-2*img[1,...] + 2*img[3,...])
            denom = (img[0,...] - 2*img[2,...] + img[4,...])
            self.wrappedPhase = np.arctan2(nom, denom)
    
            # contrast
            term1 = np.power((img[1,...] - img[3,...]), 2)
            term2 = np.power((img[0,...] -2*img[2,...] + img[4,...]), 2)
            nom = 2*np.power(4*term1 + term2, 0.5)
            denom = (img[0,...] + 2*(img[1,...] + img[2,...] + img[3,...]) + img[4,...])
            self.contrast =  nom / denom
        
        if self.numStepAnalysis == 6:
            # phase
            nom = (-3*img[1,...] + 4*img[3,...] -img[5,...])
            denom =  (img[0,...] -4*img[2,...] + 3*img[4,...])
            self.wrappedPhase = np.arctan2(nom, denom)
    
            # contrast (based on first 5 images)
            term1 = np.power((img[1,...] - img[3,...]), 2)
            term2 = np.power((img[0,...] -2*img[2,...] + img[4,...]), 2)
            nom = 2*np.power(4*term1 + term2, 0.5)
            denom = (img[0,...] + 2*(img[1,...] + img[2,...] + img[3,...]) + img[4,...])
            self.contrast =  nom / denom
    
        if self.numStepAnalysis == 7:
            nom = 4*(img[1,...] - 2*img[3,...] + img[5,...])
            denom = (-img[0,...] + 7*img[2,...] - 7*img[4,...] + img[6,...])
            self.wrappedPhase = np.arctan2(nom, denom)
     
            # contrast (based on first 5 images)
            term1 = np.power((img[1,...] - img[3,...]), 2)
            term2 = np.power((img[0,...] -2*img[2,...] + img[4,...]), 2)
            nom = 2*np.power(4*term1 + term2, 0.5)
            denom = (img[0,...] + 2*(img[1,...] + img[2,...] + img[3,...]) + img[4,...])
            self.contrast =  nom / denom

        if roi:
            wrappedPhase = self.wrappedPhase[roi[0]:roi[0]+roi[2], roi[1]:roi[1]+roi[3]]
        else:
            wrappedPhase = self.wrappedPhase
        
        # the unwrap_phase function unwraps phase between -pi and pi
        self.unwrapped_phase = unwrap_phase(wrappedPhase)
        
        # subtrace fitted 2d flat surface (detrend)
        # perform 2d gaussean fit on residual
        # plot crossection of measurement and fit
        # calculate ellipticity
        # look at Tomas's plot
        
        self.height = self.unwrapped_phase/(np.pi*2) * analysis_wavelenth/2 * 1e6
        # correct for sign
        self.height = -1 * self.height

    def plotInterferograms(self, interpolation="none"):
        if sys.version_info > (3,):
            filename = self.filename.decode()
        else:
            filename = self.filename
        plt.figure()
        for ii in range(self.numSteps):
            plt.subplot(2,4, ii+1)
            plt.imshow(self.averagedImages[ii,...], cmap='gray', interpolation=interpolation)
#            gca().add_patch(patches.Rectangle( (100, 200),300,400,
#                                fill=False, linestyle='dashed'))
        plt.subplot(2, 4, 2)
        plt.title(filename)
        if self.numSteps > self.numStepAnalysis:
            for ii in range(self.numStepAnalysis, self.numSteps):
                plt.subplot(2, 4, ii+1)
                plt.title('unused')

    def _plotData(self, data, label, interpolation="none"):
        if sys.version_info > (3,):
            filename = self.filename.decode()
        else:
            filename = self.filename
        plt.figure()
        shape = np.shape(data)
        extentX = self.scale*1e6 * np.array((0., shape[1]))
        extentX -= np.mean(extentX)
        extentY = self.scale*1e6 * np.array((0., shape[0]))
        extentY -= np.mean(extentY)
        extent = list(extentY)
        extent.append(extentX[0])
        extent.append(extentX[1])
        img = plt.imshow(data, interpolation=interpolation, extent=extent)
        plt.xlabel('position (µm)')
        plt.ylabel('position (µm)')
        
        plt.colorbar()
        plt.title('%s - %s' % (label, str(filename)))
        return img
        
    def plotContrast(self):
        contrastData = self.contrast
        contrastData[contrastData > 1] = 1
        self._plotData(contrastData, 'fringe contrast')
        
    def plotPhase(self):
        self._plotData(self.wrappedPhase, 'wrapped phase (rad)')
        
    def plotUnwrappedPhase(self):
        self._plotData(self.unwrapped_phase, 'unwrapped phase (rad)')
    
    def plotHeight(self):
        return self._plotData(self.height, 'height (µm)')

    def fitGauss(self, data):
        shape = np.shape(data)
        x = np.linspace(0, shape[1], shape[1])
        y = np.linspace(0, shape[0], shape[0])
        x, y = np.meshgrid(x, y)
        
        # calculate initial estimages
        # size of square for which corner intensities are averaged            
        bs = int(shape[0]/10)
        
        # intensities at corners: [BL, BR, UL, UR]
        corners = [np.mean(data[:bs,:bs]), np.mean(data[:bs,-bs:]), np.mean(data[-bs:,:bs]), np.mean(data[-bs:,-bs:])]
        offset = np.mean(corners)
        amplitude = np.min(data)-offset
        theta = 0
        # center of mass:
        (yo, xo) = center_of_mass(-1*data)        
        xtilt = (corners[1] - corners[0])/shape[1]/0.9
        ytilt = (corners[2] - corners[0])/shape[0]/0.9
        
        detrend_params = (0, xo, yo, 60, 60, theta, offset, xtilt, ytilt)
        trend = twoD_GaussianWithTilt((x,y), *detrend_params).reshape(shape)
        # perform rough detrend so sigma can be estimated
        detrended_data = data - trend
        # fix with accurate integrals from Bastiaan
        # See https://en.wikipedia.org/wiki/Beam_diameter
        
        x_sum = np.cumsum(np.mean(detrended_data-np.min(detrended_data), axis=1))
        y_sum = np.cumsum(np.mean(detrended_data-np.min(detrended_data), axis=0))
        x_sum /= x_sum
        y_sum /= y_sum

        sigma_x = 40
        sigma_y = 40
        
        initial_guess = (amplitude, xo, yo, sigma_x, sigma_y, theta, offset, xtilt, ytilt)
        initial_guessData = twoD_GaussianWithTilt((x, y), *initial_guess).reshape(shape)
        
        plt.figure()
        img = plt.imshow(detrended_data, interpolation="none")
        plt.colorbar()
        plt.title('tilt removed from data (µm)')
        
        plt.figure()
        img = plt.imshow(initial_guessData, interpolation="none")
        plt.colorbar()
        plt.title('initial guesses parameters')

        popt, pcov = opt.curve_fit(twoD_GaussianWithTilt, (x, y), data.ravel(), p0=initial_guess)
        data_fitted = twoD_GaussianWithTilt((x, y), *popt).reshape(shape)

        plt.figure()
        img = plt.imshow(data_fitted, interpolation="none")
        plt.colorbar()
        plt.title('fit residual (µm)')
        
        plt.figure()
        img = plt.imshow(data-data_fitted, interpolation="none")
        plt.colorbar()
        plt.title('(data - fit)  (µm)')
        
        self.data_fitted = data_fitted
        self.popt = popt

        #print('found fit params: (amplitude: %3f\n\t\t(xo, yo): (%.1f, %.1f)\n\t\t(sigma_x, sigma_y): (%.2f, %.2f)\n\t\ttheta (rad): %.3f\n\t\toffset: %.3f\n\t\t(xtilt, ytilt): (%.4f, %.4f)' % popt)
        
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
        phase_6 = atan((-3*img[1] + 4*img[3] -img[5]) / (img[0] -4*img[2] + 3*img[4]))
        phase for seven phase steps:
        phase_7 = atan((4*(img[1] - 2*img[3] + img[5])) / (-img[0] + 7*img[2] - 7*img[4] + img[6]))
        '''

        
        
if __name__ == '__main__':
    data = 'C:\\eschenm\\03_projects\\31_Qutech\\FDMS\\data\\20170620\\20170620T101715_interferograms.hdf5'
    image = fdmsImage(data)
    image.analyzeSurface()
    image.plotContrast()
    
    # Hint from Pep for interrupting and starting ipython console during execution:
    #from IPython import embed
    #embed()
