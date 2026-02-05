import time
import board
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

i2c = board.I2C()  # uses board.SCL and board.SDA

pca = PCA9685(i2c)
pca.frequency = 50

servo0 = servo.Servo(pca.channels[0])

# We sleep in the loops to give the servo time to move into position.
for i in range(180):
    servo0.angle = i
    time.sleep(0.03)
for i in range(180):
    servo0.angle = 180 - i
    time.sleep(0.03)

# You can also specify the movement fractionally.
fraction = 0.0
while fraction < 1.0:
    servo0.fraction = fraction
    fraction += 0.01
    time.sleep(0.03)

pca.deinit()
