import time
from adafruit_motor import servo
from Utils.Logger import get_logger

logger = get_logger(__name__)

class ServoDevice:
    """
    General-purpose servo control base class for a single servo connected to PCA9685.
    """
    def __init__(self, pca_channels, channel, min_pulse=500, max_pulse=2400, actuation_range=180):
        """
        Initialize the servo
        :param pca_channels: The 'channels' attribute of a PCA9685 object
        :param channel: Physical channel number on the board (0-15)
        :param min_pulse: Minimum pulse width (default 500)
        :param max_pulse: Maximum pulse width (default 2400)
        :param actuation_range: Total physical range of the servo in degrees (default 180)
        """
        self.channel_num = channel
        self.servo = servo.Servo(
            pca_channels[channel],
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            actuation_range=actuation_range
        )
        self.current_angle = None
        self.range = actuation_range

    def move_to(self, angle):
        if angle < 0: angle = 0
        if angle > self.range: angle = self.range

        self.servo.angle = angle
        self.current_angle = angle

    def set_fraction(self, fraction):
        """
        Control position using a percentage from 0.0 to 1.0
        """
        if 0.0 <= fraction <= 1.0:
            self.servo.fraction = fraction
            self.current_angle = fraction * self.range

    def smooth_move(self, target_angle, speed=50):
        """
        Move to the target angle smoothly
        :param target_angle: Target angle in degrees
        :param speed: Speed of movement in degrees per second (default 50)
        """
        if self.current_angle is None:
            self.move_to(target_angle)
            self.current_angle = target_angle
            return

        start = int(self.current_angle)
        end = int(target_angle)
        step = 1 if end > start else -1
        delay = 1 / speed

        for i in range(start, end + step, step):
            self.move_to(i)
            time.sleep(delay)

    def init_to(self, angle, speed=50):
        """
        Initializes the servo to a starting angle.
        If the current position is unknown (None), it moves directly to the target
        to establish a reference point for software tracking.
        """
        logger.info(f"Initializing servo on channel {self.channel_num} to {angle} degrees...")
        self.smooth_move(angle, speed)

    def get_current_angle(self):
        """
        Returns the last commanded angle (Software Tracking).
        Note: 3-wired servos do not provide real-time hardware feedback.
        """
        return self.current_angle

    def release(self):
        """
        Release the servo (stop sending PWM signals)
        This reduces heat and jitter noise, but the servo will no longer hold its position
        """
        self.servo.angle = None
        self.current_angle = None
