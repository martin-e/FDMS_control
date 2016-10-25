# acquisition script

import time
from piezo import *
from pyflycap import *
import numpy as np
import matplotlib.pyplot as plt

steps = range(5)
multiplier = 3.48/4
waitBetweenAcquisitions = 0.5

# Camera parameters
ctr = [580, 580]  # [offset_X, offset_Y] # [left, top]
dia = 1080
roi = [ctr[0]-dia/2, ctr[1]-dia/2, dia, dia]  # [offset_X, offset_Y, width, height]
frameRate = 30
integrationTime = 19 # ms
pixelFormat = fc2PixelFormat.FC2_PIXEL_FORMAT_MONO16.value

# init and configure
u3 = LabJackU3()
piezo = Piezo(u3, float(steps[0])*multiplier)
cam = FlyCapture()
numCameras = cam.getNumOfCameras()
if numCameras == 0:
    raise "no camera found!"
guid = cam.getCameraFromIndex(0)
cam.connect(guid)
cameraInfo = cam.getCameraInfo()

# disable all properties which can be set to \"auto\"
for propType in fc2PropertyType:
    if propType.value > 17:
            break
    propInfo = cam.getPropertyInfo(propType.value)
    prop = cam.getProperty(propType.value)
    if bool(propInfo.autoSupported):
        prop.autoManualMode = 0
        cam.setProperty(prop)
        time.sleep(0.25)

# set framerate
propType = fc2PropertyType.FC2_FRAME_RATE
propInfo = cam.getPropertyInfo(propType.value)
prop = cam.getProperty(propType.value)
prop.absValue = frameRate
cam.setProperty(prop)

# set gain and integration time
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
    
# attempt to set FORMAT7 mode...
format7Mode = 7
(supported, fm7Info)= cam.getFormat7Info(format7Mode)
fm7Settings = Format7ImageSettingsStruct()
fm7Settings.mode = format7Mode
fm7Settings.offsetX = roi[0]
fm7Settings.offsetY = roi[1]
fm7Settings.width   = roi[2] #fm7Info.maxWidth
fm7Settings.height  = roi[3] #fm7Info.maxHeight
fm7Settings.pixelFormat = pixelFormat
(isValid, fm7PacketInfo) = cam.validateFormat7Settings(fm7Settings)
if isValid:
    cam.setFormat7ConfigurationPacket(fm7Settings, int(fm7PacketInfo.recommendedBytesPerPacket))
else:
    print("!!! invalid format 7 settings defined")



cam.startCapture()
time.sleep(0.1)
nw = time.localtime(time.time())
timestamp = ("%04d%02d%02d_%02d%02d%02d" % (nw[0], nw[1], nw[2], nw[3], nw[4], nw[5]))
option = TIFFOptionStruct()
#option.compressionMethod = 1   # uncompressed
option.compressionMethod = 3   # DEFLATE  (ZLIB compression)
dtype=np.uint16
imageArray = np.zeros((roi[2], roi[3], len(steps)), dtype)
piezoVoltages = []
for a in steps:
    piezoVoltages.append(a*multiplier)

# make piezo scan and save data
for a in steps:
    image = cam.createImage()
    time.sleep(0.05)
    image = cam.retrieveBuffer(image)
    time.sleep(0.05)    
    # if not last position, then set next
    if a+1 < len(steps):
        piezo.setVoltage(piezoVoltages[a+1])
    filename = ("%s_im_%d.tiff" % (timestamp, a))
    print ("Saving image %d to %s" % (a, filename))
    cam.saveImageWithOption(image, filename, 5, option)
    #imageData = cam.getImageData(image)
    #imageData = np.fromstring(imageData,  dtype)
    #imageData = imageData.reshape([image.rows, image.cols])
    #imageArray[:,:,a] = imageData
    time.sleep(waitBetweenAcquisitions)
cam.stopCapture()
piezo.setVoltage(0)
#arrayFilename = "%s_data" % timestamp
#np.savez_compressed(arrayFilename, imageArray = imageArray, piezoVoltages = piezoVoltages)

#for loading:
# data=np.load(arrayFilename)
# imageArray = data['imageArray']
# piezoVoltages = data['piezoVoltages']

# now show images
'''for a in steps:
    plaatje = imageArray[:,:,a]
    fh = plt.figure()
    plt.imshow(plaatje)
    cb = plt.colorbar()
    fh2= plt.figure()
    histData = plt.hist(imageArray[:,:,a], bins=64)'''

u3.disconnect()
cam.destroyContext()
cam.unloadLib()
del(cam)
