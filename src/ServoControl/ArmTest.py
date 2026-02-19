# Test
from ServoControl.ArmManager import ArmManager
from ServoControl.kinematics import solve_ik
from ServoControl.BoardConfig import BoardManager
import board
import busio
from adafruit_pca9685 import PCA9685
import time

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

Arm1 = ArmManager(pca_channels=pca.channels)

# init
Arm1.arm_init()
time.sleep(1)

Arm1.arm_rest()
time.sleep(1)

# grab piece
target1 = [20.5,2,5]
angles1, status1 = solve_ik(*target1)
Arm1.move_arm(angles1)
time.sleep(1)

Arm1.set_gripper("open")
time.sleep(1)

target2 = [20.5,2,2]
angles2, status2 = solve_ik(*target2)
Arm1.move_arm(angles2)
time.sleep(1)

Arm1.set_gripper("close")
time.sleep(1)

Arm1.move_arm(angles1)
time.sleep(1)

# place piece
target1 = [16,-2,5]
angles1, status1 = solve_ik(*target1)
Arm1.move_arm(angles1)
time.sleep(1)

target2 = [16,-2,2]
angles2, status2 = solve_ik(*target2)
Arm1.move_arm(angles2)
time.sleep(1)

Arm1.set_gripper("open")
time.sleep(1)

Arm1.move_arm(angles1)
time.sleep(1)

# def physical_test():
#     # 1. Hardware Setup
#     i2c = busio.I2C(board.SCL, board.SDA)
#     pca = PCA9685(i2c)
#     pca.frequency = 50

#     # 2. Initialize Managers
#     arm = ArmManager(pca.channels, config_file="armconfig.json")
#     bm = BoardManager()
#     arm.arm_rest()  # Move to rest position first
#     arm.arm_init()  # Home the arm at the start of the test

#     # 3. Define Test Sequence (Notation for Black side)
#     # Target sequence: h1 -> h8 -> h5 -> d5 -> g5
#     test_points = ["h1", "h8", "h5", "d5", "g5"]
#     side = "black"

#     print(f"--- Starting Physical Accuracy Test (Side: {side}) ---")
#     arm.arm_init() # Home the arm first

#     try:
#         for point in test_points:
#             # Get coordinates from your BoardConfig
#             target_pos = bm.get_slot_coords(side, point)

#             print(f"\nMoving to {point} | Coordinates: {target_pos[:2]}")

#             # Move to target at safe Z height (5.0cm)
#             if arm.goto_coordinate(*target_pos):
#                 print(f"Reached {point}. Please verify the gripper is centered over the square.")
#                 # Optional: Lower to Z=2 to check exact center proximity
#                 # arm.goto_coordinate(target_pos[0], target_pos[1], 2.0)

#                 input("Press Enter to move to the next point...")

#                 # Back to safe height if you lowered it
#                 # arm.goto_coordinate(target_pos[0], target_pos[1], 5.0)
#             else:
#                 print(f"Error: Could not calculate IK for {point}. Out of range?")

#     except KeyboardInterrupt:
#         print("\nTest stopped by user.")
#     finally:
#         print("\nReturning to home position...")
#         arm.arm_init()
#         arm.release_all()
#         print("Test complete.")

# if __name__ == "__main__":
#     physical_test()




