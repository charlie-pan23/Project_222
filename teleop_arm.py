import sys
import os
import time
import tty
import termios

# Ensure path to ServoControl is accessible
sys.path.append(os.path.join(os.path.dirname(__file__), 'ServoControl'))

from ServoControl.IK import get_servo_command
from ServoControl.RobotDriver import RobotDriver
from Utils.Logger import get_logger

logger = get_logger("TeleopArm")

def getch():
    """ Read a single keypress from stdin without needing Enter. """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    try:
        # Initialize Driver
        arm = RobotDriver()

        # Starting Position (Your Initialization State)
        # Based on your URDF: s1 up, s2 forward, s3 down
        # Roughly corresponds to this coordinate (in meters):
        curr_x = 0.125  # 1.5cm offset + 10.5cm arm + 0.5cm tweak
        curr_y = 0.01   # 1cm shoulder offset
        curr_z = 0.10   # 7cm base + 2.5cm offset + some height

        step = 0.005 # 5mm per press

        logger.info("Control Mode: W/S (X), A/D (Y), P/L (Z) | ESC to exit")
        logger.info(f"Initial Target: X={curr_x}, Y={curr_y}, Z={curr_z}")

        while True:
            char = getch()

            if char.lower() == 'w': curr_x += step
            elif char.lower() == 's': curr_x -= step
            elif char.lower() == 'a': curr_y += step # Y+ is Left in standard ROS
            elif char.lower() == 'd': curr_y -= step
            elif char.lower() == 'p': curr_z += step
            elif char.lower() == 'l': curr_z -= step
            elif char == '\x1b': # ESC key
                logger.info("Exiting Teleop Mode...")
                break
            else:
                continue

            # 1. Update Target
            target = [round(curr_x, 3), round(curr_y, 3), round(curr_z, 3)]

            try:
                # 2. Compute IK
                angles = get_servo_command(target)

                # 3. Execute Movement
                arm.execute_commands(angles)

                logger.info(f"Pos: {target} | Angles: {list(angles.values())}")

            except Exception as e:
                logger.error(f"Target {target} unreachable: {e}")
                # Revert coordinate if unreachable
                if char.lower() == 'w': curr_x -= step
                elif char.lower() == 's': curr_x += step
                # ... repeat for others if needed to stay in bounds

    except KeyboardInterrupt:
        logger.info("Teleop stopped.")
    except Exception as e:
        logger.error(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
