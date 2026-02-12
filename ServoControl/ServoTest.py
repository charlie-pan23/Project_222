# Test script
import time
import board
from adafruit_pca9685 import PCA9685
from ServoControl.Servo import ServoDevice
from Utils.Logger import get_logger

logger = get_logger(__name__)

i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 50

s0_yaw = ServoDevice(pca.channels, channel=0)
s1_pitch = ServoDevice(pca.channels, channel=1)
s2_pitch = ServoDevice(pca.channels, channel=2)
s3_pitch = ServoDevice(pca.channels, channel=4)
s4_roll = ServoDevice(pca.channels, channel=5)
s5_gripper = ServoDevice(pca.channels, channel=8)

# Initialize to a known position
s0_yaw.init_to(82)
s1_pitch.init_to(102)
s2_pitch.init_to(75)
s3_pitch.init_to(95)
s4_roll.init_to(160)
s5_gripper.init_to(20)
