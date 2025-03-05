import logging
import smbus2
import time
from typing import Any
import threading
import math

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


class GyroSensor:
    """
    Reads data from an MPU-6050 gyroscope sensor over I2C.
    
    Attributes:
        bus: The SMBus object for I2C communication.
        gyro_offset: The calculated offset after calibration.
    """
    def __init__(self, bus_number: int = 1, address: int = 0x68, pwr_mgmt_reg: int = 0x6B, calibration_samples: int = 150) -> None:
        self.bus_number = bus_number
        self.address = address
        self.pwr_mgmt_reg = pwr_mgmt_reg
        try:
            self.bus = smbus2.SMBus(bus_number)
            self.bus.write_byte_data(self.address, self.pwr_mgmt_reg, 0)
        except Exception as e:
            logger.error("Error initializing I2C bus: %s", e)
            raise e
        self.calibrate(calibration_samples)
    
    def read_raw_data(self, addr: int) -> int:
        """
        Reads two bytes of raw data from the MPU-6050 starting at addr.
        
        Args:
            addr (int): Register address.
            
        Returns:
            int: A signed integer representing the sensor reading.
        """
        try:
            high = self.bus.read_byte_data(self.address, addr)
            low = self.bus.read_byte_data(self.address, addr + 1)
            value = (high << 8) | low
            if value > 32768:
                value -= 65536
            return value
        except Exception as e:
            logger.error("Error reading raw data: %s", e)
            return 0
    
    def read_gyro_z(self) -> float:
        """
        Reads the Z-axis gyroscope value and converts it to degrees per second.
        
        Returns:
            float: The Z-axis rate in deg/sec.
        """
        raw = self.read_raw_data(0x47)  # Z-axis register for MPU-6050
        gyro_z = raw / 131.0
        return gyro_z
    
    def read_accel_x(self) -> float:
        """
        X ekseni accelerometer verisini okur ve m/s² cinsine çevirir.
        MPU-6050 için ±2g aralığında ve 16384 LSB/g ölçeği kullanılır.
        
        Returns:
            float: X ekseni doğrusal ivme (m/s²).
        """
        try:
            high = self.bus.read_byte_data(self.address, 0x3B)  # Accelerometer X yüksek byte
            low = self.bus.read_byte_data(self.address, 0x3C)   # Accelerometer X düşük byte
            value = (high << 8) | low
            if value > 32768:
                value -= 65536
            # 1g = 16384 LSB, 1g = 9.81 m/s²
            accel_x = (value / 16384.0) * 9.81
            return accel_x
        except Exception as e:
            logger.error("Error reading accelerometer data: %s", e)
            return 0.0
    
    def get_smoothed_gyro(self, samples: int = 5, delay: float = 0.005) -> float:
        """
        Returns a smoothed gyro reading using a moving average.
        
        Args:
            samples (int): Number of samples to average.
            delay (float): Delay between samples.
            
        Returns:
            float: The averaged gyro reading (with offset subtracted).
        """
        total = 0.0
        for _ in range(samples):
            total += (self.read_gyro_z() - self.gyro_offset)
            time.sleep(delay)
        return total / samples
    
    def calibrate(self, samples: int = 150) -> None:
        """
        Calibrates the gyro by averaging a number of samples while the sensor is stationary.
        """
        logger.info("Calibrating gyro... Please keep the sensor still.")
        offset_sum = 0.0
        for _ in range(samples):
            offset_sum += self.read_gyro_z()
            time.sleep(0.005)
        self.gyro_offset = offset_sum / samples
        logger.info("Calibration complete. Gyro offset: %.2f deg/sec", self.gyro_offset)
    
    def cleanup(self) -> None:
        """
        Closes the I2C bus.
        """
        try:
            self.bus.close()
        except Exception as e:
            logger.error("Error during I2C bus cleanup in GyroSensor: %s", e)

    def __enter__(self) -> "GyroSensor":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()

    def __del__(self) -> None:
        self.cleanup()

class AngleTracker(threading.Thread):
    """
    Aracın açısal pozisyonunu (gyroscope verisiyle) ve ileri hızını, 
    accelerometer verisinden entegrasyon yaparak hesaplayan thread.
    Ardından bu verilerle (x, y) konumunu günceller.
    """
    def __init__(self, gyro_sensor: GyroSensor, sample_delay: float = 0.005) -> None:
        """
        Args:
            gyro_sensor (GyroSensor): Kullanılacak sensör.
            sample_delay (float): Ölçümler arası bekleme süresi.
        """
        super().__init__()
        self.gyro_sensor = gyro_sensor
        self.sample_delay = sample_delay
        self.angle = 0.0    # Başlangıç açısı (derece)
        self.x = 0.0        # Başlangıç x konumu
        self.y = 0.0        # Başlangıç y konumu
        self.forward_speed = 0.0  # Başlangıç ileri hızı (m/s)
        self._stop_event = threading.Event()
    
    def run(self) -> None:
        logger.info("Starting AngleTracker thread...")
        last_time = time.time()
        while not self._stop_event.is_set():
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Açısal hız entegrasyonu: Jiroskop verisiyle açıyı güncelle
            angular_velocity = self.gyro_sensor.get_smoothed_gyro()
            self.angle += angular_velocity * dt
            
            # İvme entegrasyonu: Accelerometer x verisinden ileri hızı hesapla
            acceleration = self.gyro_sensor.read_accel_x()  # m/s² cinsinden
            self.forward_speed += acceleration * dt
            
            # Hesaplanan hız ile geçen mesafeyi bul ve konum entegrasyonu yap
            distance = self.forward_speed * dt
            angle_rad = math.radians(self.angle)
            self.x += distance * math.cos(angle_rad)
            self.y += distance * math.sin(angle_rad)
            
            # logger.info("Angle: %.2f deg, Speed: %.2f m/s, Position: (%.2f, %.2f)", 
            #             self.angle, self.forward_speed, self.x, self.y)
            time.sleep(self.sample_delay)
    
    def stop(self) -> None:
        self._stop_event.set()
        logger.info("Stopping AngleTracker thread...")
    
    def get_position(self) -> tuple:
        """
        Güncel (x, y) konumunu döndürür.
        
        Returns:
            tuple: (x, y) konumu.
        """
        return self.x, self.y
    
    def get_speed(self) -> float:
        """
        Güncel ileri hızı (m/s) döndürür.
        
        Returns:
            float: İleri hız.
        """
        return self.forward_speed