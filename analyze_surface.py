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
# from scipy.ndimage.measurements import center_of_mass

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
                self.wavelength = getattr(hdf5File['images'], 'wavelength', 635E-9)

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
        
        # average multiple images taken at eacht phase step
        self.averagedImages = np.mean(self.images[:,2:3,...],1)
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
        # multiply with -1 to get correct sign (dimples are negative height)
        self.unwrapped_phase = -1*unwrap_phase(wrappedPhase)
        
        # subtrace fitted 2d flat surface (detrend)
        # perform 2d gaussean fit on residual
        # plot crossection of measurement and fit
        # calculate ellipticity
        # look at Tomas's plot
        
        self.height = self.unwrapped_phase/(np.pi*2) * self.wavelength/2 * 1e6
        
    def plotInterferograms(self, interpolation="none"):
        if sys.version_info > (3,):
            filename = self.filename.decode()
        else:
            filename = self.filename
        try:
            sh = self.averagedImages.shape
        except AttributeError:
            msg = 'interferograms not yet averaged! Run analyzeSurface() first!'
            print(msg)
            logging.error(msg)
            return
        fig = plt.figure()
        for ii in range(self.numSteps):
            plt.subplot(2, 4, ii+1)
            ax = plt.gca()
            plotdata = self.averagedImages[ii,...]
            ax.imshow(plotdata, cmap='gray', interpolation=interpolation)
            if hasattr(self, 'roi'):
                rect = patches.Rectangle((roi[1],roi[0]),roi[3],roi[2], \
                                         linewidth=1,edgecolor='r',facecolor='none')
                ax.add_patch(rect)
            title = '#%d' % ii
            if (self.numSteps > self.numStepAnalysis) & (ii+1 > self.numStepAnalysis):
                title = title + ' (unused)'
            plt.title(title)
            # gca().add_patch(patches.Rectangle( (100, 200),300,400,
            #                    fill=False, linestyle='dashed'))
        ax = plt.subplot(248)
        ax.axis('off')
        
        if hasattr(self, 'roi'):
            roitxt = 'ROI(X,Y,W,H): (%d,%d,%d,%d)' % (roi[1],roi[0],roi[3],roi[2])
        else:
            roitxt = 'no ROI defined'
        txt = '%s\n%s\nusing %d images' % (str(filename), roitxt, self.numStepAnalysis)

        ax.text(0.05,0.5, txt, fontsize=11)
        plt.show()
        return plt.gcf()

    def _plotData(self, data, title='', interpolation="none"):
        if sys.version_info > (3,):
            filename = self.filename.decode()
        else:
            filename = self.filename
        if not title:
            title = str(filename)
        plot = plt.figure()
        shape = np.shape(data)

        extentX = self.scale*1e6 * np.array((0., shape[1]))
        extentX -= np.mean(extentX)
        extentY = self.scale*1e6 * np.array((0., shape[0]))
        extentY -= np.mean(extentY)
        extent = list(extentY)
        extent.append(extentX[0])
        extent.append(extentX[1])
        plt.imshow(data, interpolation=interpolation, extent=extent, aspect='auto')
        plt.xlabel('position (µm)')
        plt.ylabel('position (µm)')
        plt.colorbar()
        plt.title(title)
        plt.show()
        return plot
        
    def plotContrast(self):
        contrastData = self.contrast
        contrastData[contrastData > 1] = 1
        self._plotData(contrastData, title='fringe contrast')
        
    def plotPhase(self):
        return self._plotData(self.wrappedPhase, title='wrapped phase (rad)')
        
    def plotUnwrappedPhase(self):
        return self._plotData(self.unwrapped_phase, title='unwrapped phase (rad)')
    
    def plotHeight(self):
        return self._plotData(self.height, title='height (µm)')

    def fitGauss(self, data = []):
        if not data:
            data = self.height
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
        #   center of mass:
        # (yo, xo) = center_of_mass(data)
        minpos = np.where(data == np.min(data))
        (yo, xo) = (minpos[0][0], minpos[1][0])
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

        sigma_x = 40  # hardcoded, needs better quick estimation
        sigma_y = 40
        
        initial_guess = (amplitude, xo, yo, sigma_x, sigma_y, theta, offset, xtilt, ytilt)
        ig = initial_guess
        shape = data.shape
        txt = 'initial_guess: amplitude: %.3fµm\n\t\t(x0, y0): (%.1f, %.1f) µm\n\t\t(sigma_x, sigma_y): (%.2f, %.2f) µm\n\t\ttheta: %.3f (deg)\n\t\toffset: %.3f µm\n\t\t(xtilt, ytilt): (%.4f, %.4f) (µm/image length)'
        x0 = self.scale*1e6 * (ig[1] - shape[1]/2)
        y0 = self.scale*1e6 * (ig[2] - shape[0]/2)
        sigma_x = ig[3]*1E6*self.scale
        sigma_y = ig[4]*1E6*self.scale
        theta_deg = ig[5]/np.pi*180

        vals = (ig[0], x0, y0, sigma_x, sigma_y, theta_deg, ig[6], ig[7], ig[8])
        # print(txt % vals)
        initial_guessSurf = twoD_GaussianWithTilt((x, y), *initial_guess).reshape(shape)
        popt, pcov = opt.curve_fit(twoD_GaussianWithTilt, (x, y), data.ravel(), p0=initial_guess)
        data_fitted = twoD_GaussianWithTilt((x, y), *popt).reshape(shape)
        self.data_fitted = data_fitted
        self.popt = popt
        
        txt = 'found fit params: amplitude: %.3fµm\n\t\t(x0, y0): (%.1f, %.1f) µm\n\t\t(sigma_x, sigma_y): (%.2f, %.2f) µm\n\t\ttheta: %.3f (deg)\n\t\toffset: %.3f µm\n\t\t(xtilt, ytilt): (%.4f, %.4f) (µm/image length)'
        x0 = self.scale*1e6 * (popt[1] - shape[1]/2)
        y0 = self.scale*1e6 * (popt[2] - shape[0]/2)
        sigma_x = popt[3]*1E6*self.scale
        sigma_y = popt[4]*1E6*self.scale
        theta_deg = popt[5]/np.pi*180
        vals = (popt[0], x0, y0, sigma_x, sigma_y, theta_deg, popt[6], popt[7], popt[8])
        
        print(txt % vals)
        self.dimpleDepth = popt[0]
        self.sigma = (popt[3]*self.scale*1E6, popt[4]*self.scale*1E6)
        
        if 1:
            img = self._plotData(detrended_data, title='tilt removed from data (µm)')
            img = self._plotData(initial_guessSurf, title='initial guessed parameters')
            title = 'fitted Gauss (with tilt) (µm)\ndepth: %.2fµm, sigma: (%.3f HOR and %.3f VER)µm' % (popt[0], self.sigma[0], self.sigma[1])
            img = self._plotData(data_fitted, title=title)
            img = self._plotData(data-data_fitted, title='fit residual  (µm)')
        
        roc_x = self._roc(popt[3]*1E6*self.scale, self.popt[0])
        roc_y = self._roc(popt[4]*1E6*self.scale, self.popt[0])
        self.radiiOfCurvature = (roc_x, roc_y)
        print('calculated radii of curvature: %.3f and %.3f µm' % self.radiiOfCurvature)

    def fitSine(self, roi):
        '''roi in (X, Y, W, H)
        returns amplitude and phase'''
        
        data = self.averagedImages[:,roi[1]:roi[1]+roi[3],roi[0]:roi[0]+roi[2]]
        x = np.array(range(0,self.numStepAnalysis))*np.pi/2
        y = np.mean(np.mean(data, axis=2), axis=1)
        # val = amplitude * np.sin(x/period-phase) + offset

        # initial guess
        amplitude= (np.max(y)-np.min(y))/2
        offset = np.max(y)-amplitude
        # we already have a good estimate of the phase in self.wrappedPhase
        phase = np.mean(self.wrappedPhase[roi[1]:roi[1]+roi[3],roi[0]:roi[0]+roi[2]])
        period = 4
        initial_guess = (amplitude, phase, offset,  period)
        popt, pcov = opt.curve_fit(self._sin, x, y,  p0=initial_guess)
        print('amplitude: %.3f phase: %.3f offset: %.3f period: %.3f' % (popt[0],  popt[1],  popt[2],  popt[3]))        
        print('phase from map: %.3f' % phase)
        
    def _sin(self, x, amplitude, phase, offset,  period):
        '''returns sine for given x, amplitude, phase, offset and period. x and phase in radians'''
        val = amplitude * np.sin(x/period-phase) + offset
        return val
        
    def _roc(self, sigma, depth):
        D = 2*np.sqrt(2) * sigma
        radius_curvature = D**2 / (8*depth)
        #with D = full width at height of 1/e
        return radius_curvature
    
if __name__ == '__main__':
    if 1:
        filename = '/home/martin/code/20170623T145259_interferograms.hdf5'
        # filename = 'C:\\eschenm\\03_projects\\31_Qutech\\FDMS\\data\\20170623\\20170623T145259_interferograms.hdf5'
        roi = (800, 310, 210, 380)
        useNrOfSteps = 7
    elif 0:
        filename  = 'C:\\eschenm\\03_projects\\31_Qutech\\FDMS\\data\\20170620\\20170620T101715_interferograms.hdf5'
        useNrOfSteps = 5
    image = fdmsImage(filename)
    image.analyzeSurface(useNrOfSteps=useNrOfSteps, roi=roi)
    image.plotInterferograms()
    
    image.plotHeight()
    #image.fitGauss()
    image.fitSine((546,  949,  10,  5))
    
    # Hint from Pep for interrupting and starting ipython console during execution:
    if 0:
        from IPython import embed
        embed()

    '''
    Phase determination source: Wyant_Phase-Shifting-Interferometry.pdf
    
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
