# FDMS_control
# Martin Eschen  (C) 2017 - 2018

Control software for precise dose control of a pulsed laser as 
well as measuring microscopic surface using a phase stepped 
interferometer.

Controlled equipment:
power meter (Thorlabs PM100USB)
Arbitrary waveform generator (Siglent SDG2000X series)
Labjack U3-LV with LJTick-DAC for interferometer control and 
	GPIO and additional ADC
Camera (Point Grey Research (now FLIR) USB Blackfly cmos detector)

Each piece of the above equipment has its own class. The 
interferometer reference arm length is read by the Labjack and is 
used as input for a PID control loop. The piezo is controlled by 
changing the LJTick-DAC output voltage. Nominally about 4.0V/fringe 
and with 1.5 fringes phase step in total for a 7-step scan the 
output voltage is scanned over about 6V.
(minimum setpoint offset is 0.02)

For surface measurement using the interferometer and the camera 
there is a measuring class.

The laser output into the setup is controlled by the AWG output. 
The power meter measures the intensity briefly before firing the 
laser. The awg output pulse is corrected to get a pre defined 
intensity during the pulse. The achieved dose can be precisely 
altered by changing the pulse length.

An analysis class reads the stored HDF5 files containg camera images.
It unwraps the calculated phase and produces a surface height map.
A 2-d gauss fit can be performed on a dimple enclosed in the ROI.
Fit parameters are stored in a txt file.