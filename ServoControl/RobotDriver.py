import json
import os
import time
from adafruit_servokit import ServoKit
from Utils.Logger import get_logger

class RobotDriver:
    """
    Hardware driver class for controlling the PCA9685 PWM controller
    and mapping logical angles to physical servo pulses.
    """
    def __init__(self, config_path=None):
        self.logger = get_logger("RobotDriver")

        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "../armconfig.json")

        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            self.logger.info(f"Successfully loaded armconfig: {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load armconfig: {e}")
            raise

        # Initialize PCA9685 via Adafruit ServoKit
        try:
            self.kit = ServoKit(channels=16)
            self.logger.info("PCA9685 hardware initialized successfully")
        except Exception as e:
            self.logger.error(f"Hardware initialization failed. Check I2C wiring: {e}")
            raise

        self._setup_servos()

    def _setup_servos(self):
        for servo in self.config['servos']:
            ch = servo['channel']
            min_p = servo['min_pulse']
            max_p = servo['max_pulse']
            self.kit.servo[ch].set_pulse_width_range(min_p, max_p)
            self.logger.debug(f"Configured {servo['id']} (Ch:{ch}) with pulse {min_p}-{max_p}")

    def execute_commands(self, commands):

        for s_id, target_angle in commands.items():
            servo_info = next((s for s in self.config['servos'] if s['id'] == s_id), None)

            if servo_info:
                channel = servo_info['channel']

                safe_angle = max(servo_info['min_limit'], min(servo_info['max_limit'], target_angle))

                if abs(safe_angle - target_angle) > 0.01:
                    self.logger.warning(f"Joint {s_id} target {target_angle:.2f}° out of bounds. Clipped to {safe_angle:.2f}°")

                self.kit.servo[channel].angle = safe_angle
                self.logger.info(f"Moving {s_id} (Ch:{channel}) to {safe_angle:.2f}°")
            else:
                self.logger.error(f"Servo ID '{s_id}' not found in configuration.")

    def go_home(self):
        self.logger.info("Returning to HOME position (Zero Offset)...")
        home_cmds = {s['id']: s['zero_offset'] for s in self.config['servos']}
        self.execute_commands(home_cmds)

if __name__ == "__main__":
    try:
        arm = RobotDriver()
        arm.go_home()
    except Exception as e:
        pass
