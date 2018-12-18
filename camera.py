# -*- coding: utf-8 -*-
'''
@author: eschenm
'''

import logging
import numpy as np
import sys
import socket
import time
import numpy as np


class CameraError(Exception):
    '''Raised in case of failed interaction with the camera application.'''
    pass


class CameraClient:

    def __init__(self, camera_ini, host='localhost', tcpport=14901):
        logging.info('opening connection to camera application')
        self._ini = camera_ini
        try:
            self._sock = socket.create_connection((host, tcpport))
            self._recv_buf = bytearray()
        except Exception as e:
            raise CameraError('error during connecting, is camera application started? Message: %s' % e)
        resp = self.read_line()
        if not resp.startswith(b'QMI_CAMERA'):
            raise CameraError('Unexpected message from camera server application')
        logging.debug('successfully opened connection to camera application')
        nrBits = str(camera_ini['nrBits'])
        if nrBits not in ['8', '16']:
            raise CameraError('illegal nr of bits in .ini file: %s' % nrBits)
        self.set_pixel_format('Mono'+nrBits)
        self.set_black_level(0)
        self.set_gain(0)
        self.start_acquisition()
        self.set_exposure_time(camera_ini['exposureTime'])
        self.set_frame_rate(camera_ini['framerate'])
        self.start_acquisition()
        logging.info('connected and started camera')
        
    def close(self):
        self._sock.close()
        self._sock = None
        logging.debug('closed connection to camera application')
        
    def read_line(self):
        while True:
            p = self._recv_buf.find(b'\n')
            if p >= 0:
                line = self._recv_buf[:p]
                self._recv_buf = self._recv_buf[p+1:]
                return line
            d = self._sock.recv(4096)
            if not d:
                raise CameraError('Connection closed by server')
            self._recv_buf.extend(d)

    def read_bytes(self, n):
        while len(self._recv_buf) < n:
            d = self._sock.recv(n - len(self._recv_buf))
            if not d:
                raise CameraError('Connection closed by server')
            self._recv_buf.extend(d)
        data = self._recv_buf[:n]
        self._recv_buf = self._recv_buf[n:]
        return data

    def cmd(self, cmd):
        self._sock.sendall(cmd.encode('UTF-8') + b'\n')
        resp = self.read_line()
        if resp.startswith(b'ERR '):
            raise CameraError('Command failed: ' + resp[4:].decode('UTF-8', errors='replace'))
        if not resp.startswith(b'OK'):
            raise CameraError('Invalid response from server')

    def ask(self, cmd):
        self._sock.sendall(cmd.encode('UTF-8') + b'\n')
        resp = self.read_line()
        if resp.startswith(b'ERR '):
            raise CameraError('Command failed: ' + resp[4:].decode('UTF-8', errors='replace'))
        try:
            v = float(resp.strip())
        except ValueError:
            raise CameraError('Invalid response from server')
        return v

    def get_image(self):
        '''Retrieve the most recent image from the camera.

        Returns a tuple (image_data, meta_data)
            where image_data is a 2D numpy array containing pixel values;
                  meta_data is a numpy record containing image meta data.

        Note that calling this function repeatedly may cause the same
        image to be returned more than once.
        '''

        logging.debug('request image from camera application')
        self._sock.sendall(b'get_image\n')
        # Read image data.
        resp = self.read_line()
        if resp.startswith(b'ERR '):
            raise CameraError('Command failed: ' + resp[4:].decode('UTF-8', errors='replace'))
        try:
            n = int(resp.strip())
        except ValueError:
            raise CameraError('Invalid response from server')
        d1 = self.read_bytes(n)
        eol = self.read_bytes(1)
        if eol != b'\n':
            raise CameraError('Invalid response from server')
        # Read meta data.
        resp = self.read_line()
        try:
            n = int(resp.strip())
        except ValueError:
            raise CameraError('Invalid response from server')
        d2 = self.read_bytes(n)
        eol = self.read_bytes(1)
        if eol != b'\n':
            raise CameraError('Invalid response from server')
        image_data = np.loads(d1)
        meta_data = np.loads(d2)
        return (image_data, meta_data)

    def decode_meta_data(self, meta):
        '''decodes the image meta data'''
        meta_data = {'width': meta['width'],
             'height': meta['height'],
             'offset_x': meta['offset_x'],
             'offset_y': meta['offset_y'],
             'pixel_format': meta['pixel_format'].decode(),
             'frame_id': meta['frame_id'],
             'image_id': meta['image_id'],
             'timestamp': meta['timestamp'],
             'gain': meta['gain'],
             'black_level': meta['black_level'],
             'exposure_time': meta['exposure_time']}
        return meta_data
        
    def set_frame_rate(self, frame_rate):
        '''Set camera frame rate in frames/second.'''
        self.cmd('set_frame_rate {}'.format(frame_rate))
        logging.debug('set frame rate to {}'.format(frame_rate))

    def get_frame_rate(self):
        '''Return camera frame rate in frames/second.'''
        return self.ask('get_frame_rate')

    def set_exposure_time(self, exposure_time):
        '''Set exposure time in microseconds.'''
        self.cmd('set_exposure_time {}'.format(exposure_time))
        logging.debug('set exposure time to {} microsecond'.format(exposure_time))

    def get_exposure_time(self):
        '''Return exposure time in microseconds.'''
        return self.ask('get_exposure_time')

    def set_pixel_format(self, pixel_format):
        '''Set pixel data format. Valid values are 'Mono8' and 'Mono16'.'''
        self.cmd('set_pixel_format {}'.format(pixel_format))
        logging.debug('set pixel format to: {}'.format(pixel_format))

    def set_black_level(self, black_level):
        '''Set black level in percent.'''
        self.cmd('set_black_level {}'.format(black_level))
        logging.debug('set black level to: {}'.format(black_level))

    def get_black_level(self):
        '''Return black level in percent.'''
        return self.ask('get_black_level')

    def set_gain(self, gain):
        '''Set analog gain in dB.'''
        self.cmd('set_gain {}'.format(gain))
        logging.debug('set gain to {}'.format(gain))

    def get_gain(self):
        '''Return analog gain in dB.'''
        return self.ask('get_gain')

    def start_acquisition(self):
        '''Start streaming video acquisition.'''
        self.cmd('start_acquisition')
        logging.debug('start acquisition')

    def stop_acquisition(self):
        '''Stop streaming video acquisition.'''
        self.cmd('stop_acquisition')
        logging.debug('stopped acquisition')

