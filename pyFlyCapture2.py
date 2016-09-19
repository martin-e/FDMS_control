# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 15:36:01 2016

@author: eschenm
supporting module with all used structure type definitions and supporting 
functions
"""

import ctypes
from enum import Enum

FULL_32BIT_VALUE = 0x7FFFFFFF
MAX_STRING_LENGTH = 512

class FlyCaptureError(StandardError):
    pass

class FC2Struct(ctypes.Structure):
    def clone(self):
        clone = type(self)()
        ctypes.pointer(clone)[0] = self
        return clone

class VersionStruct(FC2Struct):
    _fields_ = [('major', ctypes.c_uint),
        ('minor', ctypes.c_uint),
        ('libtype', ctypes.c_uint),
        ('build', ctypes.c_uint)]
        
class ImageStruct(FC2Struct):
    _fields_ = [('rows', ctypes.c_uint),
        ('cols', ctypes.c_uint),
        ('stride', ctypes.c_uint),
        ('pData', ctypes.POINTER(ctypes.c_ubyte)),
        ('dataSize', ctypes.c_uint),
        ('receivedDataSize', ctypes.c_uint),
        ('pixFormat', ctypes.c_uint),
        ('bayerFormat', ctypes.c_int),
        ('imageImpl', ctypes.c_void_p),]
    def __str__(self):
        rtxt = ("image data structure:\n\t%dx%d rows x cols\n" % (self.cols, self.rows))
        rtxt = rtxt + ("\tstride: %d\n" % self.stride)
        rtxt = rtxt + ("\tdata size: %d\n" % self.dataSize)
        rtxt = rtxt + ("\treceived data size: %d\n" % self.receivedDataSize)
        rtxt = rtxt + ("\tpixel format: %s\n" % fc2PixelFormat(self.pixFormat).name)
        rtxt = rtxt + ("\tbayer tile format: %s\n" % self.bayerFormat)
        return rtxt

class ConfigROMStruct(FC2Struct):
    _fields_ = [('nodeVendorId', ctypes.c_uint),
                ('chipIdHi', ctypes.c_uint),
                ('chipIdLo', ctypes.c_uint),
                ('unitSpecId', ctypes.c_uint),
                ('unitSWVer', ctypes.c_uint),
                ('unitSubSWVer', ctypes.c_uint),
                ('vendorUniqueInfo_0', ctypes.c_uint),
                ('vendorUniqueInfo_1', ctypes.c_uint),
                ('vendorUniqueInfo_2', ctypes.c_uint),
                ('vendorUniqueInfo_3', ctypes.c_uint),
                ('pszKeyword', ctypes.c_char*512),
                ('reserved', ctypes.c_uint*16)]
 
class MACAddressStruct(FC2Struct):
    _fields_ = [('octets', ctypes.c_ubyte*6)]

class IPAddressStruct(FC2Struct):
    _fields_ = [('octets', ctypes.c_ubyte*4)]

class CameraInfoStruct(FC2Struct):
    _fields_ = [('serialNumber', ctypes.c_uint),
                ('interfaceType', ctypes.c_long),
                ('driverType', ctypes.c_int),
                ('isColorCamera', ctypes.c_long),  # defined as BOOL in c_struct
                ('modelName', ctypes.c_char*512),
                ('vendorName', ctypes.c_char*512),
                ('sensorInfo', ctypes.c_char*512),
                ('sensorResolution', ctypes.c_char*512),
                ('driverName', ctypes.c_char*512),
                ('firmwareVersion', ctypes.c_char*512),
                ('firmwareBuildTime', ctypes.c_char*512),
                ('maximumBusSpeed', ctypes.c_int),
                ('bayerTileFormat', ctypes.c_int),
                ('pcieBusSpeed', ctypes.c_int),
                ('nodeNumber', ctypes.c_ushort),
                ('busNumber', ctypes.c_ushort),
                ('iidcVer', ctypes.c_uint),
                ('configROM', ConfigROMStruct),
                ('gigEMajorVersion', ctypes.c_uint),
                ('gigEMinorVersion', ctypes.c_uint),
                ('userDefinedName', ctypes.c_char*512),
                ('xmlURL1', ctypes.c_char*512),
                ('xmlURL2', ctypes.c_char*512),
                ('macAddress', MACAddressStruct),
                ('ipAddress', IPAddressStruct),
                ('subnetMask', IPAddressStruct),
                ('defaultGateway', IPAddressStruct),
                ('ccpStatus', ctypes.c_uint),
                ('applicationPort', ctypes.c_uint),
                ('reserved', ctypes.c_uint*16)]
    def __str__(self):
        rtxt = "Camera info:\n"
        rtxt = rtxt + ("\tmodel: %s\n" % self.modelName)
        rtxt = rtxt + ("\tserial number: %d\n" % int(self.serialNumber))
        rtxt = rtxt + ("\tfirmware version: %s\n" % self.firmwareVersion)
        rtxt = rtxt + ("\tmonochrome camera? %s\n" % ('yes' if not bool(self.isColorCamera) else 'no'))
        rtxt = rtxt + "Sensor info:\n"
        rtxt = rtxt + ("\ttype: %s\n" % self.sensorInfo)
        rtxt = rtxt + ("\tresolution: %s\n" % self.sensorResolution)
        return rtxt

class TimeStampStruct(FC2Struct):
    _fields_ = [('seconds',ctypes.c_longlong),
                ('microSeconds', ctypes.c_uint),
                ('cycleSeconds', ctypes.c_uint),
                ('cycleCount', ctypes.c_uint),
                ('cycleOffset', ctypes.c_uint),
                ('reserved', ctypes.c_uint *8)]
    def __str__(self):
        return time.strftime('%Y%m%d %H%M%S', time.localtime(ts.seconds))

class CameraStatsStruct(FC2Struct):
    _fields_ = [('imageDropped', ctypes.c_uint),
                ('imageCorrupt', ctypes.c_uint),
                ('imageXmitFailed', ctypes.c_uint),
                ('imageDriverDropped', ctypes.c_uint),
                ('regReadFailed', ctypes.c_uint),
                ('regWriteFailed', ctypes.c_uint),
                ('portErrors', ctypes.c_uint),
                ('cameraPowerUp', ctypes.c_bool),
                ('cameraVoltages', ctypes.c_float*8),
                ('numVoltages', ctypes.c_uint),
                ('cameraCurrents', ctypes.c_float*8),
                ('numCurrents', ctypes.c_uint),
                ('temperature', ctypes.c_uint),
                ('timeSinceInitialization', ctypes.c_uint),
                ('timeSinceBusReset', ctypes.c_uint),
                ('timeStamp', TimeStampStruct),
                ('numResendPacketsRequested', ctypes.c_uint),
                ('numResendPacketsReceived', ctypes.c_uint),
                ('reserved', ctypes.c_uint*16)]
    def __str__(self):
        rtxt = "Statistics:\n"
        rtxt = rtxt + ("\tcamera powered on: %s\n" % (self.cameraPowerUp))
        rtxt = rtxt + ("\ttemperature: %.1f degC\n" % (self.temperature/10 - 273.2))
        rtxt = rtxt + ("\tSeconds since initialisation: %d\n" % (self.timeSinceInitialization))
        for idx in range(self.numVoltages):
            rtxt = rtxt + ("\tCamera voltage %d: %.3f V\n" % (idx, (self.cameraVoltages[idx])))
        for idx in range(self.numCurrents):
            rtxt = rtxt + ("\tCamera current %d: %.3f A\n" % (idx, (self.cameraCurrents[idx])))
        return rtxt

# /** Format 7 image settings. */
class Format7ImageSettingsStruct(FC2Struct):
    _fields_ = [('mode', ctypes.c_int),
                ('offsetX', ctypes.c_uint),
                ('offsetY', ctypes.c_uint),
                ('width', ctypes.c_uint),
                ('height', ctypes.c_uint),
                ('pixelFormat', ctypes.c_uint),
                ('reserved', ctypes.c_uint *8)]
    def __str__(self):
        rtxt = ("FORMAT7 image settings:\n")
        rtxt = rtxt + ("\tmode: %d\n" % self.mode)
        rtxt = rtxt + ("\tsize: %dx%d (WxH)\n" % (self.width, self.height))
        rtxt = rtxt + ("\toffset: %dx%d (XxY)\n" % (self.offsetX, self.offsetY))
        rtxt = rtxt + ("\tpixel format: %s\n" % fc2PixelFormat(self.pixelFormat).name)
        return rtxt

# /** Format 7 information for a single mode. */
class Format7InfoStruct(FC2Struct):
    _fields_ = [('mode', ctypes.c_uint),
                ('maxWidth', ctypes.c_uint),
                ('maxHeight', ctypes.c_uint),
                ('offsetHStepSize', ctypes.c_uint),
                ('offsetVStepSize', ctypes.c_uint),
                ('imageHStepSize', ctypes.c_uint),
                ('imageVStepSize', ctypes.c_uint),
                ('pixelFormatBitField', ctypes.c_uint),
                ('vendorPixelFormatBitField', ctypes.c_uint),
                ('packetSize', ctypes.c_uint),
                ('minPacketSize', ctypes.c_uint),
                ('maxPacketSize', ctypes.c_uint),
                ('percentage', ctypes.c_float),
                ('reserved', ctypes.c_uint *8)]
    def __str__(self):
        rtxt = ("FORMAT7 mode %s info:\n" % self.mode)
        rtxt = rtxt + ("\tsize: %dx%d (WxH)\n" % (self.maxWidth, self.maxHeight))
        rtxt = rtxt + ("\toffset step size: %dx%d (HxV)\n" % (self.offsetHStepSize, self.offsetVStepSize))
        rtxt = rtxt + ("\timage step size: %dx%d (HxV)\n" % (self.imageHStepSize, self.imageVStepSize))
        rtxt = rtxt + ("\tpixelFormatBitField: %0x\n" % self.pixelFormatBitField)
        rtxt = rtxt + ("\tpacketSize: %d (%.1f%%)\n" % (self.packetSize, self.percentage))
        rtxt = rtxt + ("\t\tminPacketSize: %d\n" % self.minPacketSize)
        rtxt = rtxt + ("\t\tmaxPacketSize: %d\n" % self.maxPacketSize)
        return rtxt

# /** Format 7 packet information. */
class Format7PacketInfoStruct(FC2Struct):
    _fields_ = [('recommendedBytesPerPacket', ctypes.c_uint),
                ('maxBytesPerPacket', ctypes.c_uint),
                ('unitBytesPerPacket', ctypes.c_uint),
                ('reserved', ctypes.c_uint *8)]
    def __str__(self):
        rtxt = ("Format7PacketInfo:\n")
        rtxt = rtxt + ("\trecommendedBytesPerPacket: %d\n" % self.recommendedBytesPerPacket)
        rtxt = rtxt + ("\tmaxBytesPerPacket: %d\n" % self.maxBytesPerPacket)
        rtxt = rtxt + ("\tunitBytesPerPacket: %d\n" % self.unitBytesPerPacket)
        return rtxt                

# /** The error types returned by functions. */
class fc2Error(Enum):
    FC2_ERROR_UNDEFINED = -1
    FC2_ERROR_OK = 0
    FC2_ERROR_FAILED = 1
    FC2_ERROR_NOT_IMPLEMENTED = 2
    FC2_ERROR_FAILED_BUS_MASTER_CONNECTION = 3
    FC2_ERROR_NOT_CONNECTED = 4
    FC2_ERROR_INIT_FAILED = 5
    FC2_ERROR_NOT_INTITIALIZED = 6
    FC2_ERROR_INVALID_PARAMETER = 7
    FC2_ERROR_INVALID_SETTINGS = 8
    FC2_ERROR_INVALID_BUS_MANAGER = 9
    FC2_ERROR_MEMORY_ALLOCATION_FAILED = 10
    FC2_ERROR_LOW_LEVEL_FAILURE = 11
    FC2_ERROR_NOT_FOUND = 12
    FC2_ERROR_FAILED_GUID = 13
    FC2_ERROR_INVALID_PACKET_SIZE = 14
    FC2_ERROR_INVALID_MODE = 15
    FC2_ERROR_NOT_IN_FORMAT7 = 16
    FC2_ERROR_NOT_SUPPORTED = 17
    FC2_ERROR_TIMEOUT = 18
    FC2_ERROR_BUS_MASTER_FAILED = 19
    FC2_ERROR_INVALID_GENERATION = 20
    FC2_ERROR_LUT_FAILED = 21
    FC2_ERROR_IIDC_FAILED = 22
    FC2_ERROR_STROBE_FAILED = 23
    FC2_ERROR_TRIGGER_FAILED = 24
    FC2_ERROR_PROPERTY_FAILED = 25
    FC2_ERROR_PROPERTY_NOT_PRESENT = 26
    FC2_ERROR_REGISTER_FAILED = 27
    FC2_ERROR_READ_REGISTER_FAILED = 28
    FC2_ERROR_WRITE_REGISTER_FAILED = 29
    FC2_ERROR_ISOCH_FAILED = 30
    FC2_ERROR_ISOCH_ALREADY_STARTED = 31
    FC2_ERROR_ISOCH_NOT_STARTED = 32
    FC2_ERROR_ISOCH_START_FAILED = 33
    FC2_ERROR_ISOCH_RETRIEVE_BUFFER_FAILED = 34
    FC2_ERROR_ISOCH_STOP_FAILED = 35
    FC2_ERROR_ISOCH_SYNC_FAILED = 36
    FC2_ERROR_ISOCH_BANDWIDTH_EXCEEDED = 37
    FC2_ERROR_IMAGE_CONVERSION_FAILED = 38
    FC2_ERROR_IMAGE_LIBRARY_FAILURE = 39
    FC2_ERROR_BUFFER_TOO_SMALL = 40
    FC2_ERROR_IMAGE_CONSISTENCY_ERROR = 41
    FC2_ERROR_INCOMPATIBLE_DRIVER = 42
    FC2_ERROR_FORCE_32BITS = FULL_32BIT_VALUE

#    /** The type of bus callback to register a callback function for. */
class fc2BusCallbackType(Enum):
    FC2_BUS_RESET = 0 #/**< Register for all bus events. */
    FC2_ARRIVAL = 1   #/**< Register for arrivals only. */
    FC2_REMOVAL = 2   #/**< Register for removals only. */
    FC2_CALLBACK_TYPE_FORCE_32BITS = FULL_32BIT_VALUE

#    /** The grab strategy employed during image transfer. This type controls
#     * how images that stream off the camera accumulate in a user buffer
#     * for handling.
class fc2GrabMode(Enum):
    FC2_DROP_FRAMES = 0  # * Grabs the newest image
    FC2_BUFFER_FRAMES = 1 #* Images accumulate, oldest is grabbed 
    FC2_UNSPECIFIED_GRAB_MODE = 2
    FC2_GRAB_MODE_FORCE_32BITS = FULL_32BIT_VALUE

#    /** Timeout options for grabbing images. */
class fc2GrabTimeout(Enum):
    FC2_TIMEOUT_NONE = 0         #/**< Non-blocking wait. */
    FC2_TIMEOUT_INFINITE = -1    #/**< Wait indefinitely. */
    FC2_TIMEOUT_UNSPECIFIED = -2 #/**< Unspecified timeout setting. */
    FC2_GRAB_TIMEOUT_FORCE_32BITS = FULL_32BIT_VALUE

# /** Bandwidth allocation options for 1394 devices. */
class fc2BandwidthAllocation(Enum):
    FC2_BANDWIDTH_ALLOCATION_OFF = 0
    FC2_BANDWIDTH_ALLOCATION_ON = 1    # default setting
    FC2_BANDWIDTH_ALLOCATION_UNSUPPORTED = 2
    FC2_BANDWIDTH_ALLOCATION_UNSPECIFIED = 3
    FC2_BANDWIDTH_ALLOCATION_FORCE_32BITS = FULL_32BIT_VALUE

#    /** Interfaces that a camera may use to communicate with a host. */
class fc2InterfaceType(Enum):
    FC2_INTERFACE_IEEE1394 = 0
    FC2_INTERFACE_USB_2 = 1
    FC2_INTERFACE_USB_3 = 2
    FC2_INTERFACE_GIGE = 3
    FC2_INTERFACE_UNKNOWN = 4
    FC2_INTERFACE_TYPE_FORCE_32BITS = FULL_32BIT_VALUE

#     * Camera properties. Not all properties may be supported, depending
#     * on the camera model.
class fc2PropertyType(Enum):
    FC2_BRIGHTNESS = 0
    FC2_AUTO_EXPOSURE = 1
    FC2_SHARPNESS = 2
    FC2_WHITE_BALANCE = 3
    FC2_HUE = 4
    FC2_SATURATION = 5
    FC2_GAMMA = 6
    FC2_IRIS = 7
    FC2_FOCUS = 8
    FC2_ZOOM = 9
    FC2_PAN = 10
    FC2_TILT = 11
    FC2_SHUTTER = 12
    FC2_GAIN = 13
    FC2_TRIGGER_MODE = 14
    FC2_TRIGGER_DELAY = 15
    FC2_FRAME_RATE = 16
    FC2_TEMPERATURE = 17
    FC2_UNSPECIFIED_PROPERTY_TYPE = 18
    FC2_PROPERTY_TYPE_FORCE_32BITS = FULL_32BIT_VALUE

#    /** Frame rates in frames per second. */
class fc2FrameRate(Enum):
    FC2_FRAMERATE_1_875 = 0
    FC2_FRAMERATE_3_75 = 1
    FC2_FRAMERATE_7_5 = 2
    FC2_FRAMERATE_15 = 3
    FC2_FRAMERATE_30 = 4
    FC2_FRAMERATE_60 = 5
    FC2_FRAMERATE_120 = 6
    FC2_FRAMERATE_240 = 7
    FC2_FRAMERATE_FORMAT7 = 8
    FC2_NUM_FRAMERATES = 9
    FC2_FRAMERATE_FORCE_32BITS = FULL_32BIT_VALUE

#    /** DCAM video modes. */
class fc2VideoMode(Enum):
    FC2_VIDEOMODE_160x120YUV444 = 0
    FC2_VIDEOMODE_320x240YUV422 = 1
    FC2_VIDEOMODE_640x480YUV411 = 2
    FC2_VIDEOMODE_640x480YUV422 = 3
    FC2_VIDEOMODE_640x480RGB = 4
    FC2_VIDEOMODE_640x480Y8 = 5
    FC2_VIDEOMODE_640x480Y16 = 6
    FC2_VIDEOMODE_800x600YUV422 = 7
    FC2_VIDEOMODE_800x600RGB = 8
    FC2_VIDEOMODE_800x600Y8 = 9
    FC2_VIDEOMODE_800x600Y16 = 10
    FC2_VIDEOMODE_1024x768YUV422 = 11
    FC2_VIDEOMODE_1024x768RGB = 12
    FC2_VIDEOMODE_1024x768Y8 = 13
    FC2_VIDEOMODE_1024x768Y16 = 14
    FC2_VIDEOMODE_1280x960YUV422 = 15
    FC2_VIDEOMODE_1280x960RGB = 16
    FC2_VIDEOMODE_1280x960Y8 = 17
    FC2_VIDEOMODE_1280x960Y16 = 18
    FC2_VIDEOMODE_1600x1200YUV422 = 19
    FC2_VIDEOMODE_1600x1200RGB = 20
    FC2_VIDEOMODE_1600x1200Y8 = 21
    FC2_VIDEOMODE_1600x1200Y16 = 22
    FC2_VIDEOMODE_FORMAT7 = 23
    FC2_NUM_VIDEOMODES = 24
    FC2_VIDEOMODE_FORCE_32BITS = FULL_32BIT_VALUE

#    /** Camera modes for DCAM formats as well as Format7. */
class fc2Mode(Enum):
    FC2_MODE_0 = 0
    FC2_MODE_1 = 1
    FC2_MODE_2 = 2
    FC2_MODE_3 = 3
    FC2_MODE_4 = 4
    FC2_MODE_5 = 5
    FC2_MODE_6 = 6
    FC2_MODE_7 = 7
    FC2_MODE_8 = 8
    FC2_MODE_9 = 9
    FC2_MODE_10 = 10
    FC2_MODE_11 = 11
    FC2_MODE_12 = 12
    FC2_MODE_13 = 13
    FC2_MODE_14 = 14
    FC2_MODE_15 = 15
    FC2_MODE_16 = 16
    FC2_MODE_17 = 17
    FC2_MODE_18 = 18
    FC2_MODE_19 = 19
    FC2_MODE_20 = 20
    FC2_MODE_21 = 21
    FC2_MODE_22 = 22
    FC2_MODE_23 = 23
    FC2_MODE_24 = 24
    FC2_MODE_25 = 25
    FC2_MODE_26 = 26
    FC2_MODE_27 = 27
    FC2_MODE_28 = 28
    FC2_MODE_29 = 29
    FC2_MODE_30 = 30
    FC2_MODE_31 = 31
    FC2_NUM_MODES = 32
    FC2_MODE_FORCE_32BITS = FULL_32BIT_VALUE

#    /** Pixel formats available for Format7 modes. */
class fc2PixelFormat(Enum):
    FC2_PIXEL_FORMAT_MONO8          = 0x80000000
    FC2_PIXEL_FORMAT_411YUV8        = 0x40000000
    FC2_PIXEL_FORMAT_422YUV8        = 0x20000000
    FC2_PIXEL_FORMAT_444YUV8        = 0x10000000
    FC2_PIXEL_FORMAT_RGB8           = 0x08000000
    FC2_PIXEL_FORMAT_MONO16         = 0x04000000
    FC2_PIXEL_FORMAT_RGB16          = 0x02000000
    FC2_PIXEL_FORMAT_S_MONO16       = 0x01000000
    FC2_PIXEL_FORMAT_S_RGB16        = 0x00800000
    FC2_PIXEL_FORMAT_RAW8           = 0x00400000
    FC2_PIXEL_FORMAT_RAW16          = 0x00200000
    FC2_PIXEL_FORMAT_MONO12         = 0x00100000
    FC2_PIXEL_FORMAT_RAW12          = 0x00080000
    FC2_PIXEL_FORMAT_BGR            = 0x80000008
    FC2_PIXEL_FORMAT_BGRU           = 0x40000008
    FC2_PIXEL_FORMAT_RGB            = 0x08000000
    FC2_PIXEL_FORMAT_RGBU           = 0x40000002
    FC2_PIXEL_FORMAT_BGR16          = 0x02000001
    FC2_PIXEL_FORMAT_BGRU16         = 0x02000002
    FC2_PIXEL_FORMAT_422YUV8_JPEG   = 0x40000001 # JPEG compressed stream
    FC2_NUM_PIXEL_FORMATS           = 20
    FC2_UNSPECIFIED_PIXEL_FORMAT    = 0

#    /** Bus speeds. */
class fc2BusSpeed(Enum):
    FC2_BUSSPEED_S100 = 0 # 100Mbits/sec. */
    FC2_BUSSPEED_S200 = 1 # 200Mbits/sec. */
    FC2_BUSSPEED_S400 = 2 #  400Mbits/sec. */
    FC2_BUSSPEED_S480 = 3 # 480Mbits/sec. Only for USB2 cameras. */
    FC2_BUSSPEED_S800 = 4 # 800Mbits/sec. */
    FC2_BUSSPEED_S1600 = 5 #  1600Mbits/sec. */
    FC2_BUSSPEED_S3200 = 6 # 3200Mbits/sec. */
    FC2_BUSSPEED_S5000 = 7 # 5000Mbits/sec. Only for USB3 cameras. */
    FC2_BUSSPEED_10BASE_T = 8 # /**< 10Base-T. Only for GigE cameras. */
    FC2_BUSSPEED_100BASE_T = 9 # 100Base-T.  Only for GigE cameras.*/
    FC2_BUSSPEED_1000BASE_T = 10 # 1000Base-T (Gigabit Ethernet).  Only for GigE cameras. */
    FC2_BUSSPEED_10000BASE_T = 11 # 10000Base-T.  Only for GigE cameras. */
    FC2_BUSSPEED_S_FASTEST = 12 # The fastest speed available. */
    FC2_BUSSPEED_ANY = 13 # Any speed that is available. */
    FC2_BUSSPEED_SPEED_UNKNOWN = -1
    FC2_BUSSPEED_FORCE_32BITS = FULL_32BIT_VALUE

class fc2PCIeBusSpeed(Enum):
    FC2_PCIE_BUSSPEED_2_5 = 0
    FC2_PCIE_BUSSPEED_5_0 = 1
    FC2_PCIE_BUSSPEED_UNKNOWN = -1
    FC2_PCIE_BUSSPEED_FORCE_32BITS = FULL_32BIT_VALUE
    
#    /** Types of low level drivers that FlyCapture uses. */
class fc2DriverType(Enum):
    FC2_DRIVER_1394_CAM = 0 # /**< PGRCam.sys. */
    FC2_DRIVER_1394_PRO = 1 # /**< PGR1394.sys. */
    FC2_DRIVER_1394_JUJU = 2 # /**< firewire_core. */
    FC2_DRIVER_1394_VIDEO1394 = 3 # /**< video1394. */
    FC2_DRIVER_1394_RAW1394 = 4 # /**< raw1394. */
    FC2_DRIVER_USB_NONE = 5 # /**< No usb driver used just BSD stack. (Linux only) */
    FC2_DRIVER_USB_CAM = 6 # /**< PGRUsbCam.sys. */
    FC2_DRIVER_USB3_PRO = 7 # /**< PGRXHCI.sys. */
    FC2_DRIVER_GIGE_NONE = 8 # /**< no GigE drivers used, MS/BSD stack. */
    FC2_DRIVER_GIGE_FILTER = 9 # /**< PGRGigE.sys. */
    FC2_DRIVER_GIGE_PRO = 10 #  /**< PGRGigEPro.sys. */
    FC2_DRIVER_GIGE_LWF = 11 # /**< PgrLwf.sys. */
    FC2_DRIVER_UNKNOWN = -1
    FC2_DRIVER_FORCE_32BITS = FULL_32BIT_VALUE

#     * Color processing algorithms. Please refer to our knowledge base at
#     * article at http://www.ptgrey.com/support/kb/index.asp?a=4&q=33 for
#     * complete details for each algorithm.
class fc2ColorProcessingAlgorithm(Enum):
    FC2_DEFAULT = 0
    FC2_NO_COLOR_PROCESSING = 1
    FC2_NEAREST_NEIGHBOR_FAST = 2 # Fastest but lowest quality
    FC2_EDGE_SENSING = 3 #  Weights surrounding pixels based on localized edge orientation. */
    FC2_HQ_LINEAR = 4  #    Well-balanced speed and quality. */
    FC2_RIGOROUS = 5   #    Slowest but produces good results.
    FC2_IPP = 6 #           Multithreaded with similar results to edge sensing.
    FC2_DIRECTIONAL = 7 #   Best quality but much faster than rigorous.
    FC2_COLOR_PROCESSING_ALGORITHM_FORCE_32BITS = FULL_32BIT_VALUE
    
#    /** Bayer tile formats. */
class fc2BayerTileFormat(Enum):
    FC2_BT_NONE = 0
    FC2_BT_RGGB = 1
    FC2_BT_GRBG = 2
    FC2_BT_GBRG = 3
    FC2_BT_BGGR = 4
    FC2_BT_FORCE_32BITS = FULL_32BIT_VALUE

#    /** File formats to be used for saving images to disk. */
class fc2ImageFileFormat(Enum):
    FC2_FROM_FILE_EXT = -1 #Determine file format from file extension
    FC2_PGM = 0
    FC2_PPM = 1
    FC2_BMP = 2
    FC2_JPEG = 3
    FC2_JPEG2000 = 4
    FC2_TIFF = 5
    FC2_PNG = 6
    FC2_RAW = 7
    FC2_IMAGE_FILE_FORMAT_FORCE_32BITS = FULL_32BIT_VALUE

class fc2GigEPropertyType(Enum):
    FC2_HEARTBEAT = 0
    FC2_HEARTBEAT_TIMEOUT =  1
    PACKET_SIZE = 2
    PACKET_DELAY = 3

#     * Channels that allow statistics to be calculated.
class fc2StatisticsChannel(Enum):
    FC2_STATISTICS_GREY = 0
    FC2_STATISTICS_RED = 1
    FC2_STATISTICS_GREEN = 2
    FC2_STATISTICS_BLUE = 3
    FC2_STATISTICS_HUE = 4
    FC2_STATISTICS_SATURATION = 5
    FC2_STATISTICS_LIGHTNESS = 6
    FC2_STATISTICS_FORCE_32BITS = FULL_32BIT_VALUE

#    /** Possible operating systems. */
class fc2OSType(Enum):
    FC2_WINDOWS_X86 = 0 # /**< All Windows 32-bit variants. */
    FC2_WINDOWS_X64 = 1 # /**< All Windows 64-bit variants. */
    FC2_LINUX_X86 = 2 # /**< All Linux 32-bit variants. */
    FC2_LINUX_X64 = 3 # /**< All Linux 32-bit variants. */
    FC2_MAC = 4 # /**< Mac OSX. */
    FC2_UNKNOWN_OS = 5 # /**< Unknown operating system. */
    FC2_OSTYPE_FORCE_32BITS = FULL_32BIT_VALUE

#    /** Possible byte orders. */
class fc2ByteOrder(Enum):
    FC2_BYTE_ORDER_LITTLE_ENDIAN = 0
    FC2_BYTE_ORDER_BIG_ENDIAN = 1
    FC2_BYTE_ORDER_FORCE_32BITS = FULL_32BIT_VALUE

class SystemInfoStruct(FC2Struct):
    _fields_ = [('osType', ctypes.c_int),
                ('osDescription', ctypes.c_char*MAX_STRING_LENGTH),
                ('byteOrder', ctypes.c_int),
                ('sysMemSize', ctypes.c_size_t),
                ('cpuDescription', ctypes.c_char*MAX_STRING_LENGTH),
                ('numCpuCores', ctypes.c_size_t),
                ('driverList', ctypes.c_char*MAX_STRING_LENGTH),
                ('libraryList', ctypes.c_char*MAX_STRING_LENGTH),
                ('gpuDescription', ctypes.c_char*MAX_STRING_LENGTH),
                ('screenWidth', ctypes.c_size_t),
                ('screenHeight', ctypes.c_size_t),                
                ('reserved', ctypes.c_uint*16)]
    def __str__(self):
         rtxt = ("System description:\n\tOS Type: %s\n" % fc2OSType(self.osType).name)
         rtxt = rtxt + ("\tOS description: %s\n" % self.osDescription)
         rtxt = rtxt + ("\tbyteOrder: %s\n" % fc2ByteOrder(self.byteOrder).name)
         rtxt = rtxt + ("\tsysMemSize: %d MB\n" % self.sysMemSize)
         rtxt = rtxt + ("\tCPU Description: %s\n" % self.cpuDescription)
         rtxt = rtxt + ("\tNumber of cores: %d\n" % self.numCpuCores)
         rtxt = rtxt + ("\tGPU description: %s\n" % self.gpuDescription)
         rtxt = rtxt + ("\tdriver list: %s\n" % self.driverList)
         rtxt = rtxt + ("\tlibrary list: %s\n" % self.libraryList)
         rtxt = rtxt + ("\tscreen size: %dx%d (WxH)\n" % (self.screenWidth, self.screenHeight))
         return rtxt
    def __repr__(self):
        return self.__str__()
    def clone(self):
        clone = type(self)()
        ctypes.pointer(clone)[0] = self
        return clone 

# * Possible states of a port on a node.
class fc2PortType(Enum):
    NOT_CONNECTED = 1
    CONNECTED_TO_PARENT = 2
    CONNECTED_TO_CHILD = 3

#     * Type of node.
class fc2NodeType(Enum):
    COMPUTER = 0
    BUS = 1
    CAMERA = 2
    NODE = 3

class fc2TIFFCompressionMethod(Enum):
    FC2_TIFF_NONE = 1 
    FC2_TIFF_PACKBITS = 2
    FC2_TIFF_DEFLATE = 3
    FC2_TIFF_ADOBE_DEFLATE = 4
    FC2_TIFF_CCITTFAX3 = 5 # CCITT Group 3 fax encoding (only 1 bit images) Default to LZW for other bit depths.
    FC2_TIFF_CCITTFAX4 = 6 # CCITT Group 4 fax encoding (only 1 bit images) Default to LZW for other bit depths.
    FC2_TIFF_LZW = 7 # LZW compression
    FC2_TIFF_JPEG = 8 # only valid for 8-bit greyscale and 24bit. Default to LZW for other bit depths.

def errorDescription(errorNr):
    description = ['Function returned with no errors.', 'General failure.', 'Function has not been implemented.', 'Could not connect to Bus Master.', 'Camera has not been connected.', 'Initialization failed.', 'Camera has not been initialized.', 'Invalid parameter passed to function.', 'Setting set to camera is invalid.', 'Invalid Bus Manager object.', 'Could not allocate memory.', 'Low level error.', 'Device not found.', 'GUID failure.', 'Packet size set to camera is invalid.', 'Invalid mode has been passed to function.', 'Error due to not being in Format7.', 'This feature is unsupported.', 'Timeout error.', 'Bus Master Failure.', 'Generation Count Mismatch.', 'Look Up Table failure.', 'IIDC failure.', 'Strobe failure.', 'Trigger failure.', 'Property failure.', 'Property is not present.', 'Register access failed.', 'Register read failed.', 'Register write failed.', 'Isochronous failure.', 'Isochronous transfer has already been started.', 'Isochronous transfer has not been started.', 'Isochronous start failed.', 'Isochronous retrieve buffer failed.', 'Isochronous stop failed.', 'Isochronous image synchronization failed.', 'Isochronous bandwidth exceeded.', 'Image conversion failed.', 'Image library failure.', 'Buffer is too small.', 'There is an image consistency error.', 'The installed driver is not compatible with the library.', FULL_32BIT_VALUE]
    if errorNr == -1:
        return('Undefined')
    else:
        return(description[errorNr])

class PropertyInfoStruct(FC2Struct):
    _fields_ = [('type', ctypes.c_int),
                ('present', ctypes.c_long),
                ('autoSupported', ctypes.c_long),
                ('manualSupported', ctypes.c_long),
                ('onOffSupported', ctypes.c_long),
                ('onePushSupported', ctypes.c_long),
                ('absValSupported', ctypes.c_long),
                ('readOutSupported', ctypes.c_long),
                ('min', ctypes.c_uint),
                ('max', ctypes.c_uint),
                ('absMin', ctypes.c_float),
                ('absMax', ctypes.c_float),
                ('pUnits', ctypes.c_char*MAX_STRING_LENGTH),
                ('pUnitAbbr', ctypes.c_char*MAX_STRING_LENGTH),
                ('reserved', ctypes.c_uint*8)]
    def __str__(self):
        rtxt = ("Property type info:\n\ttype: %s\n" % fc2PropertyType(self.type).name)
        rtxt = rtxt + ("\tproperty is present: %s\n" % ('yes' if bool(self.present) else 'no'))
        rtxt = rtxt + ("Supported properties:\n\tauto:\t\t%s\n" % ('yes' if bool(self.autoSupported) else 'no'))
        rtxt = rtxt + ("\tmanual: \t%s\n" % ('yes' if bool(self.manualSupported) else 'no'))
        rtxt = rtxt + ("\tonOff: \t\t%s\n" % ('yes' if bool(self.onOffSupported) else 'no'))
        rtxt = rtxt + ("\tonePush: \t%s\n" % ('yes' if bool(self.onePushSupported) else 'no'))
        rtxt = rtxt + ("\tabsVal: \t%s\n" % ('yes' if bool(self.absValSupported) else 'no'))
        rtxt = rtxt + ("\treadOut: \t%s\n" % ('yes' if bool(self.readOutSupported) else 'no'))
        rtxt = rtxt + ("Absolute ranges:\n")
        rtxt = rtxt + ("\tmin: %.6f %s\n" % (self.absMin, self.pUnitAbbr))
        rtxt = rtxt + ("\tmax: %.6f %s\n" % (self.absMax, self.pUnitAbbr))
        rtxt = rtxt + ("\tunits: %s\n" % self.pUnits)
        rtxt = rtxt + ("Range of camera internal units:\n\tmin: %d\n" % self.min)
        rtxt = rtxt + ("\tmax: %d\n" % self.max)        
        return rtxt

class PropertyStruct(FC2Struct):
    _fields_ = [('type', ctypes.c_int),
                ('present', ctypes.c_long), #property is present
                ('absControl', ctypes.c_long), #absolute or camera internal units
                ('onePush', ctypes.c_long),
                ('onOff', ctypes.c_long),
                ('autoManualMode', ctypes.c_long),
                ('valueA', ctypes.c_uint),
                ('valueB', ctypes.c_uint),
                ('absValue', ctypes.c_float), # for controlling in absolute mode
                ('reserved', ctypes.c_uint*8)]
    def __str__(self):
        rtxt = ("Camera property:\n\ttype: %s (%d)\n" % (fc2PropertyType(self.type).name, self.type))
        rtxt = rtxt + ("\tproperty is present: %s\n" % ('yes' if  bool(self.present) else 'NO'))
        if bool(self.present):
            rtxt = rtxt + ("\tmode: \t%s\n" % ('auto' if bool(self.autoManualMode) else 'manual'))
            rtxt = rtxt + ("\tControlling %sabsolute value\n" % ('non-' if not bool(self.absControl) else ''))
            rtxt = rtxt + ("\tControlling onePush: \t%s\n" % ('yes' if bool(self.onePush) else 'no'))
            rtxt = rtxt + ("\tControlling onOff: \t\t%s\n" % ('yes' if bool(self.onOff) else 'no'))
            rtxt = rtxt + ("\tabolute value: \t%.6f\n" % self.absValue)
            if self.type != 3:
                rtxt = rtxt + ("\tnon-absolute value: \t%d\n" % self.valueA)
            elif self.type == 3:  # (type is white balance)
                rtxt = rtxt + ("\tnon-absolute valueA: \t%d\n" % self.valueA)
                rtxt = rtxt + ("\tnon-absolute valueB: \t%d\n" % self.valueB)
        return rtxt

class TriggerDelayStruct(PropertyStruct):
    pass
    # For convenience, trigger delay is the same structure
    # used in a separate function along with trigger mode.

class PNGOptionStruct(FC2Struct):
    _fields_ = [('interlaced', ctypes.c_long),
                ('compressionLevel', ctypes.c_uint),  # 0: none  9:best
                ('reserved', ctypes.c_uint*16)]

class PPMOptionStruct(FC2Struct):
    _fields_ = [('binaryFile', ctypes.c_long),
                ('reserved', ctypes.c_uint*16)]

class PGMOptionStruct(FC2Struct):
    _fields_ = [('binaryFile', ctypes.c_long),
                ('reserved', ctypes.c_uint*16)]

class TIFFOptionStruct(FC2Struct):
    _fields_ = [('compressionMethod', ctypes.c_int),
                ('reserved', ctypes.c_uint*16)]

class JPEGOptionStruct(FC2Struct):
    _fields_ = [('progressive', ctypes.c_long),
                # JPEG image quality in range (0-100)
                # 10: poor  50:normal  75:good  100:superb
                ('quality', ctypes.c_uint),
                ('reserved', ctypes.c_uint*16)]

class JPG2OptionStruct(FC2Struct):
    _fields_ = [('quality', ctypes.c_uint),
                ('reserved', ctypes.c_uint*16)]

class BMPOptionStruct(FC2Struct):
    _fields_ = [('indexedColor_8bit', ctypes.c_long),
                ('reserved', ctypes.c_uint*16)]

class MJPGOptionStruct(FC2Struct):
    _fields_ = [('frameRate', ctypes.c_float),
                ('quality', ctypes.c_uint),
                ('reserved', ctypes.c_uint*256)]

class H264OptionStruct(FC2Struct):
    _fields_ = [('frameRate', ctypes.c_float),
                ('width', ctypes.c_uint),
                ('height', ctypes.c_uint),
                ('bitrate', ctypes.c_uint),
                ('reserved', ctypes.c_uint*256)]

class AVIOptionStruct(FC2Struct):
    _fields_ = [('frameRate', ctypes.c_float),
                ('reserved', ctypes.c_uint*256)]
