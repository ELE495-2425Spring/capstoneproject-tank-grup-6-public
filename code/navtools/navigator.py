import logging
import time
import threading
import RPi.GPIO as GPIO
from typing import Optional
from .motor_controller import MotorController
from .gyro_sensor import GyroSensor
from .pid_controller import PIDController
from .config import MOTOR_CONFIG, GYRO_CONFIG, PID_CONFIG, MOVEMENT_CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


class Navigator:
    """
    High-level class for controlling a Raspberry Pi–based robot with fixed motor pins.
    
    This class combines motor control, gyro sensing, and PID control for straight
    movement. Rotation is handled using unsigned integration of gyro data.
    It uses a movement lock for thread safety and provides both blocking and
    non-blocking movement methods.
    """
    def __init__(self, kp: float = PID_CONFIG["STRAIGHT"]["KP"],
                 ki: float = PID_CONFIG["STRAIGHT"]["KI"],
                 kd: float = PID_CONFIG["STRAIGHT"]["KD"],
                 loop_delay: float = MOVEMENT_CONFIG["LOOP_DELAY"]) -> None:
        # Fixed Motor Pin Declarations (do not change)
        self.ENA: int = MOTOR_CONFIG["ENA"]
        self.IN1: int = MOTOR_CONFIG["IN1"]
        self.IN2: int = MOTOR_CONFIG["IN2"]
        self.ENB: int = MOTOR_CONFIG["ENB"]
        self.IN3: int = MOTOR_CONFIG["IN3"]
        self.IN4: int = MOTOR_CONFIG["IN4"]
        
        # Instantiate MotorController using fixed pins and configuration
        self.motor_controller = MotorController(
            self.ENA, self.IN1, self.IN2,
            self.ENB, self.IN3, self.IN4,
            pwm_frequency=MOTOR_CONFIG["PWM_FREQUENCY"]
        )
        
        # Instantiate GyroSensor with configuration
        self.gyro_sensor = GyroSensor(
            bus_number=GYRO_CONFIG["BUS_NUMBER"],
            address=GYRO_CONFIG["ADDRESS"],
            pwr_mgmt_reg=GYRO_CONFIG["PWR_MGMT_REG"],
            calibration_samples=GYRO_CONFIG["CALIBRATION_SAMPLES"]
        )
        
        # PID controllers for straight movement (forward and backward)
        self.pid_forward = PIDController(kp, ki, kd,
                                         deadband=PID_CONFIG["STRAIGHT"]["DEADBAND"],
                                         integral_max=PID_CONFIG["STRAIGHT"]["INTEGRAL_MAX"])
        self.pid_backward = PIDController(kp, ki, kd,
                                          deadband=PID_CONFIG["STRAIGHT"]["DEADBAND"],
                                          integral_max=PID_CONFIG["STRAIGHT"]["INTEGRAL_MAX"])
        self.loop_delay: float = loop_delay
        
        # Movement lock to ensure thread safety for movement commands
        self.movement_lock = threading.Lock()
        self.cleaned = False


    def _pid_move(self, duration: float, base_speed: float, direction: str = 'forward') -> None:
        """
        Internal method to execute PID-controlled straight movement.
        
        Args:
            duration (float): How long to move (seconds).
            base_speed (float): Base PWM speed.
            direction (str): 'forward' or 'backward'.
        """
        self.gyro_sensor.calibrate()
        with self.movement_lock:
            pid = self.pid_forward if direction == 'forward' else self.pid_backward
            pid.reset()
            start_time = time.time()
            while (time.time() - start_time) < duration:
                gyro_rate: float = self.gyro_sensor.get_smoothed_gyro()
                # We want 0 deg/sec yaw during straight movement
                adjustment: float = pid.compute(0, gyro_rate)
                
                if direction == 'forward':
                    left_speed: float = max(0, min(100, base_speed - adjustment))
                    right_speed: float = max(0, min(100, base_speed + adjustment))
                    self.motor_controller.forward(left_speed, right_speed)
                    # logger.info("Forward PID | Gyro: %.2f | Adj: %.2f | L: %.1f | R: %.1f",
                    #             gyro_rate, adjustment, left_speed, right_speed)
                else:
                    left_speed: float = max(0, min(100, base_speed + adjustment))
                    right_speed: float = max(0, min(100, base_speed - adjustment))
                    self.motor_controller.backward(left_speed, right_speed)
                    # logger.info("Backward PID | Gyro: %.2f | Adj: %.2f | L: %.1f | R: %.1f",
                    #             gyro_rate, adjustment, left_speed, right_speed)
                time.sleep(self.loop_delay)
            self.motor_controller.stop()

    def backward(self, duration: float, speed: float, blocking: bool = True) -> Optional[threading.Thread]:
        """
        Executes PID-controlled forward movement.
        
        Args:
            duration (float): Movement duration in seconds.
            speed (float): Base PWM speed.
            blocking (bool): If True, function blocks until completion.
        
        Returns:
            Optional[threading.Thread]: Thread object if non-blocking; otherwise, None.
        """
        if blocking:
            self._pid_move(duration, speed, direction='forward')
            return None
        else:
            thread = threading.Thread(target=self._pid_move, args=(duration, speed, 'forward'))
            thread.start()
            return thread

    def forward(self, duration: float, speed: float, blocking: bool = True) -> Optional[threading.Thread]:
        """
        Executes PID-controlled backward movement.
        
        Args:
            duration (float): Movement duration in seconds.
            speed (float): Base PWM speed.
            blocking (bool): If True, function blocks until completion.
        
        Returns:
            Optional[threading.Thread]: Thread object if non-blocking; otherwise, None.
        """
        if blocking:
            self._pid_move(duration, speed, direction='backward')
            return None
        else:
            thread = threading.Thread(target=self._pid_move, args=(duration, speed, 'backward'))
            thread.start()
            return thread

    def rotate(self, target_angle: float, speed: float, blocking: bool = True, rotation: str = 'Left') -> Optional[threading.Thread]:
        """
        Rotates the car to the left by `target_angle` degrees using unsigned rotation control.
        The method integrates gyro readings (using their absolute value) until the target angle is reached.

        Args:
            target_angle (float): Desired rotation in degrees.
            speed (float): PWM speed during rotation.
            blocking (bool): If True, the function blocks until rotation completes; otherwise, returns a Thread.

        Returns:
            Optional[threading.Thread]: If blocking is False, returns the Thread object; otherwise, returns None.
        """
        self.gyro_sensor.calibrate()
        integrated_angle: float = 0.0
        previous_time: float = time.time()

        def rotation_loop() -> None:
            nonlocal integrated_angle, previous_time
            while integrated_angle < target_angle:
                current_time: float = time.time()
                dt: float = current_time - previous_time
                if dt <= 0:
                    dt = 0.001
                previous_time = current_time

                # Use the absolute value of the gyro rate for integration.
                gyro_rate: float = abs(self.gyro_sensor.get_smoothed_gyro())
                integrated_angle += gyro_rate * dt
                # logger.info("Rotating... Integrated angle: %.2f°", integrated_angle)

                if rotation == 'Left':
                    # For left rotation: left motor backward, right motor forward.
                    GPIO.output(self.IN1, GPIO.LOW)
                    GPIO.output(self.IN2, GPIO.HIGH)
                    GPIO.output(self.IN3, GPIO.HIGH)
                    GPIO.output(self.IN4, GPIO.LOW)
                else:
                    # For left rotation: left motor backward, right motor forward.
                    GPIO.output(self.IN1, GPIO.HIGH)
                    GPIO.output(self.IN2, GPIO.LOW)
                    GPIO.output(self.IN3, GPIO.LOW)
                    GPIO.output(self.IN4, GPIO.HIGH)
                self.motor_controller.pwmA.ChangeDutyCycle(speed)
                self.motor_controller.pwmB.ChangeDutyCycle(speed)
                time.sleep(self.loop_delay)
            self.motor_controller.stop()
            logger.info("Rotation complete. Total rotated: %.2f°", integrated_angle)

        if blocking:
            rotation_loop()
            return None
        else:
            thread = threading.Thread(target=rotation_loop)
            thread.start()
            return thread
    
    def cleanup(self) -> None:
        """
        Cleans up all resources used by Navigator.
        """
        if self.cleaned:
            return
        self.motor_controller.cleanup()
        self.gyro_sensor.cleanup()
        try:
            if GPIO.getmode() is not None:
                GPIO.cleanup()
            else:
                logger.info("GPIO cleanup skipped: No channels have been set up.")
        except Exception as e:
            logger.error("Error during GPIO cleanup in Navigator: %s", e)
        self.cleaned = True

    def __enter__(self) -> "Navigator":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    def __del__(self) -> None:
        self.cleanup()
