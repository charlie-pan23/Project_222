import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ServoControl.IK import get_servo_command
from ServoControl.RobotDriver import RobotDriver
from Utils.Logger import get_logger

logger = get_logger("CoordinateTest")

def main():
    try:
        # Initialize the hardware driver
        arm = RobotDriver()
        logger.info("System operational. Coordinate Frame: X(Right), Y(Forward), Z(Up)")

        while True:
            raw_input = input("\nEnter Target XYZ or 'q' to quit: ").strip()

            if raw_input.lower() == 'q':
                logger.info("Test terminated by user.")
                break

            try:
                # Parse raw input into a list of floats
                coords = [float(x) for x in raw_input.split()]
                if len(coords) != 3:
                    logger.warning("Invalid input. Required: 3 numerical values (x y z)")
                    continue

                # 1. Kinematics Layer: Resolve XYZ to joint angles
                logger.debug(f"Computing Inverse Kinematics for target: {coords}")
                angles = get_servo_command(coords)

                # 2. Driver Layer: Execute physical motion
                arm.execute_commands(angles)

            except ValueError:
                logger.error("Non-numeric input detected. Please enter numbers only.")
            except Exception as e:
                logger.error(f"Failed to process coordinate: {e}")

    except KeyboardInterrupt:
        print("\n")
        logger.info("Program stopped manually.")

if __name__ == "__main__":
    main()
