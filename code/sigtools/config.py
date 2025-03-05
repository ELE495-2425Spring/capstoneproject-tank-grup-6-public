"""
Configuration parameters for the RTL-SDR SignalHandler.
"""

SIGNAL_CONFIG = {
    "CENTER_FREQ": 432.89e6,   # Center frequency in Hz (432.89 MHz)
    "SAMPLE_RATE": 3200000,    # Highest possible sample rate for RTL-SDR (samples per second)
    "GAIN": 50.0,              # Gain for the SDR device
	"SAMPLE_NUMBER": 256
}
