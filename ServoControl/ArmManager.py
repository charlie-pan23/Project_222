import time
import json
import os
import numpy as np
from ServoControl.Servo import ServoDevice
from Utils.Logger import get_logger

logger = get_logger(__name__)


class ArmManager:

    def __init__(self, pca_channels, config_file="armconfig.json"):
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # project_root = os.path.dirname(current_dir)
        # config_path = os.path.join(project_root, config_file)
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        # Initialize exactly 6 servos as a fixed list for faster access
        self.servos = []
        for cfg in config_data['servos']:
            s = ServoDevice(
                pca_channels=pca_channels,
                channel=cfg['channel']
            )
            # Injecting calibration parameters directly
            s.offset = 90 + cfg['zero_adjusting']
            s.direction = cfg['direction']
            s.min_limit = cfg['min_limit']
            s.max_limit = cfg['max_limit']
            self.servos.append(s)

        self.servo_count = 6
        logger.info("6-axis hardware interface initialized.")

    def arm_init(self):
        """Move all servos to their zero positions."""
        for s in self.servos:
            s.smooth_move(s.offset)
        logger.info("Arm initialized to zero positions.")

    def move_arm(self, angles):
        """
        Move the arm to the specified angles.
        :param angles: List of 4 angles in degrees for J1 to J4.
        """
        if len(angles) != 4:
            logger.error(f"Expected 4 angles, got {len(angles)}.")
            return

        target_angles = []
        for i in range(4):
            target = self.servos[i].offset + (float(angles[i]) * self.servos[i].direction)
            target_angles.append(target)

        # Security check
        for i in range(4):
            if self.servos[i].current_angle is None:
                logger.warning(f"Servo {i} position unknown, defaulting to offset.")
                self.servos[i].current_angle = self.servos[i].offset

        # calculating
        current_positions = [self.servos[i].current_angle for i in range(4)]
        diffs = [target_angles[i] - current_positions[i] for i in range(4)]

        # speed
        max_diff = max(abs(d) for d in diffs)
        steps = int(max_diff)

        # move
        if steps > 0:
            increments = [d / steps for d in diffs]

            for s in range(steps):
                for j in range(4):
                    next_pos = current_positions[j] + (increments[j] * (s + 1))
                    self.servos[j].move_to(next_pos)
                time.sleep(0.02)

        for j in range(4):
            self.servos[j].move_to(target_angles[j])

        logger.info(f"Arm moved to angles (absolute): {[round(a, 2) for a in target_angles]}")

    def set_gripper(self, status):
        """
        Directly control the gripper (S5).
        :param status: 0 for "close", 30 for "open".
        """
        if status == "open":
            angle = 45
        elif status == "close":
            angle = 25
        else:
            logger.error(f"Wrong gripper statu {status}")

        self.servos[5].smooth_move(angle,20)

    def release_all(self):
        """Stop PWM signal to all 6 servos."""
        for s in self.servos:
            s.release()
        logger.info("All 6 axes powered down.")
