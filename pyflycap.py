"""
Created on Fri Jul 29 15:36:01 2016

@author: eschenm
"""

import ctypes, os, platform, struct

from pyFlyCapture2 import *

class FlyCapture():
    def __init__(self, libdir = '', debug = False):
        self.libdir = ''
        self.debug = debug
        self.libIsLoaded = False
        self.platformInfo = self.getPlatformInfo()
        self.loadLib(libdir)
        self.createContext()

    def __del__(self):
        try:
            self.fc2DestroyContext(self.fc2Context)
        except:
            pass
        self.unloadLib
        
    def __repr__(self):
        rtxt = "Point Grey FlyCapture2 SDK:\n"
        if not self.libIsLoaded:
           rtxt =  rtxt + "library not loaded\n"
        else:
            version = self.getLibraryVersion()
            rtxt = rtxt + "         %s library version %d.%d type: %d build: %d\n" % (self.platformInfo.bitness, version[0], version[1], version[2], version[3])
            try:
                rtxt = rtxt + ("         context: %s\n" % self.fc2Context.contents[:])
                nrCams = self.getNumOfCameras()
                if nrCams == 0:
                    rtxt = rtxt + "No cameras detected\n"
                else:
                    rtxt = rtxt + ("detected %d camera%s\n" % (nrCams, (nrCams>1)*'s'))
            except:
                rtxt = rtxt + "no context created\n"
        return rtxt

    def loadLib(self, libdir):
        if not os.path.exists(libdir):
            if self.debug:
                print ("could not find directory %s" % self.libdir.__repr__())
                print ("attempt to locate Fly Capture library in default locations...")
            if os.path.exists(os.path.join(os.environ['PROGRAMFILES'], 'Point Grey Research\FlyCapture2')):
                libdir = os.path.join(os.environ['PROGRAMFILES'], 'Point Grey Research\FlyCapture2')
                print ("located %s Fly Capture library at: %s" % (self.platformInfo.bitness, libdir))
            else:
                from platform import architecture
                raise FlyCaptureError("Point Grey Fly Capture SDK libraries not found for %s python. Did you install the correct version of the SDK??" % architecture()[0])
        if self.platformInfo.bitness == '32bit':
            self.fc2Path = os.path.join(libdir, 'bin\FlyCapture2.dll')
            self.fc2_cPath = os.path.join(libdir, 'bin\FlyCapture2_C.dll')
        elif self.platformInfo.bitness == '64bit':
            self.fc2Path = os.path.join(libdir, 'bin64\FlyCapture2.dll')
            self.fc2_cPath = os.path.join(libdir, 'bin64\FlyCapture2_C.dll')
        else:
            raise FlyCaptureError("unknown bitness")

        self.fc2 = ctypes.CDLL(self.fc2Path)
        self.fc2_c = ctypes.CDLL(self.fc2_cPath)
                
        self.libIsLoaded = True
        self.libdir = libdir
        if self.debug:
            print("Fly Capture library loaded")

    def unloadLib(self):
        del(self.fc2)
        del(self.fc2_c)
        self.libIsLoaded = False
    
    def getPlatformInfo(self):
        platformInfo = struct
        (platformInfo.bitness , version) = platform.architecture()
        platformInfo.pcName = platform.node()
        platformInfo.pythonver = os.sys.version_info
        return platformInfo
    
    def getSystemInfo(self):
        fc2GetSystemInfo = self.fc2_c.fc2GetSystemInfo
        fc2GetSystemInfo.argtypes = [ctypes.POINTER(SystemInfoStruct)]
        fc2GetSystemInfo.restype = ctypes.c_int
        systemInfo = SystemInfoStruct()
        #fc2GetSystemInfo( fc2SystemInfo* pSystemInfo);
        error = fc2GetSystemInfo(ctypes.pointer(systemInfo))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in setting Format7 configuration: %s" % errDescr)
        return systemInfo

    def getLibraryVersion(self):
        version = VersionStruct(major=0, minor=0, libtype=0, build=0)
        
        fc2GetLibraryVersion = self.fc2_c.fc2GetLibraryVersion
        fc2GetLibraryVersion.argtypes = [ctypes.POINTER(VersionStruct)]
        fc2GetLibraryVersion.restype = ctypes.c_int
        
        error = fc2GetLibraryVersion(version)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error connecting to dll: %s" % errDescr)
        return (version.major, version.minor, version.libtype, version.build)
    def printLibraryVersion(self):
        version = self.getLibraryVersion()
        print ("Point Grey FlyCapture2 library version: %d.%d type: %d build: %d" % (version[0], version[1], version[2], version[3]))

    def createContext(self):
        fc2CreateContext = self.fc2_c.fc2CreateContext
        fc2CreateContext.argtypes = [ctypes.c_void_p]
        fc2CreateContext.restype = ctypes.c_uint
        self.fc2Context_arr = 4 * ctypes.c_ulong
        self.fc2Context = ctypes.pointer(self.fc2Context_arr(0))
        error = fc2CreateContext(ctypes.pointer(self.fc2Context))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("encountered error during context creation: %s" % errDescr)

    def getNumOfCameras(self,):
        fc2GetNumOfCameras = self.fc2_c.fc2GetNumOfCameras
        fc2GetNumOfCameras.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
        fc2GetNumOfCameras.restype = ctypes.c_int
        numCameras = ctypes.c_uint(0)
        error = fc2GetNumOfCameras(self.fc2Context, ctypes.pointer(numCameras))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("could not query number of cameras: %s" % errDescr)
        return int(numCameras.value)

    def destroyContext(self):
        fc2DestroyContext = self.fc2_c.fc2DestroyContext
        fc2DestroyContext.argtypes = [ctypes.c_void_p,]
        fc2DestroyContext.restype = ctypes.c_int
        error = fc2DestroyContext(self.fc2Context.contents)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error during context destruction (disconnect): %s" % errDescr)
        del(self.fc2Context)

    def getCameraFromIndex(self, index):
        guid_arr = 4 * ctypes.c_uint
        fc2GetCameraFromIndex = self.fc2_c.fc2GetCameraFromIndex
        fc2GetCameraFromIndex.argtypes = [ctypes.POINTER(guid_arr)]
        fc2GetCameraFromIndex.restype = ctypes.c_int
        guid = guid_arr(0,0,0,0)
        error = fc2GetCameraFromIndex(self.fc2Context, index, ctypes.pointer(guid))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in fc2GetCameraFromIndex: %s" % errDescr)
        return guid
    
    def connect(self, guid):
        fc2Connect = self.fc2_c.fc2Connect
        fc2Connect.argtypes = [ctypes.c_void_p,]
        fc2Connect.restype = ctypes.c_int
        error = fc2Connect(self.fc2Context, ctypes.pointer(guid))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in connect: %s" % errDescr)
        
    def disconnect(self):
        fc2Disconnect = self.fc2_c.fc2Disconnect
        fc2Disconnect.argtypes = [ctypes.c_void_p,]
        fc2Disconnect.restype = ctypes.c_int
        error = fc2Disconnect(self.fc2Context)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in disconnect: %s" % errDescr)

    def startCapture(self):
        fc2StartCapture = self.fc2_c.fc2StartCapture
        fc2StartCapture.argtypes = [ctypes.c_void_p]
        fc2StartCapture.restype = ctypes.c_int
        error = fc2StartCapture(self.fc2Context)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in start capturing: %s" % errDescr)

    def stopCapture(self):
        fc2StopCapture = self.fc2_c.fc2StopCapture
        fc2StopCapture.argtypes = [ctypes.c_void_p]
        fc2StopCapture.restype = ctypes.c_int
        error = fc2StopCapture(self.fc2Context)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in stop capturing: %s" % errDescr)

    def rescanBus(self):
        fc2RescanBus = self.fc2_c.fc2RescanBus
        fc2RescanBus.argtypes = [ctypes.c_void_p]
        fc2RescanBus.restype = ctypes.c_int
        error = fc2RescanBus(self.fc2Context.contents)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("could not rescan buses: %s" % errDescr)

    def createImage(self):
        image = ImageStruct()
        fc2CreateImage = self.fc2_c.fc2CreateImage
        error = fc2CreateImage(ctypes.pointer(image))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in creating image memory buffer: %s" % errDescr)
        return image
        
    def retrieveBuffer(self, image):
        fc2RetrieveBuffer = self.fc2_c.fc2RetrieveBuffer
        fc2RetrieveBuffer.argtypes = [ctypes.c_void_p, ctypes.POINTER(ImageStruct)]
        fc2RetrieveBuffer.restype = ctypes.c_int
        error = fc2RetrieveBuffer(self.fc2Context, ctypes.pointer(image))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in retrieving buffer: %s" % errDescr)
        return image

    def getCameraInfo(self):
        fc2GetCameraInfo = self.fc2_c.fc2GetCameraInfo
        fc2GetCameraInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(CameraInfoStruct)]
        fc2GetCameraInfo.restype = ctypes.c_int
        cameraInfo = CameraInfoStruct()
        cameraInfo.configROM = ConfigROMStruct()
        cameraInfo.macAddress = MACAddressStruct()
        cameraInfo.ipAddress = IPAddressStruct()
        cameraInfo.subnetMask = IPAddressStruct()
        cameraInfo.defaultGateway = IPAddressStruct()
        error = fc2GetCameraInfo(self.fc2Context, ctypes.pointer(cameraInfo))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in querying camera info: %s" % errDescr)
        return cameraInfo
        
    def getCameraStats(self):
        fc2GetStats = self.fc2_c.fc2GetStats
        fc2GetStats.argtypes = [ctypes.c_void_p, ctypes.POINTER(CameraStatsStruct)]
        fc2GetStats.restype = ctypes.c_int
        cameraStats = CameraStatsStruct()
        cameraStats.timeStamp = TimeStampStruct()
        error = fc2GetStats(self.fc2Context, ctypes.pointer(cameraStats))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in querying camera stats: %s" % errDescr)
        return cameraStats

    def saveImage(self, image, filename, fileFormat):
        fc2SaveImage = self.fc2_c.fc2SaveImage
        fc2SaveImage.argtypes = [ctypes.POINTER(ImageStruct), ctypes.c_char_p, ctypes.c_int]
        fc2SaveImage.restype = ctypes.c_int
        error = fc2SaveImage(ctypes.pointer(image), filename, fileFormat)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in storing image: %s" % errDescr)
    
    def getPropertyInfo(self, property):
        fc2GetPropertyInfo = self.fc2_c.fc2GetPropertyInfo
        fc2GetPropertyInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(PropertyInfoStruct)]
        fc2GetPropertyInfo.restype = ctypes.c_int
        propertyInfo = PropertyInfoStruct()
        propertyInfo.type = property
        # fc2GetPropertyInfo(fc2Context context,     fc2PropertyInfo* propInfo );
        error = fc2GetPropertyInfo(self.fc2Context, ctypes.pointer(propertyInfo))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting property info: %s" % errDescr)
        return propertyInfo

    def getProperty(self, property):
        # Reads the settings for the specified property from the camera. If 
        # auto is on, the integer and abs values returned may not be consistent
        # with each other.
        fc2GetProperty = self.fc2_c.fc2GetProperty
        fc2GetProperty.argtypes = [ctypes.c_void_p, ctypes.POINTER(PropertyStruct)]
        fc2GetProperty.restype = ctypes.c_int
        propertyStruct = PropertyStruct()
        propertyStruct.type = property
        # fc2GetProperty( fc2Context context, fc2Property* prop );
        error = fc2GetProperty(self.fc2Context, ctypes.pointer(propertyStruct))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting property info: %s" % errDescr)
        return propertyStruct
       
    def setProperty(self, propertyStruct):
        # Writes the settings for the specified property to the camera. The
        # property type must be specified in the Property structure passed
        # into the function in order for the function to succeed.
        # The absControl flag controls whether the absolute or integer value
        # is written to the camera. Use fc2GetPropertyInfo() to query which
        # options are available for a specific property.
        fc2SetProperty = self.fc2_c.fc2SetProperty
        fc2SetProperty.argtypes = [ctypes.c_void_p, ctypes.POINTER(PropertyStruct)]
        fc2SetProperty.restype = ctypes.c_int
        # fc2SetProperty(fc2Context context, fc2Property* prop );
        error = fc2SetProperty(self.fc2Context, ctypes.pointer(propertyStruct))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in setting property info: %s" % errDescr)
       
    def getTemperature(self):
        prop = self.getProperty(fc2PropertyType.FC2_TEMPERATURE.value)
        return ((float(prop.valueA)/10)-273.1)

    def getVideoModeAndFrameRateInfo(self, videoMode, frameRate):
        # Query the camera to determine if the specified video mode and
        # frame rate is supported. It appears Format7 is excluded...
        fc2GetVideoModeAndFrameRateInfo = self.fc2_c.fc2GetVideoModeAndFrameRateInfo
        fc2GetVideoModeAndFrameRateInfo.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_long)]
        fc2GetVideoModeAndFrameRateInfo.restype = ctypes.c_int
        supported = ctypes.c_long()
        videoModeV = ctypes.c_long(videoMode)
        frameRateV = ctypes.c_long(frameRate)
        #fc2GetVideoModeAndFrameRateInfo(fc2Context context, fc2VideoMode videoMode, fc2FrameRate frameRate, BOOL* pSupported);
        error = fc2GetVideoModeAndFrameRateInfo(self.fc2Context, videoModeV, frameRateV, ctypes.pointer(supported))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting video mode and frame rate supported status: %s" % errDescr)
        return bool(supported)

    def getVideoModeAndFrameRate(self):
        # Get the current video mode and frame rate from the camera.
        fc2GetVideoModeAndFrameRate = self.fc2_c.fc2GetVideoModeAndFrameRate
        fc2GetVideoModeAndFrameRate.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        fc2GetVideoModeAndFrameRate.restype = ctypes.c_int
        videoMode = ctypes.c_long(-1)
        frameRate = ctypes.c_long(-1)
        #fc2GetVideoModeAndFrameRate(fc2Context context, fc2VideoMode* videoMode, fc2FrameRate* frameRate );
        error = fc2GetVideoModeAndFrameRate(self.fc2Context, ctypes.pointer(videoMode), ctypes.pointer(frameRate))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting current video mode and frame rate: %s" % errDescr)
        return (fc2VideoMode(videoMode.value), fc2FrameRate(frameRate.value))

    def setVideoModeAndFrameRate(self, videoMode, frameRate):
        # Set the specified video mode and frame rate to the camera. It is
        # not possible to set the camera to VIDEOMODE_FORMAT7 or
        # FRAMERATE_FORMAT7. Use the Format7 functions to set the camera
        # into Format7.
        fc2SetVideoModeAndFrameRate = self.fc2_c.fc2SetVideoModeAndFrameRate
        fc2SetVideoModeAndFrameRate.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        fc2SetVideoModeAndFrameRate.restype = ctypes.c_int
        videoModeV = ctypes.c_int(videoMode)
        frameRateV = ctypes.c_int(frameRate)
        if (videoMode==fc2VideoMode.FC2_VIDEOMODE_FORMAT7.value) or (frameRate==fc2FrameRate.FC2_FRAMERATE_FORMAT7):
            raise FlyCaptureError("Use the Format7 functions to set the camera into Format7!!")
        #fc2SetVideoModeAndFrameRate( fc2Context context, fc2VideoMode videoMode, fc2FrameRate frameRate );
        error = fc2SetVideoModeAndFrameRate(self.fc2Context, videoModeV, frameRateV)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in setting video mode and frame rate: %s" % errDescr)

    def getFormat7Info(self, mode):
        # Retrieve the availability of Format7 custom image mode and the
        # camera capabilities for the specified Format7 mode.
        fc2GetFormat7Info = self.fc2_c.fc2GetFormat7Info
        fc2GetFormat7Info.argtypes = [ctypes.c_void_p, ctypes.POINTER(Format7InfoStruct), ctypes.POINTER(ctypes.c_bool)]
        fc2GetFormat7Info.restype = ctypes.c_int
        format7Info = Format7InfoStruct()
        format7Info.mode = mode
        supported = ctypes.c_bool()
        #fc2GetFormat7Info(fc2Context context, fc2Format7Info* info, BOOL* pSupported );
        error = fc2GetFormat7Info(self.fc2Context, ctypes.pointer(format7Info), ctypes.pointer(supported))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting video mode FORMAT7 info: %s" % errDescr)
        return (bool(supported), format7Info)
        
    def getSupportedFormat7PixelFormats(self, format7Info):
        supportedFormats = []
        for format in fc2PixelFormat:
            if (format.value in [0, 20]):
                pass
            if format.value & format7Info.pixelFormatBitField:
                supportedFormats.append(format)
        return supportedFormats

    def validateFormat7Settings(self, fm7ImgSettings):
        # Validates Format7ImageSettings structure and returns valid packet
        # size information if the image settings are valid. The current
        # image settings are cached while validation is taking place. The
        # cached settings are restored when validation is complete.
        fc2ValidateFormat7Settings = self.fc2_c.fc2ValidateFormat7Settings
        fc2ValidateFormat7Settings.argtypes = [ctypes.c_void_p, ctypes.POINTER(Format7ImageSettingsStruct), ctypes.POINTER(ctypes.c_bool), ctypes.POINTER(Format7PacketInfoStruct)]
        fc2ValidateFormat7Settings.restype = ctypes.c_int
        isValid = ctypes.c_bool()
        fm7PacketInfo = Format7PacketInfoStruct()
        # fc2Error fc2ValidateFormat7Settings(fc2Context context, fc2Format7ImageSettings* imageSettings, BOOL* settingsAreValid, fc2Format7PacketInfo* packetInfo );
        error = fc2ValidateFormat7Settings(self.fc2Context, ctypes.pointer(fm7ImgSettings), ctypes.pointer(isValid ) , ctypes.pointer(fm7PacketInfo))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in validating FORMAT7 settings: %s" % errDescr)
        return (bool(isValid.value), fm7PacketInfo)
        
    def getFormat7Configuration(self):
        # Get the current Format7 configuration from the camera. This call
        # will only succeed if the camera is already in Format7.
        fc2GetFormat7Configuration = self.fc2_c.fc2GetFormat7Configuration
        fc2GetFormat7Configuration.argtypes = [ctypes.c_void_p, ctypes.POINTER(Format7ImageSettingsStruct), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_float)]
        fc2GetFormat7Configuration.restype = ctypes.c_int
        imageSettings = Format7ImageSettingsStruct()
        packetSize = ctypes.c_uint()
        percentage = ctypes.c_float()
      #fc2GetFormat7Configuration(fc2Context context, fc2Format7ImageSettings* imageSettings, unsigned int* packetSize, float* percentage );
        error = fc2GetFormat7Configuration(self.fc2Context, ctypes.pointer(imageSettings), ctypes.pointer(packetSize), ctypes.pointer(percentage))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting Format7 configuration settings: %s" % errDescr)
        return (imageSettings, int(packetSize.value), float(percentage.value))
       
    def setFormat7ConfigurationPacket(self, fm7ImgSettings, packetSize):
        # Set the current Format7 configuration to the camera.
        fc2SetFormat7ConfigurationPacket = self.fc2_c.fc2SetFormat7ConfigurationPacket
        fc2SetFormat7ConfigurationPacket.argtypes = [ctypes.c_void_p, ctypes.POINTER(Format7ImageSettingsStruct), ctypes.c_uint]
        fc2SetFormat7ConfigurationPacket.restype = ctypes.c_int
        #fc2SetFormat7ConfigurationPacket(fc2Context context, fc2Format7ImageSettings* imageSettings, unsigned int packetSize );
        error = fc2SetFormat7ConfigurationPacket(self.fc2Context, ctypes.pointer(fm7ImgSettings), packetSize)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in setting Format7 configuration: %s" % errDescr)
    
    def setFormat7Configuration(self, fm7ImgSettings, percentSpeed):
        # Set the current Format7 configuration to the camera.
        fc2SetFormat7Configuration = self.fc2_c.fc2SetFormat7Configuration
        fc2SetFormat7Configuration.argtypes = [ctypes.c_void_p, ctypes.POINTER(Format7ImageSettingsStruct), ctypes.c_float]
        fc2SetFormat7Configuration.restype = ctypes.c_int
        percentSpeed = ctypes.c_float(percentSpeed)
        #fc2SetFormat7Configuration(fc2Context context, fc2Format7ImageSettings* imageSettings, float percentSpeed );
        error = fc2SetFormat7Configuration(self.fc2Context, ctypes.pointer(fm7ImgSettings), percentSpeed)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in setting Format7 configuration: %s" % errDescr)
        
    def getImageData(self, image):
        data = ctypes.string_at(image.pData, image.dataSize)
        return data
        # imageData = np.fromstring(ctypes.string_at(image.pData, image.dataSize), dtype=np.uint8)        
        # Get a pointer to the data associated with the image. This function
        # is considered unsafe. The pointer returned could be invalidated if
        # the buffer is resized or released. The pointer may also be
        # invalidated if the Image object is passed to fc2RetrieveBuffer().
        fc2GetImageData = self.fc2_c.fc2GetImageData
        fc2GetImageData.argtypes = [ctypes.POINTER(ImageStruct), ctypes.POINTER(ctypes.c_char_p)]
        fc2GetImageData.restype = ctypes.c_int
        dataSize = image.dataSize
        data = ctypes.c_char_p
        data = data()
        #fc2GetImageData(fc2Image* pImage, unsigned char** ppData);
        error = fc2GetImageData(ctypes.pointer(image), ctypes.pointer(data))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in setting Format7 configuration: %s" % errDescr)
        
    def convertImageTo(self, pixelFormat, imageIn):
        # Converts the  image buffer to the specified output format and
    # returns the result.
        fc2ConvertImageTo = self.fc2_c.fc2ConvertImageTo
        fc2ConvertImageTo.argtypes = [ctypes.c_long, ctypes.POINTER(ImageStruct), ctypes.POINTER(ImageStruct)]
        fc2ConvertImageTo.restype = ctypes.c_int
        imageOut = ImageStruct()
    #fc2ConvertImageTo(fc2PixelFormat format, fc2Image* pImageIn, fc2Image* pImageOut );
        error = fc2ConvertImageTo(pixelFormat, ctypes.pointer(imageIn), ctypes.pointer(imageOut))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in converting image format: %s" % errDescr)
        return imageOut
                
    def saveImageWithOption(self, image, filename, imageFormat, option):
        # Save the image to the specified file name with the file format specified.
        optionStructs = [PNGOptionStruct, PPMOptionStruct, PGMOptionStruct, TIFFOptionStruct, JPEGOptionStruct, JPG2OptionStruct, BMPOptionStruct]
        try:
            optionStructs.index(option.__class__)
        except:
            raise FlyCaptureError("option is of unknown class")
        fc2SaveImageWithOption = self.fc2_c.fc2SaveImageWithOption
        fc2SaveImageWithOption.argtypes = [ctypes.POINTER(ImageStruct), ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(option.__class__)]
        fc2SaveImageWithOption.restype = ctypes.c_int
        #fc2SaveImageWithOption(fc2Image* pImage, const char* pFilename, fc2ImageFileFormat format, void* pOption );
        error = fc2SaveImageWithOption(image, filename, imageFormat, option)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in saving image with options: %s" % errDescr)

    def determineBitsPerPixel(self, format):
        fc2DetermineBitsPerPixel= self.fc2_c.fc2DetermineBitsPerPixel
        fc2DetermineBitsPerPixel.argtypes = [ctypes.c_long, ctypes.POINTER(ctypes.c_uint)]
        fc2DetermineBitsPerPixel.restype = ctypes.c_int
        bitsPerPixel = ctypes.c_uint(0)
        #fc2DetermineBitsPerPixel(fc2PixelFormat format,unsigned int* pBitsPerPixel)
        error = fc2DetermineBitsPerPixel(format, ctypes.pointer(bitsPerPixel))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in determine bits per pixel: %s" % errDescr)
        return int(bitsPerPixel.value)

    def getImageTimeStamp(self, image):
        fc2GetImageTimeStamp = self.fc2_c.fc2GetImageTimeStamp
        timeStamp = TimeStampStruct()
        fc2GetImageTimeStamp.argtypes = [ctypes.POINTER(ImageStruct)]
        fc2GetImageTimeStamp.restype = TimeStampStruct
        #fc2TimeStamp  fc2GetImageTimeStamp(fc2Image* pImage);
        try:
            timeStamp = fc2GetImageTimeStamp(ctypes.pointer(image))
        except:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting image timestamp")
        return timeStamp

    def createImageStatistics(self):
        fc2CreateImageStatistics = self.fc2_c.fc2CreateImageStatistics
        ImageStatisticsContext = ctypes.c_void_p()
        fc2CreateImageStatistics.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        fc2CreateImageStatistics.restype = ctypes.c_int
        #fc2CreateImageStatistics(fc2ImageStatisticsContext* pImageStatisticsContext );
        error = fc2CreateImageStatistics(ctypes.pointer(ImageStatisticsContext))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in creating image statistics: %s" % errDescr)
        return ImageStatisticsContext
        
    def destroyImageStatistics(self, ImageStatisticsContext):
        fc2DestroyImageStatistics = self.fc2_c.fc2DestroyImageStatistics
        fc2DestroyImageStatistics.argtypes = [ctypes.c_void_p]
        fc2DestroyImageStatistics.restype = ctypes.c_int
        #fc2DestroyImageStatistics(fc2ImageStatisticsContext imageStatisticsContext );
        error = fc2DestroyImageStatistics(ImageStatisticsContext)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in destroying context: %s" % errDescr)
        return data

    def calculateImageStatistics(self, image, ImageStatisticsContext):
        fc2CalculateImageStatistics = self.fc2_c.fc2CalculateImageStatistics
        fc2CalculateImageStatistics.argtypes = [ctypes.POINTER(ImageStruct), ctypes.POINTER(ctypes.c_void_p)]
        fc2CalculateImageStatistics.restype = ctypes.c_int
        #fc2CalculateImageStatistics(fc2Image* pImage, fc2ImageStatisticsContext* pImageStatisticsContext )
        error = fc2CalculateImageStatistics(ctypes.pointer(image), ctypes.pointer(ImageStatisticsContext))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in : %s" % errDescr)

    def imageStatisticsEnableGreyOnly(self, ImageStatisticsContext):
        fc2ImageStatisticsEnableGreyOnly = self.fc2_c.fc2ImageStatisticsEnableGreyOnly
        fc2ImageStatisticsEnableGreyOnly.argtypes = [ctypes.c_void_p]
        fc2ImageStatisticsEnableGreyOnly.restype = ctypes.c_int
        #fc2ImageStatisticsEnableGreyOnly(fc2ImageStatisticsContext imageStatisticsContext );
        error = fc2ImageStatisticsEnableGreyOnly(ImageStatisticsContext)
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in: %s" % errDescr)
        return data

    def getImageStatistics(self, ImageStatisticsContext, channel):
        fc2GetImageStatistics = self.fc2_c.fc2GetImageStatistics
        histogramProto = ctypes.c_uint * 1024
        fc2GetImageStatistics.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_uint), \
                                          ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint), \
                                          ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_float), \
                                          ctypes.POINTER(ctypes.POINTER(histogramProto))]
        fc2GetImageStatistics.restype = ctypes.c_int
        st = struct
        st.rangeMin = 0
        st.rangeMax = 0
        st.pixelValueMin = 0
        st.pixelValueMax = 0
        st.numPixelValues = 0
        st.histogram = histogramProto()
        #fc2GetImageStatistics(fc2ImageStatisticsContext imageStatisticsContext, fc2StatisticsChannel channel, unsigned int* pRangeMin, 
        #       unsigned int* pRangeMax, unsigned int* pPixelValueMin, unsigned int* pPixelValueMax, unsigned int* pNumPixelValues, 
        #       float* pPixelValueMean, int** ppHistogram );
        error = fc2GetImageStatistics(ImageStatisticsContext, channel, ctypes.pointer(st.rangeMin), ctypes.pointer(st.rangeMax), ctypes.pointer(st.pixelValueMin), ctypes.pointer(st.pixelValueMax), ctypes.pointer(st.numPixelValues), ctypes.pointer(ctypes.pointer(st.histogram)))
        if error:
            errDescr = errorDescription(error)
            raise FlyCaptureError("Error in getting image statistics: %s" % errDescr)
        return st
    
 
    # suggested library functions to be implemented:
        # setting camera to 16bit acquisition
        # getting image statistics to work
        
            
