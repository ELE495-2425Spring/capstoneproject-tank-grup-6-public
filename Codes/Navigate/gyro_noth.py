import logging
import smbus2
import time
from typing import Any
import math

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

class GyroSensor2:
    def __init__(self, bus_number: int = 1, address: int = 0x68, pwr_mgmt_reg: int = 0x6B, calibration_samples: int = 200):
        self.bus_number = bus_number
        self.address = address
        self.pwr_mgmt_reg = pwr_mgmt_reg
        self.angle = 0.0
        try:
            self.bus = smbus2.SMBus(bus_number)
            self.bus.write_byte_data(self.address, self.pwr_mgmt_reg, 0)  # Wake up MPU-6050
            self.bus.write_byte_data(self.address, 0x1B, 0x08)  # Gyro ±500°/s
            #logger.info("MPU-6050 initialized with gyro range ±500°/s")
        except Exception as e:
            logger.error("Error initializing I2C bus: %s", e)
            raise e
        self.gyro_scale = 65.5  # LSB/(°/s) for ±500°/s
        self.calibrate(calibration_samples)

    def read_raw_data(self, addr: int) -> int:
        try:
            high = self.bus.read_byte_data(self.address, addr)
            low = self.bus.read_byte_data(self.address, addr + 1)
            value = (high << 8) | low
            if value > 32768:
                value -= 65536
            return value
        except Exception as e:
            raise e

    def read_gyro_z(self) -> float:
        raw = self.read_raw_data(0x47)  # Z-axis gyro register
        gyro_z = raw / self.gyro_scale
        return gyro_z

    def get_smoothed_gyro(self, samples: int = 10, delay: float = 0.005) -> float:
        total = 0.0
        for _ in range(samples):
            raw_gyro = self.read_gyro_z()
            corrected_gyro = raw_gyro - self.gyro_offset
            total += corrected_gyro
            time.sleep(delay)
        result = total / samples
        return result

    def calibrate(self, samples: int = 200):
        logger.info("Calibrating gyro in 3 seconds... Keep the sensor still.")
        time.sleep(3)
        offset_sum = 0.0
        for _ in range(samples):
            offset_sum += self.read_gyro_z()
            time.sleep(0.005)
        self.gyro_offset = offset_sum / samples
        logger.info("Calibration complete. Gyro offset: %.2f deg/sec", self.gyro_offset)

    def cleanup(self):
        self.bus.close()