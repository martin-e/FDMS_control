# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 20:20:37 2017

@author: eschenm
"""

import os, logging, sys, math, h5py
import numpy as np
import matplotlib as mpl

if sys.version_info > (3,):
    class AnalyzeError(Exception):
        pass
else:
    class AnalyzeError(StandardError):
        pass

class AnalyzeSurface():
    def __init__(self, datapath):
        self.datapath = os.path.abspath(datapath)
        self.wavelength = 6e-7
        
    def analyzeSurface(self, filename):
        if os.path.isfile(filename):
            filepath = os.path.realpath(filename)
        else:
            filepath = os.path.realpath(os.path.join(datapath, filename))
        if not os.path.isfile(filepath):
            logging.error('file %s not found for analysis' % filepath)
            raise AnalyzeError('file %s not found for analysis' % filepath)
        logging.info('starting analysis of file %s'  % filepath)
        try:
            self.f = h5py.File(filepath,  "r")
            #self.filename = os.path.split(filepath)[1]
            
        except:
            logging.error('could not open file %s' % filepath)
            raise AnalyzeError('could not open file %s' % filepath)

        logging.debug('file opened for reading')
        # read contents of hdf5 file
        
        images = self.f['images']
        timestamps = self.f['timestamps']
        setpoints = images.attrs['setpoints']
        pvs       = images.attrs['pvs']
        numImages = images.attrs['numImages']
        numSteps  = images.attrs['numSteps']
        filename  = images.attrs['filename']
        
        # average multiple images
        averaged = np.mean(images,1)
        img = averaged
        if numSteps == 5:
            # phase
            nom = (-2*img[1,...] + 2*img[2,...])
            denom = (img[0,...] - 2*img[2,...] + img[4,...])
            phase = np.arctan(nom / denom)

            # contrast
            term1 = np.power((img[1,...] - img[3,...]), 2)
            term2 = np.power((img[0,...] -2*img[2,...] + img[4,...]), 2)
            nom = 2*np.power(4*term1 + term2, 0.5)
            denom = (img[0,...] + 2*(img[1,...] + img[2,...] + img[3,...]) + img[4,...])
            contrast =  nom / denom

        if numSteps == 7:
            nom = (4*img[1,...] - 2*img[3,...] + img[5,...])
            denom = (-img[0,...] + 7*img[2,...] - 7*img[4,...] + img[6,...])
            phase = np.arctan(nom / denom)
 
            # contrast (based on first 5 images)
            term1 = np.power((img[1,...] - img[3,...]), 2)
            term2 = np.power((img[0,...] -2*img[2,...] + img[4,...]), 2)
            nom = 2*np.power((4*term1 + term2), 0.5)
            denom = (img[0,...] + 2*(img[1,...] + img[2,...] + img[3,...]) + img[4,...])
            contrast =  nom / denom

        mpl.pyplot.imshow(contrast);mpl.pyplot.colorbar()
        mpl.pyplot.title('contrast of %s' % os.path.split(filepath)[1])
        mpl.pyplot.imshow(phase);mpl.pyplot.colorbar()
        mpl.pyplot.title('phase of %s' % os.path.split(filepath)[1])
        height = np.unwrap(phase) * self.wavelength / 2
        mpl.pyplot.imshow(height);mpl.pyplot.colorbar()
        mpl.pyplot.title('height (in m) of %s' % os.path.split(filepath)[1])

        self.f.close()
        result = {'contrast':contrast, 'phase':phase, 'height':height}
        return result
        
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
