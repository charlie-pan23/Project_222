import time
import json
import numpy as np
from ServoControl.Servo import ServoDevice
from Utils.Logger import get_logger

logger = get_logger(__name__)

class ArmManager:
    def __init__(self, pca_channels, config_file="arm_config.json"):
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        # Initialize exactly 6 servos as a fixed list for faster access
        self.servos = []
        for cfg in config_data['servos']:
            s = ServoDevice(
                pca_channels=pca_channels,
                channel=cfg['channel'],
                min_pulse=cfg.get('min_pulse', 500),
                max_pulse=cfg.get('max_pulse', 2400)
            )
            # Injecting calibration parameters directly
            s.zero_offset = cfg['zero_offset']
            s.direction = cfg['direction']
            s.min_limit = cfg['min_limit']
            s.max_limit = cfg['max_limit']
            self.servos.append(s)

        self.servo_count = 6
        logger.info("6-axis hardware interface initialized.")

    def move_to_radians(self, target_radians, duration=1.5):
        """
        Synchronized movement for exactly 6 axes.
        :param target_radians: List or array of 6 radians from IK solver.
        :param duration: Time in seconds for the complete motion.
        """
        if len(target_radians) != self.servo_count:
            logger.error(f"Expected 6 radians, got {len(target_radians)}")
            return

        # Pre-calculate target angles to avoid repeated computation in the loop
        target_angles = np.zeros(self.servo_count)
        start_angles = np.zeros(self.servo_count)

        for i in range(self.servo_count):
            # Transformation: Physical_Angle = (Math_Radian_to_Degree * Direction) + Zero_Offset
            deg = np.degrees(target_radians[i]) * self.servos[i].direction + self.servos[i].zero_offset
            # Apply physical safety boundary
            target_angles[i] = np.clip(deg, self.servos[i].min_limit, self.servos[i].max_limit)

            # Fetch current position for interpolation
            curr = self.servos[i].get_current_angle()
            start_angles[i] = curr if curr is not None else target_angles[i]

        # Execution loop
        hz = 50
        steps = max(1, int(duration * hz))
        step_interval = 1 / hz

        for step in range(1, steps + 1):
            fraction = step / steps
            # Simultaneously update all 6 axes
            for i in range(self.servo_count):
                # Linear formula: Start + (Total_Distance * Progress_Percentage)
                interp_angle = start_angles[i] + (target_angles[i] - start_angles[i]) * fraction
                self.servos[i].move_to(interp_angle)
            time.sleep(step_interval)

    def set_gripper(self, angle):
        """
        Directly control the gripper (S5).
        :param angle: 20 for close, 45 for open.
        """
        self.servos[5].move_to(angle)

    def release_all(self):
        """Stop PWM signal to all 6 servos."""
        for s in self.servos:
            s.release()
        logger.info("All 6 axes powered down.")
