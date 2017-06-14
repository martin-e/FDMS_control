# FDMS_control

control software for precise dose control of a pulsed laser as 
well as measuring microscopic surface using a phase stepped 
interferometer.

Controlled equipment:
power meter (Thorlabs PM100USB)
Arbitrary waveform generator (Siglent SDG2000X series)
Labjack U3-LV with LJTick-DAC for interferomter control and 
	GPIO and additional ADC
Camera (Point Grey Research (now FLIR) BFLY-U3-23S6M-C cmos detector)

Each piece of the above equipment has its own class. The 
interferometer reference arm position is read by the Labjack and is 
used as input for a PID control loop. The piezo is controlled by 
changing the LJTick-DAC output voltage. Nominally about 4.0V/fringe 
and with 2.25 fringes in total (minimum setpoint offset is 0.02)

The laser pulsing is controlled by sending pulses through an RF
driver connected to an AOM. The deflected beam is passed on to the
sample. A power meter ...
