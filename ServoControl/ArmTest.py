from ServoControl.ArmManager import ArmManager
from ServoControl.IK import solve_ik
import board
import busio
from adafruit_pca9685 import PCA9685
import time

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

Arm1 = ArmManager(pca_channels=pca.channels)

Arm1.arm_init()
time.sleep(1)

target = [25,0,5]
angles, status = solve_ik(*target)
if angles:
    Arm1.move_arm(angles)
else:
    print(f"IK Failed: {status}")

angle = (Arm1.servos[0].current_angle, Arm1.servos[1].current_angle, Arm1.servos[2].current_angle, Arm1.servos[3].current_angle)

print(angle[0], angle[1], angle[2], angle[3])



