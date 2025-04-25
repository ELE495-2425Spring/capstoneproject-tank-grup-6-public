import RPi.GPIO as GPIO
import time
from .gyro_noth import GyroSensor2

class Araba:
    def __init__(self, pwm_a=23, ain1=21, ain2=19, pwm_b=11, bin1=15, bin2=13, freq=1000):
        self.PWMA = pwm_a
        self.AIN1 = ain1
        self.AIN2 = ain2
        self.PWMB = pwm_b
        self.BIN1 = bin1
        self.BIN2 = bin2
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        self.motor_pins = [self.PWMA, self.AIN1, self.AIN2, self.PWMB, self.BIN1, self.BIN2]
        for pin in self.motor_pins:
            GPIO.setup(pin, GPIO.OUT)
        self.pwm_a = GPIO.PWM(self.PWMA, freq)
        self.pwm_b = GPIO.PWM(self.PWMB, freq)
        self.pwm_a.start(0)
        self.pwm_b.start(0)

    def set_motor(self, a1, a2, b1, b2, duty_cycle=100):
        duty_cycle = max(0, min(100, duty_cycle))
        GPIO.output(self.AIN1, a1)
        GPIO.output(self.AIN2, a2)
        GPIO.output(self.BIN1, b1)
        GPIO.output(self.BIN2, b2)
        self.pwm_a.ChangeDutyCycle(duty_cycle)
        self.pwm_b.ChangeDutyCycle(duty_cycle)

    def stop(self):
        self.pwm_a.ChangeDutyCycle(0)
        self.pwm_b.ChangeDutyCycle(0)
        GPIO.output(self.AIN1, GPIO.LOW)
        GPIO.output(self.AIN2, GPIO.LOW)
        GPIO.output(self.BIN1, GPIO.LOW)
        GPIO.output(self.BIN2, GPIO.LOW)

    def ileri(self, saniye, duty_cycle=100):
        self.set_motor(GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW, duty_cycle)
        time.sleep(saniye)
        self.stop()

    def geri(self, saniye, duty_cycle=100):
        self.set_motor(GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.HIGH, duty_cycle)
        time.sleep(saniye)
        self.stop()

    def _pid_turn(self, gyro_sensor: GyroSensor2, target_angle: float, direction: str,
                  Kp=1.0, Ki=0.0, Kd=0.0, max_duty=60, calibrate_before_turn=False):
        """
        Generic PID-based turn helper.
        direction: 'right' or 'left'.
        """
        if calibrate_before_turn:
            self.stop()
            gyro_sensor.calibrate()

        # Reset tracking
        gyro_sensor.angle = 0.0
        integral = 0.0
        prev_error = target_angle
        prev_time = time.time()

        # Initial rotation direction setup
        if direction == 'right':
            motor_dir = (GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.LOW)
        else:  # left
            motor_dir = (GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.HIGH)

        # PID loop
        while True:
            current_time = time.time()
            dt = current_time - prev_time
            if dt <= 0:
                dt = 0.001
            prev_time = current_time

            # Measure current angle
            rate = gyro_sensor.get_smoothed_gyro()
            # Integrate angle; rate sign indicates direction
            gyro_sensor.angle += rate * dt
            current_angle = abs(gyro_sensor.angle)

            # Compute error (remaining angle)
            error = abs(target_angle) - current_angle
            integral += error * dt
            derivative = (error - prev_error) / dt
            prev_error = error

            # PID output
            output = Kp * error + Ki * integral + Kd * derivative
            duty = min(max_duty, max(55, abs(output)))  # ensure minimum duty

            # Apply motor command
            self.set_motor(*motor_dir, duty)

            # Check if within tolerance
            if error <= 1.0:  # 1 degree tolerance
                break

            time.sleep(0.005)

        self.stop()

    def saga_don(self, gyro_sensor: GyroSensor2, derece: float, 
                 Kp=1.0, Ki=0.0, Kd=0.0, max_duty=60, calibrate_before_turn=False):
        """
        Turn right by 'derece' degrees using a PID controller.
        """
        self._pid_turn(gyro_sensor, derece, 'right', Kp, Ki, Kd, max_duty, calibrate_before_turn)

    def sola_don(self, gyro_sensor: GyroSensor2, derece: float,
                 Kp=1.0, Ki=0.0, Kd=0.0, max_duty=60, calibrate_before_turn=False):
        """
        Turn left by 'derece' degrees using a PID controller.
        """
        self._pid_turn(gyro_sensor, derece, 'left', Kp, Ki, Kd, max_duty, calibrate_before_turn)

    def cleanup(self):
        self.pwm_a.stop()
        self.pwm_b.stop()
        GPIO.cleanup()
