"""
Configuration parameters for the robot.
"""

# Fixed Motor Configuration
MOTOR_CONFIG = {
    "ENA": 11,           # Motor A enable (PWM)
    "IN1": 13,           # Motor A direction
    "IN2": 15,           # Motor A direction
    "ENB": 19,           # Motor B enable (PWM)
    "IN3": 21,           # Motor B direction
    "IN4": 23,           # Motor B direction
    "PWM_FREQUENCY": 1000
}

# Gyroscope Configuration
GYRO_CONFIG = {
    "BUS_NUMBER": 1,
    "ADDRESS": 0x68,
    "PWR_MGMT_REG": 0x6B,
    "CALIBRATION_SAMPLES": 100
}

# PID Controller Parameters
PID_CONFIG = {
    "STRAIGHT": {
        "KP": 0.3,
        "KI": 0.1,
        "KD": 0.05,
        "DEADBAND": 0.1,
        "INTEGRAL_MAX": 20.0
    },
    "ROTATION": {
        "KP": 0.5,
        "KI": 0.0,
        "KD": 0.1,
        "DEADBAND": 0.01,
        "INTEGRAL_MAX": 10.0
    }
}

# General Movement Settings
MOVEMENT_CONFIG = {
    "LOOP_DELAY": 0.01,
    "DEFAULT_SPEED": 80,
    "DEFAULT_ROTATION_SPEED": 70
}