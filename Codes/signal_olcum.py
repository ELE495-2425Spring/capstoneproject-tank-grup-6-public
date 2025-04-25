import subprocess
import numpy as np
from scipy.signal import medfilt, savgol_filter, find_peaks
from rtlsdr import RtlSdr  # PyRTLSDR kütüphanesinden varsayılan RTL-SDR sınıfı
import logging
import time


logger = logging.getLogger(__name__)



def _run_rtl_power(start_freq_mhz, end_freq_mhz, bin_size_khz,
                   sample_interval, total_duration, sample_rate):
    """Helper function to run rtl_power command and parse output."""
    bin_size = f"{bin_size_khz}k"
    cmd = [
        "rtl_power",
        "-f", f"{start_freq_mhz}M:{end_freq_mhz}M:{bin_size}",
        "-g", "0",
        "-i", str(sample_interval),
        "-e", str(total_duration),
        "-s", str(int(sample_rate))
    ]
    result = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
    if result.returncode != 0:
        print("Hata:", result.stderr)
        return None, None

    freqs = []
    pows  = []
    for line in result.stdout.strip().split("\n"):
        if line.startswith("#"): continue
        parts = line.split(",")
        f0 = float(parts[2]) / 1e6
        f1 = float(parts[3]) / 1e6
        vals = list(map(float, parts[6:]))
        step = (f1 - f0) / len(vals)
        freqs.extend([f0 + i * step for i in range(len(vals))])
        pows.extend(vals)

    return np.array(freqs), np.array(pows)

from scipy.signal import medfilt, savgol_filter, find_peaks
import numpy as np


def measure_signal_power_narrow(center_freq_mhz=433.000,
                                span_mhz=0.06,
                                bin_size_khz=1,
                                sample_rate=2.048e6):
    """Measuring avg dBm around 433 MHz in a narrow window."""
    start = center_freq_mhz - span_mhz/2
    end   = center_freq_mhz + span_mhz/2
    freqs, pows = _run_rtl_power(start, end, bin_size_khz,
                                 sample_interval=1,
                                 total_duration=1,
                                 sample_rate=sample_rate)
    if freqs is None:
        return None
    

    # Dar band filtresi + SavGol + tepe izolasyonu
    # psd_med = medfilt(pows, kernel_size=11)
    # psd_sg  = savgol_filter(psd_med, window_length=51, polyorder=3)
    # peaks, _ = find_peaks(psd_sg, height=psd_sg.max()-20)
    # mask = np.zeros_like(psd_sg, dtype=bool)
    # half_bw = 50e3/1e6/2  # 50 kHz çevresi
    # for pk in peaks:
    #     mask |= np.abs(freqs - freqs[pk]) <= half_bw
    # psd_peaks = np.where(mask, psd_sg, psd_sg.min())

    # # Ortalama hesapla (orijinal imzaya uygun)
    tol = 0.015
    m2  = (freqs >= center_freq_mhz - tol) & (freqs <= center_freq_mhz + tol)
    vals = pows[m2]
    return np.max(vals)
    # vals = psd_peaks[m2]
    # avg_dbm = np.mean(vals) if len(vals) > 0 else None
    # return round(avg_dbm, 2) if avg_dbm is not None else None


def measure_signal_power_wide(center_freq_mhz=433,
                              span_mhz=2,
                              bin_size_khz=10,
                              sample_rate=2.048e6):
    """Raw spectrum over 432–434 MHz for display."""
    start = center_freq_mhz - span_mhz/2
    end   = center_freq_mhz + span_mhz/2
    return _run_rtl_power(start, end, bin_size_khz,
                          sample_interval=0.5,
                          total_duration=0.5,
                          sample_rate=sample_rate)