class Camera():
    def __init__(self, camera_ini):
        libVer = PyCapture2.getLibraryVersion()
        logging.info('PyCapture2 library version: %d.%d.%d.%d' % (libVer[0], libVer[1], libVer[2], libVer[3]))
        self.connectCam()
        self.prepareSettings(camera_ini)

    def connectCam(self):
        self.bus = PyCapture2.BusManager()
        numCams = self.bus.getNumOfCameras()
        if numCams == 0:
            logging.error('camera not found')
            raise CameraError('camera not found')
        self._cam = PyCapture2.Camera()
        self.guid = self.bus.getCameraFromIndex(0)
        self._cam.connect(self.guid)
        time.sleep(0.1)
        self._cameraInfo = self._cam.getCameraInfo()
        if self._cameraInfo.sensorResolution:
            self._cameraInfo.resolution = [ int(a) for a in self._cameraInfo.sensorResolution.decode().split('x') ]
        for line in str(self._formatStorageClass(self._cameraInfo)).splitlines():
            logging.info(line)
        
        # preparing image statistics calculation
        self._imgStats = PyCapture2.ImageStatistics()
        self._imgStats.enableGreyChannel()

        logging.info('camera connected')
        
    def prepareSettings(self, camera_ini):
        self.camera_ini = camera_ini
        if camera_ini['nrBits'] == 8:
            pixelFormat = PyCapture2.PIXEL_FORMAT.MONO8
        elif camera_ini['nrBits'] == 16:
            pixelFormat = PyCapture2.PIXEL_FORMAT.MONO16
        else:
            logging.error('invalid or unsupporte nr of bits per pixel given in .ini file')
            raise CameraError('invalid or unsupporte nr of bits per pixel given in .ini file')

        logging.debug('disabling all properties which can be set to \'auto\'')
        for item in dir(PyCapture2.PROPERTY_TYPE):
            propType = getattr(PyCapture2.PROPERTY_TYPE, item)
            if propType > 16:
                break
            prop = self._cam.getProperty(propType)
            if not prop.present:
                break
            if prop.autoManualMode:
                logging.debug('setting property %s to manual' % item)
                prop.autoManualMode = False
                self._cam.setProperty(prop)
                time.sleep(0.1)
                logging.debug('auto setting of %s set to %s' % (item, str(self._cam.getProperty(propType).autoManualMode)))
        
        propType = PyCapture2.PROPERTY_TYPE.SHARPNESS
        prop = self._cam.getProperty(propType)
        prop.absValue = camera_ini['sharpness']
        self._cam.setProperty(prop)
        time.sleep(0.1)
        logging.info('sharpness set to: %d' % self._cam.getProperty(propType).absValue)
        
        propType = PyCapture2.PROPERTY_TYPE.FRAME_RATE
        prop = self._cam.getProperty(propType)
        prop.absValue = camera_ini['framerate']
        self._cam.setProperty(prop)
        time.sleep(0.1)
        logging.info('framerate set to: %.3f Hz' % self._cam.getProperty(propType).absValue)

        logging.info('set gain to zero and integration time to %.3f ms' % camera_ini['integrationTime'])
        integrationTime = self.setShutter(camera_ini['integrationTime'])
        deviation = (integrationTime - camera_ini['integrationTime'])/integrationTime
        if deviation > 0.1:
            msg = 'set integration time deviates more than 10% from desired value!'
            print(msg)
            logging.warning(msg)
        propType = PyCapture2.PROPERTY_TYPE.GAIN
        prop = self._cam.getProperty(propType)
        prop.absValue = 0
        self._cam.setProperty(prop)
        time.sleep(0.1)
        logging.debug('gain is now: %.3f dB and integration time is now %.3f ms' % (self._cam.getProperty(propType).absValue, integrationTime))
        
        # setting FORMAT7 mode and ROI
        (fm7Info, supported)= self._cam.getFormat7Info(camera_ini['fm7Mode'])
        if not supported:
            msg = 'invalid mode7: %d' % camera_ini['fm7Mode']
            logging.error(msg)
            raise CameraError(msg)
        self.fm7Settings = PyCapture2.Format7ImageSettings(camera_ini['fm7Mode'], \
                                                     camera_ini['roi'][0], \
                                                     camera_ini['roi'][1], \
                                                     camera_ini['roi'][2], \
                                                     camera_ini['roi'][3], \
                                                     pixelFormat)
        (fm7PacketInfo, isValid) = self._cam.validateFormat7Settings(self.fm7Settings)
        if isValid:
            for line in str(self._formatStorageClass(fm7PacketInfo)).splitlines():
                logging.info(line)
        else:
            print('invalid image settings, make sure that image offsetX and \
            offsetY and width and height are the correct \
            multiples!! (%d, %d, %d and %d respectively)' %\
                                  (fm7Info.offsetHStepSize, 
                                  fm7Info.offsetVStepSize, 
                                  fm7Info.imageHStepSize, 
                                  fm7Info.imageVStepSize))
            logging.error('invalid image settings')
            raise CameraError('invalid image settings')
            
        self._cam.setFormat7ConfigurationPacket(fm7PacketInfo.recommendedBytesPerPacket, self.fm7Settings)
        # logging.debug('format7 settings: %s' % formatter(fm7Settings))
        # logging.debug('format7 packet info: %s' % formatter(fm7PacketInfo))
        logging.debug('Camera settings are set')

    def getStats(self):
        statistics = self._cam.getStats()
        stats = {'cameraCurrents': statistics.cameraCurrents, \
        'cameraPowerUp': statistics.cameraPowerUp, \
        'cameraVoltages': statistics.cameraVoltages, \
        'imageCorrupt': statistics.imageCorrupt, \
        'imageDriverDropped': statistics.imageDriverDropped, \
        'imageDropped': statistics.imageDropped, \
        'imageXmitFailed': statistics.imageXmitFailed, \
        'numResendPacketsReceived': statistics.numResendPacketsReceived, \
        'numResendPacketsRequested': statistics.numResendPacketsRequested, \
        'portErrors': statistics.portErrors, \
        'regReadFailed': statistics.regReadFailed, \
        'regWriteFailed': statistics.regWriteFailed, \
        'temperature': statistics.temperature/10-273.1, \
        'timeSinceBusReset': statistics.timeSinceBusReset, \
        'timeSinceInitialization': statistics.timeSinceInitialization, \
        'timeStamp': statistics.timeStamp}
        return stats
                        
    def getTemperature(self):
        tempK = self._cam.getProperty(PyCapture2.PROPERTY_TYPE.TEMPERATURE).absValue * 100
        tempC = tempK - 273.1
        return tempC
        
    def setShutter(self, integrationTime):
        propType = PyCapture2.PROPERTY_TYPE.SHUTTER
        prop = self._cam.getProperty(propType)
        prop.absValue = integrationTime
        self._cam.setProperty(prop)
        time.sleep(0.1)
        actualIntegrationTime = self._cam.getProperty(propType).absValue
        logging.info('integration time is now: %.3f ms' % actualIntegrationTime)
        return actualIntegrationTime
    
    def startCapture(self):
        self._cam.startCapture()
        logging.debug('started camera acquistion')

    def stopCapture(self):
        self._cam.stopCapture()
        logging.debug('stopped camera acquistion')

    def close(self):
        self._cam.disconnect()
        del self._cam
        del self.bus
        del self.guid
        logging.info('disconnected camera and unloaded damera dll')

    def retrieveBuffer(self):
        image = self._cam.retrieveBuffer()
        logging.debug('read image from buffer')
        return image

    def getImageData(self, image):
        pxFormat = image.getPixelFormat()
        if pxFormat == PyCapture2.PIXEL_FORMAT.MONO8:
            dtype = np.int8
        elif pxFormat == PyCapture2.PIXEL_FORMAT.MONO16:
            dtype = np.int16
        else:
            format = self._pixelFormat(pxFormat)
            msg = 'unsupported image format: %s' % format
            logging.error(msg)
            raise CameraError(msg)
        byteData = np.fromstring(bytes(image.getData()), dtype=dtype) 
        array = byteData.reshape([image.getRows(), image.getCols()])
        return array
        
    def getImageTimestamp(self, image):
        ts = image.getTimeStamp()
        tm = ts.seconds + (ts.microSeconds/1E6)
        # include conversion to useful timestamp format?
        return tm
    
    def getImageStatistics(self, image):
        self._imgStats.calculateStatistics(image)
        ((rangeMin, rangeMax), (pixValMin, pixValMax), numPixVals, pixValMean, histogram) = self._imgStats.getStatistics(PyCapture2.STATISTICS_CHANNEL.GREY)

        statistics = {'range': (rangeMin, rangeMax), \
        'pixVal': (pixValMin, pixValMax), 'numPixVals': numPixVals, \
        'pixValMean': pixValMean, 'histogram': histogram}
        return statistics

    def _getFormat7Configuration(self):
        (fm7IS, packetSize, percentage) = self._cam.getFormat7Configuration()
        percentage = float(percentage)
        settings = {'mode ': int(fm7IS.mode), 'offsetX':int(fm7IS.offsetX), \
        'offsetY':int(fm7IS.offsetY), 'width':int(fm7IS.width), \
        'height':int(fm7IS.height), 'pixelFormat':self._pixelFormat(fm7IS.pixelFormat)}
        return (settings, packetSize, percentage)
        
    def _pixelFormat(self, pxFormat):
        for format in dir(PyCapture2.PIXEL_FORMAT):
            if getattr(PyCapture2.PIXEL_FORMAT, format) == pxFormat:
                return format
            else:
                pass
        msg = 'unknown pixel format: %d' % pxFormat
        logging.error(msg)
        raise CameraError(msg)

    def _formatStorageClass(self, infoStruct):
        '''Function returns a textual output of the contents of a PyCapture 
        storage class useful for . It is not interpreting the contents so be
        careful...'''
        msg = ''
        for item in dir(infoStruct):
            if not item[0:2] == '__':
                msg = msg + (item + ': ' + str(getattr(infoStruct, item)) + '\n')
        return msg
        