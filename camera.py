# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 21:05:20 2017

@author: eschenm
"""

import logging, sys, time
import pyflycap
from pyFlyCapture2 import *

if sys.version_info > (3,):
    class CameraError(Exception):
        pass
else:
    class CameraError(StandardError):
        pass

class Camera():
    def __init__(self, camera_ini, libdir = '', debug = False):
        self.connectCam(libdir, debug)
        self.prepareSettings(camera_ini)

    def connectCam(self, libdir = '', debug = True):
        self.cam = pyflycap.FlyCapture(libdir = '', debug = True)
        logging.debug('loaded PyFlyCam camera dll driver')
        numCameras = self.cam.getNumOfCameras()
        if numCameras == 0:
            logging.error('camera not found')
            raise CameraError('camera not found')
        self.guid = self.cam.getCameraFromIndex(0)
        self.cam.connect(self.guid)
        time.sleep(0.1)
        self.cameraInfo = self.cam.getCameraInfo()
        if self.cameraInfo.sensorResolution:
            self.cam.resolution = list()
            for val in bytes.decode(self.cameraInfo.sensorResolution).split('x'):
                self.cam.resolution.append(int(val))
        logging.debug(str(self.cameraInfo))
        # stats = self.cam.getCameraStats()
        logging.info('camera connected')
        
    def prepareSettings(self, camera_ini):
        self.camera_ini = camera_ini
        if camera_ini['nrBits'] == 8:
            pixelFormat = pyflycap.fc2PixelFormat.FC2_PIXEL_FORMAT_MONO8.value
        elif camera_ini['nrBits'] == 16:
            pixelFormat = pyflycap.fc2PixelFormat.FC2_PIXEL_FORMAT_MONO16.value
        else:
            logging.error('invalid or unsupporte nr of bits per pixel given in .ini file')
            raise CameraError('invalid or unsupporte nr of bits per pixel given in .ini file')

        logging.debug('disabling all properties which can be set to \"auto\"')
        for propType in pyflycap.fc2PropertyType:
            if propType.value > 17:
                break
            propInfo = self.cam.getPropertyInfo(propType.value)
            prop = self.cam.getProperty(propType.value)
            if bool(propInfo.autoSupported):
                logging.debug('setting property %s to 0' % propType.name)
                prop.autoManualMode = 0
                self.cam.setProperty(prop)
                time.sleep(0.1)
                logging.debug('property %s set to %s' % (propType.name, str(self.cam.getProperty(propType.value))))
        
        propType = pyflycap.fc2PropertyType.FC2_FRAME_RATE
        propInfo = self.cam.getPropertyInfo(propType.value)
        prop = self.cam.getProperty(propType.value)
        prop.absValue = camera_ini['framerate']
        self.cam.setProperty(prop)
        time.sleep(0.1)
        logging.info('framerate set to: %.3f ms' % self.cam.getProperty(pyflycap.fc2PropertyType.FC2_FRAME_RATE.value).absValue)
        logging.info('set gain to zero and integration time to %.3f ms' % camera_ini['integrationTime'])
        
        self.setShutter(camera_ini['integrationTime'])
        propType = pyflycap.fc2PropertyType.FC2_GAIN
        prop = self.cam.getProperty(propType.value)
        prop.absValue = 0
        self.cam.setProperty(prop)
        time.sleep(0.1)
        logging.debug('gain is now: %.3f dB' % self.cam.getProperty(pyflycap.fc2PropertyType.FC2_GAIN.value).absValue)
            
        # setting FORMAT7 mode and ROI
        (supported, fm7Info)= self.cam.getFormat7Info(0)
        self.fm7Settings = pyflycap.Format7ImageSettingsStruct()
        self.fm7Settings.mode = 0
        try:
            self.fm7Settings.offsetX = camera_ini['roi'][0]
            self.fm7Settings.offsetY = camera_ini['roi'][1]
            self.fm7Settings.width   = camera_ini['roi'][2]
            self.fm7Settings.height  = camera_ini['roi'][3]
        except:
            logging.error('could not use ROI settings in .ini file')
            raise CameraError('could not use ROI settings in .ini file')
        
        self.fm7Settings.pixelFormat = pixelFormat
        (isValid, fm7PacketInfo) = self.cam.validateFormat7Settings(self.fm7Settings)
        if isValid:
            self.cam.setFormat7ConfigurationPacket(self.fm7Settings, int(fm7PacketInfo.recommendedBytesPerPacket))
            logging.info('format7 settings: %s' % str(self.fm7Settings))
            logging.debug('format7 packet info: %s' % str(fm7PacketInfo))
            logging.debug('Format7 mode 0 settings are set')
        else:
            logging.error('invalid format 7 settings defined')
            raise CameraError("!!! invalid format 7 settings defined")
            
    def setShutter(self, integrationTime):
        propType = pyflycap.fc2PropertyType.FC2_SHUTTER
        prop = self.cam.getProperty(propType.value)
        prop.absValue = integrationTime
        self.cam.setProperty(prop)
        time.sleep(0.1)
        self.camera_ini['integrationTime'] = self.cam.getProperty(pyflycap.fc2PropertyType.FC2_SHUTTER.value).absValue
        logging.info('integration time set to: %.3f ms' % self.camera_ini['integrationTime'])

    def startCapture(self):
        self.cam.startCapture()
        logging.debug('started camera acquistion')
    
    def stopCapture(self):
        self.cam.stopCapture()
        logging.debug('stopped camera acquistion')

    def close(self):
        self.cam.destroyContext()
        self.cam.unloadLib()
        logging.info('disconnected camera and unloaded damera dll')
        
    def createImage(self):
        image = self.cam.createImage()
        logging.debug('created image memory buffer')
        return image
        
    def retrieveBuffer(self, image):
        self.cam.retrieveBuffer(image)
        logging.debug('retrieved image buffer')
        return image
    
    def getImageData(self, image):
        imageData = self.cam.getImageData(image)
        logging.debug('read data from stored image buffer')
        return imageData
