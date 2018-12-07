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
from scipy.optimize import curve_fit
from scipy.optimize import leastsq
from skimage.restoration import unwrap_phase
from twoD_Gaussian import twoD_GaussianWithTilt
from d4s import get_d4sigma
from IPython import embed

class fdmsImage():
    def __init__(self, filename, a_path=''):
        '''
        Opens and reads hdf5 file stored by FDMS control software
        
        parameters:
            filename    path to hdf5 file
            a_path      path to directory with analysis results stored in a
                            daily directory structure similar to how the measurement
                            data is organized. If omitted, it stores all output in
                            the same directory as the hdf5 file.

        image = fdmsImage(pathToHdf5File)
        image.analyzeSurface(roi=(410,390, 400, 400), \
            useNrOfSteps=5)
        
        global variabeles control behavior of plot functions:
        PLOT_SAVE
            if initialized and True, plots will be saved to disk. Useful for batch processing
        PLOT_SHOW
            if initialized and True, plots will be displayed. Useful for batch processing
        
        
        image.plotInterferograms()
        image.plotContrast()
        image.plotPhase()
        image.plotUnwrappedPhase()
        image.plotHeight()
        image.exportHeight()
		image.fitGauss()
        '''

        #define default behavior
        
        if 'PLOT_SAVE' in globals():
            self._plot_save = bool(globals()['PLOT_SAVE'])
            msg = 'using global setting for saving plots: %s saving' % ['Disabled', 'Enabled'][self._plot_save]
            print(msg)
            logging.info(msg)
        else:
            self._plot_save = True
            msg = 'global parameter not found, %s saving figures' % ['disabled', 'enabled'][self._plot_save]
            print(msg)
            logging.info(msg)

        if 'PLOT_SHOW' in globals():
            self._plot_show = bool(globals()['PLOT_SHOW'])
            msg = 'using global setting for displaying plots: %s displaying' % ['Disabled', 'Enabled'][self._plot_save]
            print(msg)
            logging.info(msg)
        else:
            self._plot_show = True
            msg = 'global parameter not found, %s displaying figures' % ['disabled', 'enabled'][self._plot_show]
            print(msg)
            logging.info(msg)
        
        msg = ('read contents of file %s' % filename)
        print(msg)
        logging.info(msg)
        if os.path.isfile(filename):
            filepath = os.path.realpath(filename)
        else:
            logging.error('could not find file %s' % filename)
            raise Exception('could not find file %s' % filename)
        if a_path:
            if not os.path.isdir(a_path):
                msg = 'could not find path to analysis results directory: %s' % a_path
                logging.error(msg)
                raise Exception(msg)
            a_path = os.path.join(a_path, os.path.basename(filename)[:8])
            if not os.path.isdir(a_path):
                os.mkdir(a_path)
                print('created new directory for analysis results: %s' % a_path)
        else:
            a_path = os.path.dirname(filename)
        self.a_path = a_path
        self.a_time = time.strftime('%Y%m%dT%H%M%S')
        
        try:
            with h5py.File(filepath, "r") as hdf5File:
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
        self.height = self.unwrapped_phase/(np.pi*2) * self.wavelength/2 * 1e6 * -1
        # subtract average height of corners from height profile
        
        bs = int(self.height.shape[0]/10)
        corners = [np.mean(self.height[:bs,:bs]), np.mean(self.height[:bs,-bs:]), np.mean(self.height[-bs:,:bs]), np.mean(self.height[-bs:,-bs:])]
        self.height -= np.mean(corners)
        logging.info('calculating contrast, phase and phase unwrapping done')
        
        img = self.averagedImages
        nom = (img[4,...] - img[0,...])
        denom =  2*(img[3,...] - img[1,...])
        self.phaseStep = np.arccos(nom/denom)[roi[0]:roi[0]+roi[2], roi[1]:roi[1]+roi[3]]

        idx = np.logical_not(np.isnan(self.phaseStep))
        phaseMean = np.mean(self.phaseStep[idx].reshape(-1))/np.pi*180
        phaseStd = np.std(self.phaseStep[idx].reshape(-1))/np.pi*180
        msg = 'Phase step calibration info:\n\tmean phase step value: %.3f deg\n\tstandard deviation: %.2f deg (using the first 5 steps only!!)' % (phaseMean, phaseStd)
        print(msg)
        logging.info(msg)
        self.phaseMean = phaseMean
        self.phaseStd = phaseStd
        
    def plotInterferograms(self, interpolation="none"):
        filename = self.filename
        try:
            sh = self.averagedImages.shape
        except AttributeError:
            msg = 'interferograms not yet averaged! Run analyzeSurface() first!'
            print(msg)
            logging.error(msg)
            return
        fig, ax = plt.subplots(figsize=(24, 8))
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
        ax = plt.subplot(248)
        ax.axis('off')
        
        if hasattr(self, 'roi'):
            roitxt = 'ROI(T,L,H,W): (%d,%d,%d,%d)' % (roi[0],roi[1],roi[2],roi[3])
        else:
            roitxt = 'no ROI defined'
        txt = '%s\n%s\nusing %d images' % (str(filename), roitxt, self.numStepAnalysis)

        ax.text(0.05,0.5, txt, fontsize=11)
        plt.tight_layout()
        if self._plot_show:
            plt.show(block=False)
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time + '_interferograms.png'
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))
        return fig

    def plotPhaseStepper(self, ):
        try:
            roi = self.roi
        except AttributeError:
            error('no roi specified, run analyzeSurface')
        phaseStep = self.phaseStep
        fig = self._plotData(phaseStep/np.pi*180, title='average phase step (deg)')
        if self._plot_show:
            plt.show(block=False)
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time + '_averagePhaseStep.png'
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))

        idx = np.logical_not(np.isnan(phaseStep))
        phaseMean = self.phaseMean
        phaseStd = self.phaseStd
        fig = plt.figure()
        plt.hist(phaseStep[idx].reshape(-1)/np.pi*180, 100)
        plt.xlabel('phase step (deg)')
        plt.ylabel('nr. (-)')
        plt.title('phase step mean: %.3f deg std:  %.3f deg' % (phaseMean, phaseStd))
        if self._plot_show:
            plt.show(block=False)
        fn = self.filename[:15] + '_' + self.a_time + '_phaseHistogram.png'
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))


    def plotAllInterferograms(self, interpolation="none"):
        filename = self.filename
        (nrSteps, nrImages, rows, cols) = np.shape(self.images)

        fig, ax = plt.subplots(figsize=(nrImages*4, nrSteps*3))
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
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time + '_allInterferograms.png'
        plt.tight_layout()
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))
        if self._plot_show:
            plt.show(block=False)
        return fig

    def _plotData(self, data, title='', interpolation="none", applyScaling=True):
        filename = self.filename
        if not title:
            title = str(filename)
        plot = plt.figure()
        shape = np.shape(data)
        
        if applyScaling:
            extentX = self.scale*1e6 * np.array((0., shape[1]))
            extentX -= np.mean(extentX)
            extentY = self.scale*1e6 * np.array((0., shape[0]))
            extentY -= np.mean(extentY)
            extent = list(extentX)
            extent.append(extentY[0])
            extent.append(extentY[1])
            plt.imshow(data, interpolation=interpolation, extent=extent, aspect='auto', cmap='jet')
            plt.xlabel('position (um)')
            plt.ylabel('position (um)')
        else:
            plt.imshow(data, interpolation=interpolation, aspect='auto')
        plt.colorbar()
        plt.title(title)
        if self._plot_show:
            plt.show(block=False)
        return plot
        
    def plotContrast(self):
        contrastData = self.contrast
        contrastData[contrastData > 1] = 1
        fig = self._plotData(contrastData, title='fringe contrast', applyScaling=False)
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time + '_contrast.png'
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))
        return fig
        
    def plotPhase(self):
        fig = self._plotData(self.wrappedPhase, title='wrapped phase (rad)', applyScaling=False)
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time + '_wrappedPhase.png'
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))
        return fig
        
    def plotUnwrappedPhase(self):
        fig = self._plotData(self.unwrapped_phase, title='unwrapped phase (rad)')
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time + '_unwrappedPhase.png'
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))
        return fig
    
    def plotHeight(self):
        fig = self._plotData(self.height, title='height (um)')
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time + '_height.png'
        if self._plot_save:
            fig.savefig(os.path.join(fp, fn))
        return fig
    
    def exportHeight(self, path=''):
        '''exports the height map (um units) in a hdf5 file
        
        input parameter        
            path    directory where hdf5 file will be stored, defaults to instance analysis output 
        returns the hdf5 file path
        
        reading example:
            with h5py.File(<filepath>, 'r') as f:
                heightmap = f['height'][...]
                filename = height.attrs['filename']
                analysis_timestamp = height.attrs['analysis_timestamp']
                scale = height.attrs['scale']
                roi = height.attrs['roi']
                extent = height.attrs['extent']
            '''

        if not path:
            path = self.a_path
        try:
            height = self.height
        except AttributeError:
            msg = 'interferograms not yet averaged! Run analyzeSurface() first!'
            print(msg)
            logging.error(msg)
            return
        fp = path
        fn = self.filename[:15] + '_' + self.a_time + '_height.hdf5'
        HDF5_FILE = os.path.abspath(os.path.join(fp, fn))
        logging.debug('Open file %s for exporting height map' % HDF5_FILE)
        with h5py.File(HDF5_FILE, 'w') as f:
            dset = f.create_dataset("height", data=height, compression='lzf')
            # filename containing interferogram images
            dset.attrs['filename'] = np.string_(self.filename)
            # timestamp of analysis
            dset.attrs['analysis_timestamp'] = self.a_time
            # pixel size of image
            dset.attrs['scale'] = self.scale
            # used ROI of interferogram
            dset.attrs['roi'] = self.roi
            shape = height.shape
            extent = self.scale*1e6 * np.array((-shape[1], shape[1], -shape[0], shape[0]))/2
            # extent (use in imshow plot function as extent=list(extent) argument for scaling axes)
            dset.attrs['extent'] = extent
        logging.info('Exported height map to %s' % HDF5_FILE)
        return HDF5_FILE
            
    def fitGauss(self, data=np.array([]), scale=0.1172E-6):
        '''fits a 2D Gauss to a calculated height
        
        data    2D array with height profile
        scale=F dimension of image pixel in the fiber plane. Default is 
                117 nm with the Mitutoyo 50X and 200 mm tube lens and 
                5.86 um detector pixels
        '''
        
        analysisTime = self.a_time
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
            msg = 'could not estimate sigma from height profile, use defaults: %.2E %.2E' % (sigma_x, sigma_y)
            logging.debug(msg)
        else:
            sigma_x = d4s_x / 8 * self.scale * 1E6
            sigma_y = d4s_y / 8 * self.scale * 1E6
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
        # print(txt % vals)
        logging.debug('starting 2d Gauss fit with these initial parameters:')
        for line in (txt % vals).splitlines():
            logging.info(line)
        
        initial_guessSurf = twoD_GaussianWithTilt((x, y, self.scale), *initial_guess).reshape(shape)
        popt, pcov = curve_fit(twoD_GaussianWithTilt, (x, y, self.scale), data.ravel(), p0=initial_guess)
        if popt[3] < popt[4]:
            popt[3], popt[4] = popt[4], popt[3]
            popt[5] += (popt[5] + np.pi/4)
        popt[5] %= np.pi/2
        data_fitted = twoD_GaussianWithTilt((x, y, self.scale), *popt).reshape(shape)
        self.data_fitted = data_fitted
        self.popt = popt
        
        txt = '\t\tamplitude: %.3fum\n\t\t(x0, y0): (%.2f, %.2f) um\n\t\t(sigma_x, sigma_y): (%.4f, %.4f) um\n\t\ttheta: %.3f (deg)\n\t\toffset: %.3f um\n\t\tbackground tilt (x, y): (%.3E, %.3E) (mrad)'
        theta_deg = popt[5]/np.pi*180
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
        self.ellipticity = 1 - np.min((popt[3], popt[4]))/np.max((popt[3], popt[4]))
        roc_x = self._roc(popt[3], self.popt[0])
        roc_y = self._roc(popt[4], self.popt[0])
        self.radiiOfCurvature = (roc_x, roc_y)
        self.residualStdevGauss = np.std(data-data_fitted)
        
        fp = self.a_path
        fn = self.filename[:15] + '_' + self.a_time
        if 1:
            # contourplot
            title = 'fitted Gauss (with tilt) (um)\ndepth: %.2fum, sigma: (x=%.2f, y=%.2f)um\nRoC: (x=%.2f, y=%.2f)um, ellipticity: %.2f%%' % (popt[0], self.sigma[0], self.sigma[1], roc_x, roc_y, self.ellipticity*100)
            fig = self._plotData(data, title=title)
            ax = plt.gca()
            #ax.hold(True)
            ax.contour(x, y, data_fitted[::-1,:], 8, colors='w')
            #if self._plot_show:
            #    plt.show(block=False)
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitGaussContour.png'))
        
            fig = self._plotData(data-data_fitted, title='fit residual (um) - stdev: %.2E (um)'%self.residualStdevGauss)
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitResidual.png'))

        # fit debugging plots
        if 0:
            fig = self._plotData(data, title='measured height profile (um)')
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitHeight.png'))

            fig = self._plotData(detrended_data, title='tilt removed from data (um)')
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitTiltRemoved.png'))

            fig = self._plotData(initial_guessSurf, title='initial guessed parameters')
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitInitialGuessedParameters.png'))
        
            title = 'fitted Gauss (with tilt) (um)\ndepth: %.2fum, sigma: (x=%.2f, y=%.2f)um\nRoC: (x=%.2f, y=%.2f)um, ellipticity: %.2f%%' % (popt[0], self.sigma[0], self.sigma[1], roc_x, roc_y, self.ellipticity*100)
            fig = self._plotData(data_fitted, title=title)
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitGauss.png'))

        # now continue with fitting sphere
        # find all (x, y) pixels within the 1/e radius from the dimple center 
        idx = ((x-popt[1])/popt[3])**2 + ((y-popt[2])**2/popt[4]**2) < 1
        # ravel data and make coordinates matrix:
        coords = np.stack((x[idx].ravel(), y[idx].ravel(), data[idx].ravel())).T
        #initial parameter guess using results from gauss fit
        roc = (roc_x+roc_y)/2
        p0 = (popt[3],popt[4],roc-popt[6],roc)
        
        # define error function
        errfunc = lambda p, x: self._sphere(p, x) - p[3]        
        p1, flag = leastsq(errfunc, p0, args=(coords,))
        self.roc_sphere = p1[3]
        sphereFit = np.nan*np.zeros(x.shape)
        sphereFit[idx] = self._sphereSurf(p1, coords[:,:2])
        # fit debugging plots

        if 1:
            title = 'fit sphere (um)  -  RoC = %.3f' % self.roc_sphere
            fig = self._plotData(sphereFit, title=title)
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitSphere.png'))
            self.residual = np.nan*np.zeros(x.shape)
            self.residual[idx] = data[idx] - sphereFit[idx]
            self.residualStdevSphere = np.std(self.residual[idx])
            title = 'residual of spherical fit (um)  -  stdev: %.3E' % self.residualStdevSphere
            fig = self._plotData(self.residual, title=title)
            if self._plot_save:
                fig.savefig(os.path.join(fp, fn+'_fitSphereResidual.png'))

        msg1 = 'calculated radii of curvature: %.3f and %.3f um' % self.radiiOfCurvature
        print(msg1)
        logging.info(msg1)

        msg2 = 'calculated radius of curvature from spherical fit of 1/e diameter: %.3f' % self.roc_sphere
        print(msg2)
        logging.info(msg2)
        
        msg3 = 'calculated dimple diameter: %.3f and %.3f um' % self.dimpleDiameter
        print(msg3)
        logging.info(msg3)
        
        msg4 = 'calculated ellipticity:%.4f' % self.ellipticity
        print(msg4)
        logging.info(msg4)
        
        msg5 = 'gauss fit residual standard deviation: %.2E (um)' % self.residualStdevGauss
        print(msg5)
        logging.info(msg5)

        msg6 = 'sphere fit residual standard deviation: %.2E (um)' % self.residualStdevSphere
        print(msg6)
        logging.info(msg6)

        msg7 = 'average phase step: %.3f deg, stdev: %.3f deg(based on first 5 interferograms only!)' % (self.phaseMean, self.phaseStd)
        print(msg7, '\n\n')
        logging.info(msg7)

        fp = self.a_path
        fn = self.filename[:15] + '_fit_at_' + self.a_time + '.txt'

        try:
            with open(os.path.join(fp, fn), 'w') as f:
                f.write('Analysing file: %s\n' % self.filename)
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
                f.write(msg5 + '\n')
                f.write(msg6 + '\n')
                f.write(msg7 + '\n')
                logging.info('wrote output to file %s' % os.path.join(fp, fn))
        except Exception as error:
            logging.error('error during writing to file %s: %s' % (os.path.join(fp, fn), error))
            raise Exception(error)
        
        # write output in .csv file
        fn = self.filename[:15] + '_' + self.a_time + '_results.csv'
        try:
            with open(os.path.join(fp, fn), 'w') as f:
                txt1 = '%s,%.3E,%.2f,%.2f,%.3E,%.3E,%.2f,%.3f,%.3E,%.3E,'
                txt2 = '%d,%d,%d,%d,%.3f,%.3f,%.3f,%.3E,%.3f,%.3f,%.5f,%.3f\n'
                vals1 = (self.filename,popt[0],self.x_detector,self.y_detector,popt[3],popt[4],theta_deg,popt[6],popt[7],popt[8])
                vals2 = (roi[0],roi[1],roi[2],roi[3],roc_x,roc_y,self.roc_sphere,self.ellipticity,self.phaseMean,self.phaseStd,self.residualStdevGauss,self.residualStdevSphere)
                f.write(txt1 % vals1)
                f.write(txt2 % vals2)
                f.write('filename,depth,centroid_left,centroid_top,sigma_x,sigma_y,theta,offset,tiltX,tiltY,roi_T,roi_L,roi_H,roi_W,RoC_x,RoC_y,RoC_sphere,ellipticity,meanPhaseStep,stdevPhaseStep,residual_stdev_gaussFit,residual_stdev_sphereFit\n')
                f.write('-,um,pix,pix,um,um,deg,um,mrad,mrad,pix,pix,pix,pix,um,um,um,-,deg,deg,um,um\n')            
        except Exception as error:
            logging.error('error during writing to file %s: %s' % (os.path.join(fp, fn), error))
            raise Exception(error)
        print('wrote dimple parameters in csv file %s' % os.path.join(fp, fn))

        
    def _sphere(self, p, coords):
        '''returns r at given coordinates for given p'''
        # source https://stackoverflow.com/questions/15785428/how-do-i-fit-3d-data
        x0, y0, z0, R = p
        x, y, z = coords.T
        return np.sqrt((x-x0)**2 + (y-y0)**2 + (z-z0)**2)
        
    def _sphereSurf(self, p, coords):
        '''returns surface map for given (x,y) coordinates with given p'''
        x0, y0, z0, R = p
        x, y = coords.T
        # R**2 = (x-x0)**2 + (y-y0)**2 + (z-z0)**2
        # (z-z0)**2 = R**2 - ((x-x0)**2 + (y-y0)**2)
        # z-z0 = np.sqrt(R**2 - ((x-x0)**2 + (y-y0)**2))
        z = -np.sqrt(R**2 - ((x-x0)**2 + (y-y0)**2)) + z0
        return z
        
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
