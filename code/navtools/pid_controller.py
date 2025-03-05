import time
from typing import Any

class PIDController:
    """
    A simple PID controller.
    
    Attributes:
        kp, ki, kd: PID coefficients.
        deadband: Error threshold under which error is treated as zero.
        integral_max: Maximum absolute value for the integral term (anti-windup).
    """
    def __init__(self, kp: float, ki: float, kd: float, deadband: float = 0.1, integral_max: float = 20.0) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.deadband = deadband
        self.integral_max = integral_max
        self.reset()
    
    def reset(self) -> None:
        """
        Resets the integral and derivative components.
        """
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_time = time.time()
    
    def compute(self, setpoint: float, measurement: float) -> float:
        """
        Computes the PID output.
        
        Args:
            setpoint: The desired target value.
            measurement: The current measured value.
            
        Returns:
            The control output.
        """
        current_time = time.time()
        dt = current_time - self.previous_time
        if dt <= 0:
            dt = 0.001
        self.previous_time = current_time
        
        error = setpoint - measurement
        if abs(error) < self.deadband:
            error = 0.0
        self.integral += error * dt
        # Clamp the integral term to prevent windup
        self.integral = max(min(self.integral, self.integral_max), -self.integral_max)

        derivative = (error - self.previous_error) / dt
        self.previous_error = error
        
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        return output
