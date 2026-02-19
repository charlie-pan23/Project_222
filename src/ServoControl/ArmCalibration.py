import time
from ServoControl.ArmManager import ArmManager
from ServoControl.BoardConfig import BoardManager
from Utils.Logger import get_logger

logger = get_logger(__name__)

class ArmCalibrator:
    """Handles the physical alignment of the arm to the board corners."""
    def __init__(self, pca_channels):
        # Initialize hardware and coordinate mapping
        self.manager = ArmManager(pca_channels=pca_channels)
        self.board = BoardManager()

        # 4 corners to check physical square alignment
        self.points = ['a8', 'h8', 'a1', 'h1']
        self.current_idx = 0
        self.Z_SAFE = 5.0 # Travel height

    def move_to_next(self):
        """Cycles to the next corner point on Space press."""
        point = self.points[self.current_idx]

        # Get real-world coordinates for the target square
        # Using 'white' perspective as default for calibration
        coords = self.board.get_slot_coords("white", point)

        logger.info(f"Calibration: Moving to {point.upper()} at {coords}")

        # Move arm to the target at a safe height
        success = self.manager.goto_coordinate(coords[0], coords[1], self.Z_SAFE)

        # Increment index for the next call
        self.current_idx = (self.current_idx + 1) % len(self.points)
        return point.upper(), success

    def reset_position(self):
        """Returns arm to init position."""
        self.manager.arm_init()

if __name__ == "__main__":
    # Example standalone test (requires hardware connection)
    pass