def measure_signal_power_narrow_rtlsdr(sdr, 
                                      center_freq_mhz=433.000,
                                      span_mhz=0.06,
                                      bin_size_khz=1,
                                      sample_rate=2.048e6):
    """
    Measures average signal power in a narrow frequency range (432.990 MHz to 433.010 MHz).
    Returns the average power in dBm.
    """
    # Convert inputs to Hz
    center_freq = center_freq_mhz * 1e6
    span = span_mhz * 1e6
    bin_size = bin_size_khz * 1e3
    
    # Set SDR parameters
    sdr.sample_rate = sample_rate
    sdr.center_freq = center_freq
    sdr.gain = "auto"  # Adjust gain as needed
    
    # Calculate frequency range
    freq_start = 432.990e6
    freq_end = 433.010e6
    
    # Number of samples for FFT (to achieve desired bin size)
    num_samples = int(sample_rate / bin_size)
    
    # Read samples
    samples = sdr.read_samples(num_samples)
    
    # Compute FFT
    window = np.hanning(num_samples)
    samples_windowed = samples * window
    spectrum = np.fft.fftshift(np.fft.fft(samples_windowed))
    power_spectrum = np.abs(spectrum) ** 2 / num_samples
    
    # Frequency axis
    freqs = np.fft.fftshift(np.fft.fftfreq(num_samples, 1/sample_rate)) + center_freq
    
    # Select frequencies within the narrow range
    mask = (freqs >= freq_start) & (freqs <= freq_end)
    power_selected = power_spectrum[mask]
    
    if len(power_selected) == 0:
        return np.nan  # Return NaN if no valid data
    
    # Convert to dBm (assuming 50 ohm impedance)
    power_watts = power_selected / 1e3  # Rough scaling (calibration may be needed)
    power_dbm = 10 * np.log10(power_watts) + 30
    
    # Return average power
    return np.mean(power_dbm)

def measure_signal_power_wide_rtlsdr(sdr, 
                                    center_freq_mhz=433.000,
                                    span_mhz=2.0,
                                    bin_size_khz=10,
                                    sample_rate=3.2e6):
    """
    Measures signal power across a wide frequency range (432 MHz to 434 MHz) with low resolution.
    Returns frequency array (Hz) and power array (dBm), or empty arrays if measurement fails.
    
    Parameters:
    - sdr: Initialized RtlSdr object
    - center_freq_mhz: Center frequency in MHz (default: 433.000)
    - span_mhz: Frequency span in MHz (default: 2.0, covering 432–434 MHz)
    - bin_size_khz: FFT bin size in kHz (default: 10, for low resolution)
    - sample_rate: Sample rate in Hz (default: 2.048e6)
    
    Returns:
    - freqs_selected: Numpy array of frequencies (Hz)
    - power_dbm: Numpy array of power values (dBm)
    """
    try:
        # Convert inputs to Hz
        center_freq = center_freq_mhz * 1e6
        bin_size = bin_size_khz * 1e3

        # Define wide frequency range
        freq_start = 432e6
        freq_end = 434e6

        # Number of samples for FFT (to achieve desired bin size)
        num_samples = 256#int(sample_rate / bin_size)

        # Read samples
        samples = sdr.read_samples(num_samples)

        # Compute FFT
        window = np.hanning(num_samples)
        samples_windowed = samples * window
        spectrum = np.fft.fftshift(np.fft.fft(samples_windowed))
        power_spectrum = np.abs(spectrum) ** 2 / num_samples

        # Frequency axis
        freqs = np.fft.fftshift(np.fft.fftfreq(num_samples, 1/sample_rate)) + center_freq

        # Select frequencies within the wide range
        mask = (freqs >= freq_start) & (freqs <= freq_end)
        freqs_selected = freqs[mask]
        power_selected = power_spectrum[mask]

        if len(power_selected) == 0:
            logger.warning("No data in frequency range %.3f–%.3f MHz", freq_start/1e6, freq_end/1e6)
            return np.array([]), np.array([])

        # Convert to dBm (approximate, calibration may be needed)
        power_watts = power_selected / 1e3  # Rough scaling
        power_dbm = 10 * np.log10(power_watts) + 30

        logger.debug("Wideband measurement: %d frequency points", len(freqs_selected))
        return freqs_selected, power_dbm

    except Exception as e:
        logger.error("Failed to measure wideband signal power: %s", str(e))
        return np.array([]), np.array([])
    
def get_signal_strength(sdr):
    peak_powers = []
    start_time = time.time()
    while time.time() - start_time < 1:
        samples = sdr.read_samples(256*1024)
        power_spectrum = np.abs(np.fft.fft(samples))**2
        peak_power = np.max(power_spectrum)
        peak_powers.append(10 * np.log10(peak_power))
    return round(np.mean(peak_powers)-80, 2) if peak_powers else -100
