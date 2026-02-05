import time
import board
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

i2c = board.I2C()  # uses board.SCL and board.SDA

pca = PCA9685(i2c)
pca.frequency = 50

servo0 = servo.Servo(pca.channels[8])

# We sleep in the loops to give the servo time to move into position.
for i in range(45):
    servo0.angle = i
    time.sleep(0.03)
for i in range(45):
    servo0.angle = 45 - i
    time.sleep(0.03)

pca.deinit()
