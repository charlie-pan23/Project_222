import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ServoControl.ArmManager import ArmManager
from ServoControl.BoardConfig import BoardManager
import board
import busio
from adafruit_pca9685 import PCA9685

def board_test():
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        pca = PCA9685(i2c)
        pca.frequency = 50
        pca_channels = pca.channels
        print("Hardware I2C initialized.")
    except Exception as e:
        print(f"Hardware error: {e}")
        return

    manager = ArmManager(pca_channels=pca_channels)
    board_mgr = BoardManager()

    manager.arm_init()
    print("Arm initialized to home position.")

    print("\n" + "="*30)
    print("BOARD COORDINATE TEST TOOL")
    print("Commands: Enter a square (e.g., 'a1', 'h8') to move.")
    print("Type 'exit' to stop.")
    print("="*30 + "\n")

    Z_SAFE = 6.0
    Z_CHECK = 1.5

    try:
        while True:
            target = input("Target Square: ").lower().strip()

            if target == 'exit':
                break

            try:
                coords = board_mgr.get_slot_coords("white", target)
                x, y = coords[0], coords[1]
                print(f"Moving to {target.upper()}: x={x}, y={y}")

                manager.goto_coordinate(x, y, Z_SAFE)
                time.sleep(0.5)

                manager.goto_coordinate(x, y, Z_CHECK)
                print(f"Check alignment for {target.upper()}.")

                input("Press Enter to lift arm...")
                manager.goto_coordinate(x, y, Z_SAFE)

            except Exception as e:
                print(f"Invalid square or movement error: {e}")

    finally:
        manager.arm_rest()
        print("Test finished. Arm moved to rest.")

if __name__ == "__main__":
    board_test()
