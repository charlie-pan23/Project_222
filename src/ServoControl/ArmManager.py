import time
import json
from ServoControl.Servo import ServoDevice
from Utils.Logger import get_logger
import os

logger = get_logger(__name__)


class ArmManager:

    def __init__(self, pca_channels, config_file="armconfig.json"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        config_path = os.path.join(src_dir, config_file)

        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Missing configuration at {config_path}")

        with open(config_path, 'r') as f:
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
        self.current_pos = [0, 0, 0]  # Default position for the end effector
        self.current_angles = [0, 0, 0, 0, 0, 0]
        logger.info("6-axis hardware interface initialized.")

    def arm_init(self):
        """Move all servos to their zero positions."""
        for s in self.servos:
            s.smooth_move(s.offset)
        for i in range(6):
            self.current_angles[i] = self.servos[i].offset
        self.current_pos = [15.5, 0, 5] # Default "home" position
        logger.info("Arm initialized to zero positions.")

    def release_all(self):
        """Stop PWM signal to all 6 servos."""
        for s in self.servos:
            s.release()
        logger.info("All 6 axes powered down.")

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

        for i in range(4):
            self.current_angles[i] = target_angles[i]
        logger.info(f"Arm moved to angles (absolute): {[round(a, 2) for a in target_angles]}")

    def arm_rest(self):
        """Move the arm to a predefined "rest" position."""
        rest_angles = [0, -50, -30, 0]  # Define your rest angles here
        self.move_arm(rest_angles)
        logger.info("Arm moved to rest position.")

    def goto_coordinate(self, x, y, z):
        """
        Move the arm to the specified XYZ coordinate.
        :param x: X coordinate in cm
        :param y: Y coordinate in cm
        :param z: Z coordinate in cm
        """
        from ServoControl.kinematics import solve_ik
        angles, status = solve_ik(x, y, z)

        if status == "Success":
            self.move_arm(angles)
            self.current_pos = [x, y, z]
            return True
        else:
            logger.error(f"Move failed: {status}")
            return False

    def set_gripper(self, status):
        """
        Directly control the gripper (S5).
        :param status: 0 for "close", 30 for "open".
        """
        if status == "open":
            angle = 30
        elif status == "close":
            angle = 15
        else:
            logger.error(f"Wrong gripper status {status}")

        self.servos[5].smooth_move(angle,20)
        self.current_angles[5] = angle

    def get_current_pos(self):
        return self.current_pos

    def get_current_angles(self):
        return self.current_angles

    def grip(self):
        '''
        grab the piece at current xy coordinate, move up to safe height after grab
        '''
        x, y, _ = self.current_pos
        logger.info(f"Executing GRIP at x={x}, y={y}")

        self.goto_coordinate(x, y, 5)
        time.sleep(0.5)
        self.set_gripper("open")
        time.sleep(0.5)
        self.goto_coordinate(x, y, 2)
        time.sleep(0.5)
        self.set_gripper("close")
        time.sleep(0.5)
        self.goto_coordinate(x, y, 5)

    def loose(self):
        """
        release the piece at current xy coordinate, move up to safe height after release"""
        x, y, _ = self.current_pos
        logger.info(f"Executing LOOSE at x={x}, y={y}")

        self.goto_coordinate(x, y, 2)
        time.sleep(0.5)
        self.set_gripper("open")
        time.sleep(0.5)
        self.goto_coordinate(x, y, 5)
        time.sleep(0.5)
        self.set_gripper("close")

