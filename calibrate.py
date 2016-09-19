# routine for performing calibration scan
# M. Eschen - 2016

import piezo, pyflycap, time
import numpy as np

startV = 0   # start voltage
endV = 2     # stop scan at this voltage
pausetime = 0.2
roi = [200, 100, 480, 640]  # [offset_X, offset_Y, width, height]
integrationTime = 20  # ms


# %%%%%%% prepare arrays
(start, end) = (piezo.voltageToBitval(startV), piezo.voltageToBitval(endV))
bitvals = range(start, end+1)
voltages = []
for v in bitvals:
    voltages.append(piezo.bitvalToVoltage(v))
index = range(len(bitvals))

cols = roi[2]-roi[0]+1
rows = roi[3]-roi[1]+1
calData = np.zeros((cols, rows, len(bitvals)), dtype = uint16)

# %%%%%%% connect and configure hardware %%%%%%%%%%%%%%
# connect to labjack
piezo = piezo.LabJackU3(0)
# connect to camera
cam = FlyCapture(libdir = '', debug = True)
format7Mode = 7
pixelFormat = fc2PixelFormat.FC2_PIXEL_FORMAT_MONO16.value
numCameras = cam.getNumOfCameras()
if numCameras == 0:
	raise "could not locate camera"

guid = cam.getCameraFromIndex(index)
cam.connect(guid)

# set all properties to manual
for propType in fc2PropertyType:
	if propType.value > 17:
		break
	propInfo = cam.getPropertyInfo(propType.value)
	prop = cam.getProperty(propType.value)
	if bool(propInfo.autoSupported):
		prop.autoManualMode = 0
		cam.setProperty(prop)
		time.sleep(0.05)

# set integration time
propType = fc2PropertyType.FC2_SHUTTER
propInfo = cam.getPropertyInfo(propType.value)
prop = cam.getProperty(propType.value)
prop.absValue = integrationTime
cam.setProperty(prop)

# set gain to zero
propType = fc2PropertyType.FC2_GAIN
prop = cam.getProperty(propType.value)
prop.absValue = 0
cam.setProperty(prop)
time.sleep(0.1)

# set format 7 settings
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
	print fm7Settings
	print fm7PacketInfo
	cam.setFormat7ConfigurationPacket(fm7Settings, int(fm7PacketInfo.recommendedBytesPerPacket))
	print("Format7 mode %d settings are set." % format7Mode)
else:
	raise "invalid format 7 settings defined!"

cam.startCapture()
nw = time.localtime(time.time())
filename = ("%04d%02d%02d%02d%02d%02d_calibration.npy" % (nw[0], nw[1], nw[2], nw[3], nw[4], nw[5]))

# %%%%%%%%%%% perform calibration scan
print ("starting scan!")
for i in index:
    print ("setting %3d/%3d: %.3fV" % (i, voltages[i], len(voltages)))
    piezo.setBitval(bitvals[i])
    time.sleep(pausetime)
	# get image data
    image = cam.retrieveBuffer(image)
    imageData = cam.getImagedata(image)
    imageArray = np.reshape(imageData, (cols, rows))
	# put image data in array
    calData((:, :, i)) = imageArray
	# for saving data in temp file see example in 
	# http://docs.scipy.org/doc/numpy/reference/generated/numpy.savez.html#numpy.savez

# save array
np.savez_compressed(filename, calData=calData, 
                              voltages=np.array(voltages),
                              bitvals = np.array(bitvals))
print ("Calibration data save to %s" % filename)
cam.stopCapture()
cam.destroyContext()
