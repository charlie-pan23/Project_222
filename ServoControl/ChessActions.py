from ServoControl.ArmManager import ArmManager
from ServoControl.IK import solve_ik
import board
import busio
from adafruit_pca9685 import PCA9685
import time

class ChessActions:

    def pick_up(self, target):

        i2c = busio.I2C(board.SCL, board.SDA)
        pca = PCA9685(i2c)
        pca.frequency = 50
        Arm = ArmManager(pca_channels=pca.channels)

        target1 = [20.5,2,5]
        angles1, status1 = solve_ik(*target1)
        Arm.move_arm(angles1)
        time.sleep(1)

        Arm.set_gripper("open")
        time.sleep(1)

        target2 = [20.5,2,2]
        angles2, status2 = solve_ik(*target2)
        Arm.move_arm(angles2)
        time.sleep(1)

        Arm.set_gripper("close")
        time.sleep(1)

        Arm1.move_arm(angles1)
        time.sleep(1)
