from Utils.Logger import get_logger

# Initialize logger for tracking calibration steps
logger = get_logger(__name__)

class ArmCalibrator:
    """
    Handles the physical alignment of the robotic arm to the chess board corners.
    Instead of re-initializing hardware, it reuses the existing ArmAction instance.
    """
    def __init__(self, arm_action):
        """
        Initializes with an existing ArmAction object to reuse established hardware links.

        """
        self.arm_action = arm_action

        # Reuse the manager and board objects from the injected arm_action
        self.manager = arm_action.manager
        self.board = arm_action.board

        # Define the 4 corners of the board for physical square alignment
        # These points represent the limits of the playable area.
        self.points = ['a4', 'h4', 'a1', 'h1']
        self.current_idx = 0

        # Safe travel height in cm to avoid hitting pieces during calibration
        self.Z_SAFE = 5.0

    def move_to_next(self):
        """
        Cycles the arm to the next corner point in the self.points list.
        Triggered by user input in the main loop.
        """
        point = self.points[self.current_idx]

        # Calculate real-world coordinates for the target square
        # Defaulting to 'white' perspective for baseline alignment.
        coords = self.board.get_slot_coords("white", point)

        logger.info(f"Calibration: Moving to point {point.upper()} at coordinates {coords}")

        # Execute movement to the coordinate at a safe height
        # The goto_coordinate method handles the Inverse Kinematics (IK) internally.
        success = self.manager.goto_coordinate(coords[0], coords[1], self.Z_SAFE)

        # Update index for the next cycle (loops back to 0 after point 3)
        self.current_idx = (self.current_idx + 1) % len(self.points)

        return point.upper(), success

    def reset_position(self):
        """
        Returns the arm to its initial 'home' position.
        Useful after finishing calibration.
        """
        logger.info("Calibration finished. Resetting arm to home position.")
        self.manager.arm_init()
