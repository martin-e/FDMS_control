# routines for fitting position of core 

import time
import os
import logging
import numpy as np
from tifffile import imread
from twoD_Gaussian import simple_twoD_Gaussian
from d4s import get_d4sigma
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from IPython import embed

from twoD_Gaussian import twoD_Gaussian

def fitCore(file, scale=0.1172E-6):
    '''returns the camera pixel coordinates of the maximum
    '''
    
    roi = 100
    default_sigma = 10
    if os.path.isfile(file):
        a_path = os.path.dirname(file)
    else:
        logging.error('could not find file %s' % file)
        raise Exception('could not find file %s' % file)

    try:
        img = imread(file)
    except Exception as e:
        msg = 'error during reading file: %s' % e
        logging.error(msg)
        raise Exception(msg)

    a_time = time.strftime('%Y%m%dT%H%M%S')
    
    # calculate initial estimages
    max = np.max(img)
    (row, col) = np.where((img == max))
    y0 = row[0]
    x0 = col[0]
    #logging.debug
    print('estimated centroid: %.2E %.2E' % (x0, y0))
    
    #idx are the ROI(T, T+h, L, L+w) coordinates
    idx = np.int16([y0-(roi/2), y0+(roi/2), x0-(roi/2), x0+(roi/2)])
    # check if idx is defined outside image
    if idx[0] < 0:
        idx[0] = 0
    if idx[1] > np.shape(img)[0]:
        idx[1] = np.shape(img)[0]
    if idx[2] < 0:
        idx[2] = 0
    if idx[3] > np.shape(img)[1]:
        idx[3] = np.shape(img)[1]
    
    #logging.debug
    print('using ROI: [%d:%d, %d:%d] ROI(T:T+h, L:L+w)' % (idx[0], idx[1], idx[2], idx[3]))
    img_roi = img[idx[0]:idx[1], idx[2]:idx[3]]
    x = np.arange(0, np.shape(img_roi)[1])
    y = np.arange(0, np.shape(img_roi)[0])
    x, y = np.meshgrid(x, y)

    offset = np.min(img_roi)
    amplitude = max - offset
    logging.debug('estimated amplitude and offset: %+.2E %+.2E' % (amplitude, offset))
    (d4s_x, d4s_y, xo_px, yo_px) = get_d4sigma(img_roi, 1)
    if np.isnan(np.array([d4s_x, d4s_y, xo_px, yo_px])).any():
        sigma_x, sigma_y = default_sigma, default_sigma
        msg = 'could not estimate sigma from height profile, use defaults: %.2E %.2E' % (sigma_x, sigma_y)
        logging.debug(msg)
    else:
        sigma_x = d4s_x / 8
        sigma_y = d4s_y / 8
        logging.debug('estimated sigma: %.2E %.2E' % (sigma_x, sigma_y))
    
    
    initial_guess = (amplitude, xo_px, yo_px, sigma_x, sigma_y, offset)
    
    popt, pcov = curve_fit(simple_twoD_Gaussian, (x, y), img_roi.ravel(), p0=initial_guess)
    vals = (popt[0], popt[1]+idx[2], popt[2]+idx[0], popt[3], popt[4], popt[5])
    txt = '\t\tamplitude: %.1f\n\t\t(x0, y0): (%.1f, %.1f) px\n\t\t(sigma_x, sigma_y): (%.1f, %.1f) px\n\t\toffset: %.1f\n'
    print('found fit params:')
    print(txt % vals)
    fn = file.replace('.TIFF','').replace('.tiff','').replace('.tiff','').replace('.tif','')
    fn += ('_' + a_time + '_fit_results.txt')
    with open(os.path.join(a_path, fn), 'w') as f:
        f.write('Analysing file: %s\n' % os.path.basename(file))
        f.write('Aanalysis timestamp: %s\n\n' % a_time)
        f.write('using ROI: [%d:%d, %d:%d] ROI(T:T+h, L:L+w)' % (idx[0], idx[1], idx[2], idx[3]))
        f.write('2D Gauss fit params:\n')
        f.write('%s\n' % (txt % vals))

    logging.info('found fit parameters:')
    for line in (txt % vals).splitlines():
        logging.info(line)

    fig, axes = plt.subplots(1, 2,figsize=(8,4))
    plt.subplot(1,2,1)
    
    # contourplot
    title = 'fitted Gauss\namplitude: %.1f, (x0, y0): (x=%.1f, y=%.1f)px\n' % (popt[0], popt[1]+idx[2], popt[2]+idx[0])
    shape = np.shape(img_roi)
    extent = (idx[2], idx[3], idx[1], idx[0])    
    a = plt.imshow(img_roi, extent=extent, aspect='auto')
    data_fitted = simple_twoD_Gaussian((x, y), *popt).reshape(img_roi.shape)
    ax = plt.gca()
    ax.contour(data_fitted[::-1,:], 5, extent=extent, colors='w')
    cb1 = plt.colorbar(a, ax=ax)
    plt.title(title)
    
    
    plt.subplot(1,2,2)
    title = 'fit residual'
    a2 = plt.imshow(img_roi-data_fitted, extent=extent, aspect='auto')
    ax2 = plt.gca()
    cb1 = plt.colorbar(a2, ax=ax2)
    plt.title(title)        
    if 0:
        plt.show()
    
    fn = file.replace('.TIFF','').replace('.tiff','').replace('.tiff','').replace('.tif','')
    fn += ('_' + a_time + '_fitCore.png')
    fig.savefig(os.path.join(a_path, fn))
    print('saved plot %s' % os.path.join(a_path, fn))
    