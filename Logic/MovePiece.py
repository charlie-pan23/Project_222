from ServoControl.ArmManager import ArmManager
from ServoControl.IK import solve_ik
import board
import busio
from adafruit_pca9685 import PCA9685
import time

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

Coordinate = [8][8]
class MovePiece:

    Moving = False

def get_status(self):
    return Moving







Arm1 = ArmManager(pca_channels=pca.channels)

Arm1.arm_init()
time.sleep(1)

Arm1.set_gripper("open")
time.sleep(1)
Arm1.set_gripper("close")

target = [10,0,8]
angles, status = solve_ik(*target)
if angles:
    Arm1.move_arm(angles)
else:
    print(f"IK Failed: {status}")




