import logging
import RPi.GPIO as GPIO
from typing import Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


class MotorController:
    """
    Controls motor outputs via GPIO and PWM.
    
    Attributes:
        ENA, IN1, IN2, ENB, IN3, IN4: Fixed pin numbers for motor driver.
        pwmA, pwmB: PWM objects for motor enable pins.
    """
    def __init__(self, ena: int, in1: int, in2: int, enb: int, in3: int, in4: int, pwm_frequency: int = 1000) -> None:
        self.ENA = ena
        self.IN1 = in1
        self.IN2 = in2
        self.ENB = enb
        self.IN3 = in3
        self.IN4 = in4
        self.pins = [ena, in1, in2, enb, in3, in4]
        
        # Setup GPIO pins
        GPIO.setmode(GPIO.BOARD)
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Setup PWM channels for enable pins
        self.pwmA = GPIO.PWM(self.ENA, pwm_frequency)
        self.pwmB = GPIO.PWM(self.ENB, pwm_frequency)
        self.pwmA.start(0)
        self.pwmB.start(0)
    
    def forward(self, left_speed: float, right_speed: float) -> None:
        """
        Sets motor outputs for forward motion.
        
        Args:
            left_speed (float): PWM duty cycle for left motor (0-100).
            right_speed (float): PWM duty cycle for right motor (0-100).
        """
        try:
            GPIO.output(self.IN1, GPIO.HIGH)
            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN3, GPIO.HIGH)
            GPIO.output(self.IN4, GPIO.LOW)
            self.pwmA.ChangeDutyCycle(left_speed)
            self.pwmB.ChangeDutyCycle(right_speed)
        except Exception as e:
            logger.error("Error in forward() motor command: %s", e)
    
    def backward(self, left_speed: float, right_speed: float) -> None:
        """
        Sets motor outputs for backward motion.
        
        Args:
            left_speed (float): PWM duty cycle for left motor (0-100).
            right_speed (float): PWM duty cycle for right motor (0-100).
        """
        try:
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.HIGH)
            GPIO.output(self.IN3, GPIO.LOW)
            GPIO.output(self.IN4, GPIO.HIGH)
            self.pwmA.ChangeDutyCycle(left_speed)
            self.pwmB.ChangeDutyCycle(right_speed)
        except Exception as e:
            logger.error("Error in backward() motor command: %s", e)
    
    def stop(self) -> None:
        """
        Stops the motors by setting PWM to 0 and turning off all control signals.
        """
        if GPIO.getmode() is None:
            return
        try:
            self.pwmA.ChangeDutyCycle(0)
            self.pwmB.ChangeDutyCycle(0)
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN3, GPIO.LOW)
            GPIO.output(self.IN4, GPIO.LOW)
        except Exception as e:
            logger.error("Error in stop() motor command: %s", e)
    
    def cleanup(self) -> None:
        """
        Cleans up motor resources. Note: Global GPIO.cleanup() is handled by Navigator.
        """
        self.stop()
        self.pwmA.stop()
        self.pwmB.stop()

    def __enter__(self) -> "MotorController":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()

    def __del__(self) -> None:
        self.cleanup()
