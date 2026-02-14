import time
from ArmManager import ArmManager
from BoardConfig import BoardManager
from adafruit_pca9685 import PCA9685
import board
import busio

def run_calibration():
    # Initialize I2C and PCA9685
    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50

    # Initialize Managers
    # Assuming armconfig.json is in the same directory
    arm = ArmManager(pca.channels, config_file="armconfig.json")
    bm = BoardManager()

    print("--- Robotic Arm Calibration Tool ---")
    print("Initializing arm to home position...")
    arm.arm_init() # Moves to offset positions and sets current_pos to [15.5, 0, 5]

    try:
        # Step 1: Verify a1
        print("\nStep 1: Moving to a1 (First corner)...")
        # Get coordinates for a1 based on current side (defaulting to black)
        a1_pos = bm.get_slot_coords("black", "a1")
        if arm.goto_coordinate(*a1_pos):
            print(f"Arm reached a1 at {a1_pos[:2]}. Please check alignment.")
            input("Press Enter to continue to a8...")
        else:
            print("Failed to reach a1. Check IK limits.")

        # Step 2: Verify a8
        print("\nStep 2: Moving to a8 (Last corner of the same file)...")
        a8_pos = bm.get_slot_coords("black", "a8")
        if arm.goto_coordinate(*a8_pos):
            print(f"Arm reached a8 at {a8_pos[:2]}. Please check alignment.")
            input("Verification complete. Press Enter to return home and exit...")
        else:
            print("Failed to reach a8. Check IK limits.")

    except KeyboardInterrupt:
        print("\nCalibration interrupted by user.")
    finally:
        # Return to home and release power
        arm.arm_init()
        arm.release_all() # Stops PWM signals to reduce heat
        print("System safely shut down.")

if __name__ == "__main__":
    run_calibration()
