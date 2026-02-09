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
                channel=cfg['channel']
            )
            # Injecting calibration parameters directly
            s.zero_offset = 90 + cfg['zero_adjusting']
            s.direction = cfg['direction']
            s.min_limit = cfg['min_limit']
            s.max_limit = cfg['max_limit']
            self.servos.append(s)

        self.servo_count = 6
        logger.info("6-axis hardware interface initialized.")

    def arm_init(self):
        """Move all servos to their zero positions."""
        for s in self.servos:
            s.smooth_move(s.zero_offset)
        logger.info("Arm initialized to zero positions.")

    def move_arm(self, angles):
        """
        Move the arm to the specified angles.
        :param angles: List of 4 angles in degrees for J1 to J4.
        """
        if len(angles) != 4:
            logger.error(f"Expected 4 angles, got {len(angles)}.")
            return
        # Apply zero offsets
        angles = [angles[i] + self.servos[i].zero_offset for i in range(4)]
        current_angles = [s.current_angle for s in self.servos[:4]]
        diff_angles = [angles[i] - current_angles[i] for i in range(4)]
        separate = (max(abs(diff_angles)) - min(abs(diff_angles))) / 2
        move_angles = (diff_angles[i] / separate for i in range(4))
        for i in range(int(separate)):
            for j in range(4):
                self.servos[j].move_to(current_angles[j] + move_angles[j])
            current_angles = [s.current_angle for s in self.servos[:4]]
            time.sleep(0.05)  # Adjust sleep for smoother movement
        for j in range(4):
                self.servos[j].move_to(angles[j])

        logger.info(f"Arm moved to angles: {angles}")

    def set_gripper(self, status):
        """
        Directly control the gripper (S5).
        :param status: 0 for "close", 30 for "open".
        """
        angle = self.servos[5].offset + (30 if status == "open" else 0)
        self.servos[5].move_to(angle)

    def release_all(self):
        """Stop PWM signal to all 6 servos."""
        for s in self.servos:
            s.release()
        logger.info("All 6 axes powered down.")
