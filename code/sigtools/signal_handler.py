import logging
import time
import threading
import numpy as np
from typing import Optional
from collections import deque
from collections import Counter

try:
    from rtlsdr import RtlSdr
except ImportError as e:
    raise ImportError("pyrtlsdr module not installed. Install it via 'pip install pyrtlsdr'") from e

from .config import SIGNAL_CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


class SignalHandler:
    """
    Class for RTL-SDR signal analysis.
    
    This class encapsulates an RTL-SDR device and continuously monitors
    the signal to update the RSSI (Received Signal Strength Indicator) value.
    It applies a Weighted Moving Average (WMA) filter to smooth the RSSI values.
    Additional signal acquisition methods may be added later.
    
    Attributes:
        sdr (RtlSdr): The RTL-SDR device object.
        running (bool): Flag to control the continuous RSSI reading loop.
        rssi_lock (threading.Lock): Lock for thread-safe access to RSSI data.
        current_rssi (float): The latest measured raw RSSI in dB.
        last_rssis (deque): A sliding window of recent raw RSSI readings.
        cleaned (bool): Flag indicating whether cleanup has been performed.
    """
    def __init__(self,
                 center_freq: float = SIGNAL_CONFIG["CENTER_FREQ"],
                 sample_rate: float = SIGNAL_CONFIG["SAMPLE_RATE"],
                 gain: float = SIGNAL_CONFIG["GAIN"]) -> None:
        """
        Initializes the RTL-SDR device with parameters from the configuration.
        
        Args:
            center_freq (float): Center frequency in Hz (default: 432.89e6).
            sample_rate (float): Sample rate in samples per second.
            gain (float): Gain for the SDR device (default: 20.0).
        """
        self.sdr: RtlSdr = RtlSdr()
        self.sdr.center_freq = center_freq
        self.sdr.sample_rate = sample_rate
        self.sdr.gain = gain

        self.running: bool = False
        self.rssi_lock: threading.Lock = threading.Lock()
        self.current_rssi: float = -float('inf')
        self.last_rssis: deque = deque(maxlen=30)
        self.meaned_rssis: deque = deque(maxlen=20)
        self.cleaned: bool = False
        self._rssi_thread: Optional[threading.Thread] = None
        self.cleaned = False

    def _calculate_rssi(self, samples: np.ndarray) -> float:
        """
        Calculates the RSSI (in dB) from an array of complex IQ samples.
        
        Args:
            samples (np.ndarray): Array of IQ samples.
            
        Returns:
            float: The calculated RSSI in dB.
        """
        power = np.mean(np.abs(samples) ** 2)
        rssi = 10 * np.log10(power) if power > 0 else -float('inf')
        return rssi

    def get_rssi(self, num_samples: int = 256) -> float:
        """
        Reads a batch of IQ samples from the SDR and returns the computed raw RSSI.
        
        Args:
            num_samples (int): Number of samples to read (default: 256).
            
        Returns:
            float: The calculated raw RSSI in dB.
        """
        try:
            samples = self.sdr.read_samples(num_samples)
            return self._calculate_rssi(samples)
        except Exception as e:
            logger.error("Error reading RSSI: %s", e)
            return -float('inf')

    def _calculate_wma(self, values: deque) -> float:
        """
        Calculates the Weighted Moving Average (WMA) of the RSSI values in the deque.
        Newer values are given higher weight.
        
        Args:
            values (deque): Deque containing RSSI values.
        
        Returns:
            float: The weighted moving average of the RSSI.
        """
        if not values:
            return -float('inf')
        N = len(values)
        # Weights: 1 for oldest, up to N for newest.
        weights = np.arange(1, N + 1)
        total_weight = weights.sum()
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / total_weight

    def _calculate_weighted_average_by_frequency(self, values: deque) -> float:
        """
        Calculates the weighted moving average of RSSI values based on frequency.
        Values that are close (rounded to 2 decimal places) are considered equal,
        and their frequency determines the weight.
        
        Args:
            values (deque): Deque containing RSSI values.
        
        Returns:
            float: The frequency weighted RSSI average.
        """
        if not values:
            return -float('inf')
        
        # Round values to 2 decimal places
        rounded_values = [round(v, 2) for v in values]
        
        # Create a frequency histogram of the rounded values
        freq = Counter(rounded_values)
        
        # Calculate the weighted sum using frequency as weight
        total_count = sum(freq.values())
        weighted_sum = sum(val * count for val, count in freq.items())
        
        return weighted_sum / total_count

    def start_rssi(self, blocking: bool = True, interval: float = 1.0) -> Optional[threading.Thread]:
        """
        Starts a continuous loop for reading and updating the RSSI.
        
        This method reads IQ samples, calculates the raw RSSI, updates an internal sliding
        window, and computes the weighted moving average (WMA). It can run in blocking mode
        or as a non-blocking thread.
        
        Args:
            blocking (bool): If True, the loop runs until stopped; if False, returns a Thread.
            interval (float): Time interval in seconds between successive measurements.
            
        Returns:
            Optional[threading.Thread]: Returns a Thread if non-blocking; otherwise, None.
        """
        self.running = True

        def rssi_loop() -> None:
            while self.running:
                try:
                    samples = self.sdr.read_samples(256)
                    rssi_value = self._calculate_rssi(samples)
                    with self.rssi_lock:
                        self.last_rssis.append(rssi_value)
                        self.current_rssi = rssi_value
                    logger.info("Current RSSI: %.2f dB", rssi_value)
                except Exception as e:
                    logger.error("Error reading RSSI: %s", e)
                time.sleep(interval)

        if blocking:
            rssi_loop()
            return None
        else:
            self._rssi_thread = threading.Thread(target=rssi_loop)
            self._rssi_thread.start()
            return self._rssi_thread

    def stop_rssi(self) -> None:
        """
        Stops the continuous RSSI reading loop.
        """
        self.running = False
        if self._rssi_thread is not None:
            self._rssi_thread.join()
            self._rssi_thread = None

    @property
    def latest_rssi(self) -> (float, float):
        """
        Returns the latest raw RSSI value and the weighted moving average over the recent window.
        
        Returns:
            tuple: (latest_raw_rssi, wma_rssi)
        """
        with self.rssi_lock:
            wma = self._calculate_wma(self.last_rssis)
            return self.current_rssi, wma

    def cleanup(self) -> None:
        """
        Cleans up the RTL-SDR resources.
        """
        if self.cleaned:
            return
        try:
            self.sdr.close()
        except Exception as e:
            logger.error("Error during SDR cleanup: %s", e)
        self.cleaned = True

    def __enter__(self) -> "SignalHandler":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    def __del__(self) -> None:
        self.cleanup()
