import time
import board
from adafruit_pca9685 import PCA9685
from ServoControl.Servo import ServoDevice
from Utils.Logger import get_logger

logger = get_logger(__name__)

i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 50

servoYaw = ServoDevice(pca.channels, channel=0)
servoPitch1 = ServoDevice(pca.channels, channel=1)
servoPitch2 = ServoDevice(pca.channels, channel=2)
servoPitch3 = ServoDevice(pca.channels, channel=4)
servoRoll = ServoDevice(pca.channels, channel=5)
servoGripper = ServoDevice(pca.channels, channel=8)

servoYaw.init_to(82)
servoPitch1.init_to(102)
servoPitch2.init_to(75)
servoPitch3.init_to(5)
servoRoll.init_to(160)
servoGripper.init_to(20)