## ********************************************************

if __name__  == '__main__':
    import time, os
    
    cam = FlyCapture(libdir = '', debug = True)
    format7Mode = 0
    pixelFormat = fc2PixelFormat.FC2_PIXEL_FORMAT_MONO16.value
    roi = [0, 0, 1920, 1200]  # [offset_left, offset_top, width, height]
    roi = [916, 510, 80, 80]   # (956, 550) ambient, vacuum pump turned on
    roi = [1000, 384, 80, 80]   # (1040, 424) cryo pumping
    roi = [902, 518, 80, 80]   # (956, 550) ambient, vacuum pump turned on
    path = 'D:\FiberDimpleManufacturing'
    
    print (cam)
    numCameras = cam.getNumOfCameras()

    print ('detected %d camera%s' % (numCameras, ((numCameras != 1)*'s')))
    
    if numCameras > 0:
        index = 0 # connect to first camera
        guid = cam.getCameraFromIndex(index)
        cam.connect(guid)
        print ("found and connected camera")
        time.sleep(1)
        cameraInfo = cam.getCameraInfo()

        if cameraInfo.sensorResolution:
            cam.resolution = list()
            for val in cameraInfo.sensorResolution.split('x'):
                cam.resolution.append(int(val))
        # print (cameraInfo)
        
        stats = cam.getCameraStats()
        print (stats)
        print ("\n\ncamera connected")
        
        if 0:
            print ("\n# listing all properties which can be set to \"auto\"")
            for propType in fc2PropertyType:
                if propType.value > 17:
                    break
                propInfo = cam.getPropertyInfo(propType.value)
                prop = cam.getProperty(propType.value)
                if bool(propInfo.autoSupported):
                    print (propInfo)
                    print (prop)
                    print ("\n\n*********************\n\n")
        
        if 1:
            print ("\n# disable all properties which can be set to \"auto\"")
            for propType in fc2PropertyType:
                if propType.value > 17:
                    break
                propInfo = cam.getPropertyInfo(propType.value)
                prop = cam.getProperty(propType.value)
                if bool(propInfo.autoSupported):
                    # print ("setting property %s to 0" % propType.name)
                    prop.autoManualMode = 0
                    cam.setProperty(prop)
                    time.sleep(0.25)
                    # print (cam.getProperty(propType.value))
                    # print ("\n\n*********************\n\n")   
        if 0:
            print ("\ngetting video format and frame rate settings:")
            (videoMode, frameRate) = cam.getVideoModeAndFrameRate()
            if videoMode.value == fc2VideoMode.FC2_VIDEOMODE_FORMAT7.value:
                frameRate = cam.getProperty(fc2PropertyType.FC2_FRAME_RATE.value)
                print ("\tvideo mode: %s\n\tframe rate: %.3f" % (videoMode.name, frameRate.absValue))
            else:
                print ("\tvideo mode: %s\n\tframe rate: %s" % (videoMode.name, frameRate.name))
            print ("\n**********************************\n")

        if 1:
            frameRate = 100            
            print ("set framerate to %.1f Hz" % frameRate)
            propType = fc2PropertyType.FC2_FRAME_RATE
            propInfo = cam.getPropertyInfo(propType.value)
            prop = cam.getProperty(propType.value)
            prop.absValue = frameRate
            cam.setProperty(prop)
            time.sleep(0.25)
            print ("framerate is now: %.3f ms" % cam.getProperty(fc2PropertyType.FC2_FRAME_RATE.value).absValue)
            print ("\n**********************************\n")

        if 1:
            integrationTime = 0.1  # milliseconds
            # print ("set gain to zero and integration time to %.3f ms" % integrationTime)
            propType = fc2PropertyType.FC2_SHUTTER
            propInfo = cam.getPropertyInfo(propType.value)
            prop = cam.getProperty(propType.value)
            prop.absValue = integrationTime
            cam.setProperty(prop)
            propType = fc2PropertyType.FC2_GAIN
            prop = cam.getProperty(propType.value)
            prop.absValue = 0
            cam.setProperty(prop)
            time.sleep(0.25)
            
            print ("integration time is now: %.3f ms" % cam.getProperty(fc2PropertyType.FC2_SHUTTER.value).absValue)
            print ("gain is now: %.3f dB" % cam.getProperty(fc2PropertyType.FC2_GAIN.value).absValue)
            print ("\n**********************************\n")
            
        if 0:
            print ("listing available FORMAT7 modes:\n")
            cam.availableFormat7Modes = list()
            for mode in fc2Mode:
                if mode.value >= fc2Mode.FC2_NUM_MODES.value:
                    break
                (supported, format7Info)= cam.getFormat7Info(mode.value)
                if supported:
                    cam.availableFormat7Modes.append(mode.value)
                    print (format7Info)
                    print ([ a.name for a in cam.getSupportedFormat7PixelFormats(format7Info) ])
            print ("\n**********************************\n")

        if 1:
            print ("attempt to set FORMAT7 mode and ROI...")
            (supported, fm7Info)= cam.getFormat7Info(format7Mode)
            fm7Settings = Format7ImageSettingsStruct()
            fm7Settings.mode = format7Mode
            try:
                fm7Settings.offsetX = roi[0]
                fm7Settings.offsetY = roi[1]
                fm7Settings.width   = roi[2] #fm7Info.maxWidth
                fm7Settings.height  = roi[3] #fm7Info.maxHeight
            except:
                fm7Settings.offsetX = 0
                fm7Settings.offsetY = 0
                fm7Settings.width   = fm7Info.maxWidth
                fm7Settings.height  = fm7Info.maxHeight
            fm7Settings.pixelFormat = pixelFormat
            (isValid, fm7PacketInfo) = cam.validateFormat7Settings(fm7Settings)
            if isValid:
                print (fm7Settings)
                print (fm7PacketInfo)
                cam.setFormat7ConfigurationPacket(fm7Settings, int(fm7PacketInfo.recommendedBytesPerPacket))
                print ("Format7 mode %d settings are set." % format7Mode)
            else:
                print ("!!! invalid format 7 settings defined")
            print ("\n**********************************\n")
            
        if 0:
            print ("\nstart capture of single image")
            cam.startCapture()
            image = cam.createImage()
            time.sleep(0.5)
            image = cam.retrieveBuffer(image)
            print ("stop capture")
            cam.stopCapture()
            format = '%Y%m%dT%H%M%S_testimage.tiff'
            filename = time.strftime(format)
            option = TIFFOptionStruct()
            option.compressionMethod = 1   # uncompressed
            print ("Saving image to %s" % filename)
            cam.saveImageWithOption(image, filename, 5, option)
            import numpy as np
            import matplotlib.pyplot as plt
            # 12 bit per pixel readout is not yet supported
            if fc2PixelFormat(pixelFormat).name == 'FC2_PIXEL_FORMAT_MONO12':
                raise FlyCaptureError("12 bit data readout not (yet) supported!")
            imageData = cam.getImageData(image)
            if fc2PixelFormat(image.pixFormat).name == 'FC2_PIXEL_FORMAT_MONO8':
                dtype=np.uint8
            else:
                dtype=np.uint16
                
            imageArray = np.fromstring(imageData,  dtype)
            # something still needs to be constructed for converting 12 bit
            plaatje = imageArray.reshape([image.rows, image.cols])
            fh = plt.imshow(plaatje)
            cb = plt.colorbar()
            fh2= plt.figure()
            histData = plt.hist(imageArray, bins=64)
        
        if 1:
            print ("\nstart capture of series of images")
            nrImages = 100
            import numpy as np
            from scipy import ndimage
            import h5py
            # 12 bit per pixel readout is not yet supported
            if fc2PixelFormat(pixelFormat).name == 'FC2_PIXEL_FORMAT_MONO12':
                raise FlyCaptureError("12 bit data readout not (yet) supported!")

            cam.startCapture()
            image = cam.createImage()
            time.sleep(0.5)
            if fc2PixelFormat(image.pixFormat).name == 'FC2_PIXEL_FORMAT_MONO8':
                dtype=np.uint8
                hdfDtype = np.uint8
            else:
                dtype=np.uint16
                hdfDtype = np.uint16
            format = '%Y%m%dT%H%M%S'
            startTime = time.localtime()
            filename = time.strftime(format + '_vibration.hdf5', startTime)
            print ("Saving image data to %s" % os.path.join(path, filename))
            try:
                f = h5py.File(os.path.join(path, filename), "w")
                imageStack = f.create_dataset("images",(nrImages, fm7Settings.height, fm7Settings.width,), dtype = hdfDtype)
                timestamps = f.create_dataset("timestamps",(nrImages,), dtype = np.float64)
                positions = f.create_dataset("positions", (nrImages, 2), dtype = np.float32)
            except:
                raise FlyCaptureError("error during creating HDF5 file")
                
            for ii in range(nrImages):
                image = cam.retrieveBuffer(image)
                imageData = cam.getImageData(image)
                imageTime = cam.getImageTimeStamp(image)
                timestamps[ii] = np.float64(imageTime.seconds) + np.float64(imageTime.microSeconds / 1.0e6)
                imageArray = np.fromstring(imageData, dtype)
                imageStack[ii,...] = imageArray.reshape([fm7Settings.height, fm7Settings.width])
                #print ("%d: %.3f - %d" % (ii, timestamps[ii]-timestamps[0], np.sum(np.sum(imageArray[...]))))
                time.sleep(0.015)
            numimages = ii
            imageStack.attrs["filename"] = np.string_(filename)
            imageStack.attrs["startTime"] = time.strftime(format, startTime)
            imageStack.attrs["numImages"] = numimages
            
            for ii in range(numimages):
                border = 2
                frame = imageStack[ii,border:-border, border:-border]
                offset = np.mean(np.mean(frame[0:10,0:10]))
                center_of_mass = ndimage.measurements.center_of_mass(frame - offset)
                positions[ii,...] = center_of_mass
                et = timestamps[ii]-timestamps[0]
                #print("%.3f: (%.3f, %.3f)" % (et, positions[ii,0], positions[ii,1]))
            f.flush()
            f.close()
               
            print ("stop capture")
            cam.stopCapture()
    if 1:
        cam.destroyContext()
        cam.unloadLib()
        del(cam)
