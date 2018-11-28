# -*- coding: utf-8 -*-
"""
@author: eschenm
"""

import os
import sys
import time
import h5py
import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import scipy.optimize as opt
from skimage.restoration import unwrap_phase
from twoD_Gaussian import twoD_GaussianWithTilt
from d4s import get_d4sigma
# from scipy.ndimage.measurements import center_of_mass

class fdmsImage():
    def __init__(self, filename):
        '''
        Opens and reads hdf5 file stored by FDMS control software

        image = fdmsImage(pathToHdf5File)
        image.analyzeSurface(roi=(410,390, 400, 400), \
            useNrOfSteps=5)
        
        image.plotInterferograms()
        image.plotContrast()
        image.plotPhase()
        image.plotUnwrappedPhase()
        image.plotHeight()
		image.fitGauss()
        '''
        
        msg = ('read contents of file %s' % filename)
        print(msg)
        logging.info(msg)
        if os.path.isfile(filename):
            filepath = os.path.realpath(filename)
        else:
            logging.error('could not find file %s' % filename)
            raise Exception('could not find file %s' % filename)

        
        try:
            with h5py.File(filepath,  "r") as hdf5File:
                logging.debug('file opened for reading')
                # read contents of hdf5 file
                
                self.images = hdf5File['images'][:,:,:,:]
                self.timestamps = hdf5File['timestamps'][:,:]
                self.setpoints  = hdf5File['images'].attrs['setpoints']
                self.pvs        = hdf5File['images'].attrs['pvs']
                self.numImages  = hdf5File['images'].attrs['numImages']
                self.numSteps   = hdf5File['images'].attrs['numSteps']
                self.filename   = hdf5File['images'].attrs['filename'].decode()
                self.filepath   = os.path.split(filepath)[0]
                self.wavelength = getattr(hdf5File['images'], 'wavelength', 635E-9)
        except Exception as error:
            logging.error('error during reading file %s: %s' % (filepath, error))
            raise Exception(error)
        logging.debug('done reading file %s'  % filepath)
        
    def analyzeSurface(self, useNrOfSteps=None, roi=None, scale=0.1172E-6):
        ''' 
        Calculates height profile from stored surface interferogram.
        useNrOfSteps=N  specify if only the first N images are to be used for 
                        analysis
        roi=(T,L,H,W)   specify ROI as (top, left, height, width) Default is 
                        whole image
        scale=F         dimension of image pixel in the fiber plane. Default is 
                        117 nm with the Mitutoyo 50X and 200 mm tube lens and 
                        5.86 um detector pixels
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
        logging.info('analyzing with %d number of steps. (stored in hdf5 file: %d)' % (self.numStepAnalysis, self.numSteps))

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
            logging.info('analyzing with roi: (%d, %d, %d, %d) (T,L,H,W)' % tuple(roi))
        self.scale = scale
        
        # average multiple images taken at eacht phase step
        self.averagedImages = np.mean(self.images[:,0:3,...],1)
        img = self.averagedImages
        if self.numStepAnalysis == 5:
            # phase according to Schwider-Hariharan Algorithm
            nom = (-2*img[1,...] + 2*img[3,...])
            denom = (img[0,...] - 2*img[2,...] + img[4,...])
            self.wrappedPhase = np.arctan2(nom, denom)
    
            # contrast according to Schwider-Hariharan Algorithm
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
    
            # contrast (based on first 5 images, Schwider-Hariharan Algorithm)
            term1 = np.power((img[1,...] - img[3,...]), 2)
            term2 = np.power((img[0,...] -2*img[2,...] + img[4,...]), 2)
            nom = 2*np.power(4*term1 + term2, 0.5)
            denom = (img[0,...] + 2*(img[1,...] + img[2,...] + img[3,...]) + img[4,...])
            self.contrast =  nom / denom
    
        if self.numStepAnalysis == 7:
            # phase
            nom = 4*(img[1,...] - 2*img[3,...] + img[5,...])
            denom = (-img[0,...] + 7*img[2,...] - 7*img[4,...] + img[6,...])
            self.wrappedPhase = np.arctan2(nom, denom)
     
            # contrast (based on first 5 images, Schwider-Hariharan Algorithm)
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
        
        self.height = self.unwrapped_phase/(np.pi*2) * self.wavelength/2 * 1e6 * -1
        self.height -= self.height[0, 0]
        
        logging.info('calculating contrast, phase and phase unwrapping done')

    def plotInterferograms(self, interpolation="none"):
        filename = self.filename
        try:
            sh = self.averagedImages.shape
        except AttributeError:
            msg = 'interferograms not yet averaged! Run analyzeSurface() first!'
            print(msg)
            logging.error(msg)
            return
        fig = plt.figure()
        if self.numSteps == 5:
            layout = (2, 3)
        else:
            layout = (2, 4)
        for ii in range(self.numSteps):
            plt.subplot(*layout, ii+1)
            ax = plt.gca()
            plotdata = self.averagedImages[ii,...]
            ax.imshow(plotdata, cmap='gray', interpolation=interpolation)
            if hasattr(self, 'roi'):
                roi = self.roi
                rect = patches.Rectangle((roi[1],roi[0]),roi[3],roi[2], \
                                         linewidth=1,edgecolor='r',facecolor='none')
                ax.add_patch(rect)
            title = '#%d' % ii
            if (self.numSteps > self.numStepAnalysis) & (ii+1 > self.numStepAnalysis):
                title = title + ' (unused)'
            plt.title(title)
            # gca().add_patch(patches.Rectangle( (100, 200),300,400,
            #                    fill=False, linestyle='dashed'))
        if self.numSteps == 5:
            ax = plt.subplot(236)
        else:
            ax = plt.subplot(248)
        ax.axis('off')
        
        if hasattr(self, 'roi'):
            roitxt = 'ROI(T,L,H,W): (%d,%d,%d,%d)' % (roi[0],roi[1],roi[2],roi[3])
        else:
            roitxt = 'no ROI defined'
        txt = '%s\n%s\nusing %d images' % (str(filename), roitxt, self.numStepAnalysis)

        ax.text(0.05,0.5, txt, fontsize=11)
        plt.show(block=False)
        return plt.gcf()

    def plotPhaseStepper(self, ):
        try:
            roi = self.roi
        except AttributeError:
            error('no roi specified, run analyzeSurface')
        img = self.averagedImages
        nom = (img[4,...] - img[0,...])
        denom =  2*(img[3,...] - img[1,...])
        phaseStep = np.arccos(nom/denom)[roi[0]:roi[0]+roi[2], roi[1]:roi[1]+roi[3]]
        self._plotData(phaseStep/np.pi*180, title='average phase step (deg)')
        plt.show(block=False)
        idx = np.logical_not(np.isnan(phaseStep))
        phaseMean = np.mean(phaseStep[idx].reshape(-1))/np.pi*180
        phaseStd = np.std(phaseStep[idx].reshape(-1))/np.pi*180
        print('Phase step calibration info:\n\tmean phase step value: %.3f deg\n\tstandard deviation: %.2f deg' % (phaseMean, phaseStd))
        fig = plt.figure()
        plt.hist(phaseStep[idx].reshape(-1)/np.pi*180, 100)
        plt.xlabel('phase step (deg)')
        plt.ylabel('nr. (-)')
        plt.title('phase step mean: %.3f deg std:  %.3f deg' % (phaseMean, phaseStd))
        plt.show(block=False)

    def plotAllInterferograms(self, interpolation="none"):
        filename = self.filename
        (nrSteps, nrImages, rows, cols) = np.shape(self.images)

        for ii in range(nrSteps):
            for jj in range(nrImages):
                nrPlot = ii*nrImages + jj
                # print('ii: %d   jj: %d  nrPlot: %d' %(ii, jj, nrPlot))
                plt.subplot(nrSteps, nrImages, nrPlot+1)
                ax = plt.gca()
                plotdata = self.images[ii,jj,...]
                ax.imshow(plotdata, cmap='gray', interpolation=interpolation)
                if hasattr(self, 'roi'):
                    roi = self.roi
                    rect = patches.Rectangle((roi[1],roi[0]),roi[3],roi[2], \
                                             linewidth=1,edgecolor='r',facecolor='none')
                    ax.add_patch(rect)
                title = ('step: %d image: %d' % (ii, jj))
                plt.title(title)
        plt.show(block=False)
        # return plt.gcf()
        return

    def _plotData(self, data, title='', interpolation="none"):
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
        plt.xlabel('position (um)')
        plt.ylabel('position (um)')
        plt.colorbar()
        plt.title(title)
        plt.show(block=False)
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
        return self._plotData(self.height-self.height[1,1], title='height (um)')

    def fitGauss(self, data=np.array([]), scale=0.1172E-6):
        '''fits a 2D Gauss to a calculated height
        
        data    2D array with height profile
        scale=F dimension of image pixel in the fiber plane. Default is 
                117 nm with the Mitutoyo 50X and 200 mm tube lens and 
                5.86 um detector pixels
        '''
        
        analysisTime = time.strftime('%Y%m%dT%H%M%S')
        if not data.any():
            try:
                data = self.height
            except AttributeError:
                msg = 'ho height profile calculated yet, run AnalyzeSurface() first'
                logging.error(msg)
                raise Exception(msg)
        else:
            logging.debug('using manually entered height profile') 
        shape = np.shape(data)
        x = np.linspace(0, shape[1], shape[1]) * self.scale *1e6
        x = x-np.mean(x)
        y = np.linspace(0, shape[0], shape[0]) * self.scale *1e6
        y = y-np.mean(y)
        x, y = np.meshgrid(x, y)
        
        # calculate initial estimages
        # size of square for which corner intensities are averaged            
        bs = int(shape[0]/10)
        
        # height at corners: [BL, BR, UL, UR]
        corners = [np.mean(data[:bs,:bs]), np.mean(data[:bs,-bs:]), np.mean(data[-bs:,:bs]), np.mean(data[-bs:,-bs:])]
        offset = np.mean(corners)
        # estimating tilt in mrad
        xtilt = (np.mean(corners[1::2]) - np.mean(corners[0::2]))*(self.scale*shape[1])*2000
        ytilt = (np.mean(corners[2:4]) - np.mean(corners[0:2]))*(self.scale*shape[0])*2000
        logging.debug('height at corners: %s' % str(corners))
        logging.debug('found offset: %+.2E' % (offset, ))
        logging.debug('tilt estimates: xtilt=%+.3e and ytilt=%+.3e  (mrad)' % (xtilt, ytilt))
        theta = 0

        (yo, xo) = (0, 0)
        detrend_params = (0, xo, yo, 4, 4, theta, offset, xtilt, ytilt)
        trend = twoD_GaussianWithTilt((x,y, self.scale), *detrend_params).reshape(shape)
        # perform rough detrend so amplitude and sigma can be estimated
        detrended_data = data - trend
        # height at corners: [BL, BR, UL, UR]
        detr_corners = [np.mean(detrended_data[:bs,:bs]),  np.mean(detrended_data[:bs,-bs:]), \
                        np.mean(detrended_data[-bs:,:bs]), np.mean(detrended_data[-bs:,-bs:])]
        amplitude = np.min(detrended_data) - np.mean(detr_corners)
        logging.debug('found amplitude: %.2E' % (amplitude))
        (d4s_x, d4s_y, xo_px, yo_px) = get_d4sigma(detrended_data, 1)
        if np.isnan(np.array([d4s_x, d4s_y, xo_px, yo_px])).any():
            sigma_x, sigma_y = 3, 3
            xo, yo = 0, 0
            logging.debug('could not estimate sigma from height profile, use defaults: %.2E %.2E' % (sigma_x, sigma_y))
        else:
            sigma_x = d4s_x * self.scale / 4 * 1E6
            sigma_y = d4s_y * self.scale / 4 * 1E6
            xo = x[0, int(round(xo_px))]
            yo = y[int(round(yo_px)), 0]
            logging.debug('estimated sigma: %.2E %.2E' % (sigma_x, sigma_y))
            logging.debug('estimated centroid: %.2E %.2E' % (xo, yo))
        
        initial_guess = (amplitude, xo, yo, sigma_x, sigma_y, theta, offset, xtilt, ytilt)
        ig = initial_guess
        shape = data.shape
        txt = 'initial_guess: amplitude: %.3fum\n\t\t(x0, y0): (%.1f, %.1f) um\n\t\t(sigma_x, sigma_y): (%.2f, %.2f) um\n\t\ttheta: %.3f (deg)\n\t\toffset: %.3f um\n\t\tbackground tilt (x, y): (%.3E, %.3E) (mrad)'
        theta_deg = ig[5]/np.pi*180
        vals = (ig[0], ig[1], ig[2], ig[3], ig[4], theta_deg, ig[6], ig[7], ig[8])
        print(txt % vals)
        logging.debug('starting 2d Gauss fit with these initial parameters:')
        for line in (txt % vals).splitlines():
            logging.info(line)
        
        initial_guessSurf = twoD_GaussianWithTilt((x, y, self.scale), *initial_guess).reshape(shape)
        popt, pcov = opt.curve_fit(twoD_GaussianWithTilt, (x, y, self.scale), data.ravel(), p0=initial_guess)
        data_fitted = twoD_GaussianWithTilt((x, y, self.scale), *popt).reshape(shape)
        self.data_fitted = data_fitted
        self.popt = popt
        
        txt = '\t\tamplitude: %.3fum\n\t\t(x0, y0): (%.2f, %.2f) um\n\t\t(sigma_x, sigma_y): (%.4f, %.4f) um\n\t\ttheta: %.3f (deg)\n\t\toffset: %.3f um\n\t\tbackground tilt (x, y): (%.3E, %.3E) (mrad)'
        theta_deg = np.mod(popt[5]/np.pi*180, 180)
        vals = (popt[0], popt[1], popt[2], popt[3], popt[4], theta_deg, popt[6], popt[7], popt[8])
        
        print('found fit params:')
        print(txt % vals)
        logging.info('found fit parameters:')
        for line in (txt % vals).splitlines():
            logging.info(line)
        
        # calculate centroid coordinates in detector pixels
        mnx, mxx = np.min(x), np.max(x)
        mny, mxy = np.min(y), np.max(y)
        if hasattr(self, 'roi'):
            self.x_detector = (popt[1]-mnx)/(mxx-mnx)*(x.shape[1]) + self.roi[1]
            self.y_detector = (popt[2]-mny)/(mxy-mny)*(y.shape[0]) + self.roi[0]
        else:
            self.x_detector = (popt[1]-mnx)/(mxx-mnx)*(x.shape[1]-1)
            self.y_detector = (popt[2]-mny)/(mxy-mny)*(y.shape[0]-1)
        
        txt2 = 'centroid location in detector pixels: (%.1f, %.1f)  (left, top)'% (self.x_detector, self.y_detector)
        print(txt2)
        logging.info(txt2)
        
        self.dimpleDepth = popt[0]
        self.sigma = (popt[3], popt[4])
        self.dimpleDiameter = (self._diameter(popt[3]), self._diameter(popt[4]))
        
        if 1:
            img = self._plotData(data, title='measured height profile (um)')
            img = self._plotData(detrended_data, title='tilt removed from data (um)')
            img = self._plotData(initial_guessSurf, title='initial guessed parameters')
            title = 'fitted Gauss (with tilt) (um)\ndepth: %.2fum, sigma: (%.3f HOR and %.3f VER)um' % (popt[0], self.sigma[0], self.sigma[1])
            img = self._plotData(data_fitted, title=title)
            img = self._plotData(data-data_fitted, title='fit residual (um) - stdev: %.2E (um)'%np.std(data-data_fitted))
        
        roc_x = self._roc(popt[3], self.popt[0])
        roc_y = self._roc(popt[4], self.popt[0])
        self.radiiOfCurvature = (roc_x, roc_y)
        
        msg1 = 'calculated radii of curvature: %.3f and %.3f um' % self.radiiOfCurvature
        print(msg1)
        logging.info(msg1)

        msg2 = 'calculated dimple diameter: %.3f and %.3f um' % self.dimpleDiameter
        print(msg2)
        logging.info(msg2)
        
        msg3 = 'calculated ellipticity: TBD'
        print(msg3)
        logging.info(msg3)
        
        msg4 = 'residual standard deviation: %.2E (um)' % np.std(data-data_fitted)
        print(msg4, '\n\n')
        logging.info(msg4)

        fp = self.filepath
        fn = self.filename[:15].decode() + '_fit_at_' + analysisTime + '.txt'

        with open(os.path.join(fp, fn), 'w') as f:
            try:
                f.write('Analysing file: %s\n' % self.filename.decode())
                f.write('Aanalysis timestamp: %s\n\n' % analysisTime)
                if hasattr(self, 'roi'):
                    roi = self.roi
                    f.write('using ROI: (%d,%d,%d,%d) (T,L,H,W)\n' % (roi[0],roi[1],roi[2],roi[3]))
                else:
                    f.write('no ROI used\n')
                f.write('2D Gauss fit params:\n')
                f.write('%s\n' % (txt % vals))
                f.write('\t\t%s\n' % txt2)
                f.write(msg1 + '\n')
                f.write(msg2 + '\n')
                f.write(msg3 + '\n')
                f.write(msg4 + '\n')
                logging.info('wrote output to file %s' % os.path.join(fp, fn))
            except Exception as error:
                logging.error('error during writing to file %s: %s' % (os.path.join(fp, fn), error))
                raise Exception(error)
                
    def fitCosine(self, roi, plotfit=False):
        '''roi in (X, Y, W, H)
        returns amplitude and phase'''
        
        data = self.averagedImages[:,roi[1]:roi[1]+roi[3],roi[0]:roi[0]+roi[2]]
        x = np.array(range(0,self.numStepAnalysis))*np.pi/2
        y = np.mean(np.mean(data, axis=2), axis=1)
        # val = amplitude * np.cos(x/period-phase) + offset

        # initial guess
        amplitude= (np.max(y)-np.min(y))/2
        offset = np.max(y)-amplitude
        # we already have a good estimate of the phase in self.unwrapped_phase
        phaseData = self.unwrapped_phase[roi[1]:roi[1]+roi[3],roi[0]:roi[0]+roi[2]]
        phase = np.mean(phaseData)
        period = 1
        initial_guess = (amplitude, phase, offset,  period)
        popt, pcov = opt.curve_fit(self._cos, x, y,  p0=initial_guess)
        txt = 'amplitude: %.3f phase: %.3f° offset: %.3f period: %.3f' % (popt[0],  popt[1]*180/np.pi,  popt[2],  popt[3])
        print(txt)
        #print('phase from map: %.3f deg' % (phase*180/np.pi))
        if plotfit:
            fig = plt.figure()
            plt.hold(True)
            plt.plot(x*180/np.pi ,y ,'r+-')
            x_f = np.linspace(np.min(x), np.max(x), 200)
            plt.plot(x_f*180/np.pi, image._cos(x_f,*popt),'g-')
            plt.legend(('data', 'fit'))
            plt.xlabel('phase (deg)')
            plt.ylabel('signal (counts)')
            txt = 'amplitude: %.3f phase: %.3f° offset: %.3f period: %.3f * 2PI' % (popt[0],  popt[1]*180/np.pi,  popt[2],  popt[3])
            ax=plt.gca()
            ax.text(0.05,0.85, txt, fontsize=11)
            plt.show()
            plt.grid(True)
        return popt

    def _cos(self, x, amplitude, phase, offset,  period):
        '''returns cosine for given x, amplitude, phase, offset and period. x and phase in radians'''
        val = amplitude * np.cos(x/period-phase) + offset
        return val
        
    def _roc(self, sigma, depth):
        # returns the radius of curvature for a given sigma and depth
        D = 2*np.sqrt(2) * sigma
        radius_curvature = D**2 / (8*depth)
        #with D = full width at height of 1/e
        return np.abs(radius_curvature)
    
    def _diameter(self, sigma):
        # returns the dimple 1/e diameter
        return 2*np.sqrt(2) * sigma
    
if __name__ == '__main__':
    pass
    
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
