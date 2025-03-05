import logging
import time
import threading
import numpy as np
from typing import Optional
from collections import deque
import matplotlib.pyplot as plt
from .config import SIGNAL_CONFIG

try:
    from rtlsdr import RtlSdr
except ImportError as e:
    raise ImportError("pyrtlsdr module not installed. Install it via 'pip install pyrtlsdr'") from e

from .config import SIGNAL_CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


class SDRModule:
    """
    Class for RTL-SDR signal analysis.
    
    This class encapsulates an RTL-SDR device and provides methods for receiving signal samples,
    computing the signal power (with filtering), and converting the power to dBm. It also supports
    continuous monitoring of the signal in a background thread.
    
    Attributes:
        sdr (RtlSdr): The RTL-SDR device object.
        default_sample_number (int): The default multiplier for samples (sample_number * 1024).
        latest_power_dbm (float): The latest measured signal power in dBm (from continuous monitoring).
        _power_window (deque): A sliding window to hold recent power measurements for averaging.
        _lock (threading.Lock): Lock to protect access to _power_window and latest_power_dbm.
        _running (bool): Flag to control the background monitoring thread.
        _monitor_thread (Optional[threading.Thread]): The background thread for continuous monitoring.
    """
    def __init__(self, sample_rate: float = SIGNAL_CONFIG["SAMPLE_RATE"], center_freq: float = SIGNAL_CONFIG["CENTER_FREQ"], gain: float = SIGNAL_CONFIG["GAIN"], default_sample_number: int = SIGNAL_CONFIG["SAMPLE_NUMBER"]) -> None:
        """
        Initializes the RTL-SDR device with the specified parameters.
        
        Args:
            sample_rate (float): The sample rate in samples per second.
            center_freq (float): The center frequency in Hz.
            gain (float): The gain for the SDR device.
            default_sample_number (int): The default multiplier for samples (samples = default_sample_number * 1024).
        """
        try:
            self.sdr = RtlSdr()
        except Exception as e:
            print("Error: SDR not found")
            raise e
        
        self.sdr.gain = gain
        self.sdr.sample_rate = sample_rate
        self.sdr.center_freq = center_freq
        self.default_sample_number = default_sample_number

        self.latest_power_dbm: float = -np.inf
        self._power_window: deque = deque(maxlen=30)
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None

        self._plot_running = True
        self._plot_thread = threading.Thread(target=self.save_plot, daemon=True)
        self._plot_thread.start()
    
    def get_spectrum(self):
        NFFT = 512 * 1024  # Increased FFT resolution
        samples = self.sdr.read_samples(NFFT)  # Read samples
        fft_data = np.fft.fftshift(np.fft.fft(samples))  # Compute FFT
        epsilon = np.finfo(float).eps  
        power_spectrum = 20 * np.log10(np.abs(fft_data) + epsilon)
        freqs = np.fft.fftshift(np.fft.fftfreq(len(fft_data), 1/self.sdr.sample_rate)) + self.sdr.center_freq
        return freqs, power_spectrum

    def save_plot(self):
        # Use a non-interactive backend to avoid displaying the plot on screen
        import matplotlib
        matplotlib.use("Agg")

        fig, ax = plt.subplots(figsize=(10, 5))
        freqs, power_spectrum = self.get_spectrum()
        line, = ax.plot(freqs / 1e6, power_spectrum, color='blue')

        # Set fixed axis limits
        ax.set_ylim(-140, 0)  # Fixed dB range
        ax.set_xlim((self.sdr.center_freq - self.sdr.sample_rate / 2) / 1e6,
                    (self.sdr.center_freq + self.sdr.sample_rate / 2) / 1e6)  # MHz
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("Power (dB)")
        ax.set_title("RTL-SDR Spectrum at 433 MHz")
        ax.grid()

        # Live update loop; use self._plot_running to allow thread termination
        while self._plot_running:
            start_time = time.time()
            print(f"Plot update at {start_time}")
            freqs, power_spectrum = self.get_spectrum()
            line.set_ydata(power_spectrum - 100)  # Update data with offset if needed
            fig.canvas.draw()
            try:
                fig.savefig('./images/live_plot.png')
            except Exception as e:
                logger.error("Error saving figure: %s", e)
            time.sleep(0.05)  # Faster refresh rate (~20 FPS)

    def signal_receive(self, sample_number: Optional[int] = None) -> np.ndarray:
        """
        Receives a batch of IQ samples from the SDR.
        
        Args:
            sample_number (Optional[int]): If provided, the number of samples is sample_number * 1024.
                                            Otherwise, default_sample_number * 1024 samples are read.
                                            
        Returns:
            np.ndarray: The array of complex IQ samples.
        """
        if sample_number is None:
            return self.sdr.read_samples(self.default_sample_number * 1024)
        return self.sdr.read_samples(sample_number * 1024)

    def filter_signal_power(self, signal_power: np.ndarray, threshold: float) -> np.ndarray:
        """
        Filters the signal power array by removing outliers based on the median and standard deviation.
        
        Args:
            signal_power (np.ndarray): Array of signal power values.
            threshold (float): Multiplier for the standard deviation to define acceptable range.
            
        Returns:
            np.ndarray: The filtered signal power array.
        """
        median_val = np.median(signal_power)
        std_val = np.std(signal_power)
        filtered_power = signal_power[(signal_power > median_val - threshold * std_val) &
                                      (signal_power < median_val + threshold * std_val)]
        if filtered_power.size == 0:
            return signal_power
        return filtered_power

    def find_signal_power(self, signal: np.ndarray) -> float:
        """
        Computes the average power of the signal after filtering out outliers.
        
        Args:
            signal (np.ndarray): Array of complex IQ samples.
            
        Returns:
            float: The average signal power.
        """
        power = np.abs(signal) ** 2
        avg_power = np.mean(self.filter_signal_power(power, 2))
        return avg_power

    def signal_power_to_dbm(self, signal: np.ndarray, impedance: float = 50) -> float:
        """
        Converts the average signal power to dBm.
        
        Args:
            signal (np.ndarray): Array of complex IQ samples.
            impedance (float): The system impedance in ohms (default: 50).
            
        Returns:
            float: The signal power in dBm.
        """
        avg_power = self.find_signal_power(signal)
        power_watts = avg_power / impedance
        if power_watts <= 0:
            return -np.inf
        power_dbm = 10 * np.log10(power_watts * 1000)
        return power_dbm

    def _monitor_loop(self, interval: float) -> None:
        """
        Internal method that continuously receives signal samples,
        computes the power in dBm, and updates the internal sliding window and latest_power_dbm.
        
        Args:
            interval (float): Time interval (in seconds) between successive readings.
        """
        while self._running:
            try:
                samples = self.signal_receive()
                power_dbm = self.signal_power_to_dbm(samples)
                with self._lock:
                    self.latest_power_dbm = power_dbm
            except Exception as e:
                logger.error("Error in monitoring loop: %s", e)
            time.sleep(interval)

    def start_monitoring(self, blocking: bool = True, interval: float = 1.0) -> Optional[threading.Thread]:
        """
        Starts a background thread that continuously monitors the signal power.
        
        Args:
            blocking (bool): If True, the monitoring loop runs in blocking mode; if False, a Thread is returned.
            interval (float): Time interval (in seconds) between successive signal readings.
            
        Returns:
            Optional[threading.Thread]: Returns a Thread if non-blocking; otherwise, None.
        """
        self._running = True
        if blocking:
            self._monitor_loop(interval)
            return None
        else:
            self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
            self._monitor_thread.start()
            return self._monitor_thread

    def stop_monitoring(self) -> None:
        """
        Stops the background monitoring loop and waits for the thread to terminate.
        """
        self._running = False
        if self._monitor_thread is not None:
            self._monitor_thread.join()
            self._monitor_thread = None

    def reset(self) -> None:
        """
        Resets the SDR device settings and default sample number.
        """
        self.sdr.gain = 0
        self.sdr.sample_rate = 0
        self.sdr.center_freq = 0
        self.default_sample_number = 0

    def cleanup(self) -> None:
        """
        Cleans up the SDR resources.
        """
        self.stop_monitoring()
        self._plot_running = False
        if hasattr(self, '_plot_thread') and self._plot_thread is not None:
            self._plot_thread.join()
            self._plot_thread = None
        try:
            self.sdr.close()
        except Exception as e:
            logger.error("Error during SDR cleanup: %s", e)

    def __enter__(self) -> "SDRModule":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    def __del__(self) -> None:
        self.cleanup()
