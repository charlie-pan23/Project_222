import time
from ServoControl.ArmManager import ArmManager
from ServoControl.BoardConfig import BoardManager
from Utils.Logger import get_logger

logger = get_logger(__name__)

class ArmAction:
    """
    High-level controller to bridge UI/Logic with physical arm movements.
    Translates UCI moves (e.g., 'e2e4') into coordinated servo actions.
    """
    def __init__(self, pca_channels):
        # Initialize the underlying manager with your PCA9685 channels
        self.manager = ArmManager(pca_channels=pca_channels)
        self.board = BoardManager()

        # Consistent heights as per your requirements
        self.Z_SAFE = 5.0 # Height for safe travel
        self.Z_PICK = 2.0 # Height for gripping/releasing pieces

    def initialize(self):
        """Initializes servos and moves to 90-degree start position."""
        logger.info("Initializing arm to starting position...")
        self.manager.arm_init() #

    def rest(self):
        """Moves arm out of vision range to allow clear board capture."""
        logger.info("Moving arm to rest position for camera capture...")
        self.manager.arm_rest() #

    def execute_uci_move(self, uci, side="white"):
        """
        Processes a full UCI move (e.g., 'e2e4' or 'e2e4q').
        Handles piece removal if it's a capture move.
        """
        start_sq = uci[:2]
        end_sq = uci[2:4]

        # 1. Coordinate lookup using BoardConfig
        start_coords = self.board.get_slot_coords(side, start_sq)
        end_coords = self.board.get_slot_coords(side, end_sq)

        logger.info(f"Executing UCI Move: {uci} | Start: {start_coords} -> End: {end_coords}")

        # 2. Basic Pick and Place Flow
        # Move to start, pick up piece
        self.manager.goto_coordinate(start_coords[0], start_coords[1], self.Z_SAFE)
        self.manager.grip() # Uses internal z=2/z=5 logic

        # Move to end, release piece
        self.manager.goto_coordinate(end_coords[0], end_coords[1], self.Z_SAFE)
        self.manager.loose() # Uses internal z=2/z=5 logic

        # 3. Return to rest to clear vision range
        self.rest()

    def handle_capture(self, target_sq, side="white"):
        """
        Logic for removing a captured piece from the board before moving
        the robot's own piece to that square.
        """
        logger.info(f"Capture detected on {target_sq}. Removing piece...")

        # Get target piece location
        target_coords = self.board.get_slot_coords(side, target_sq)
        # Get next available slot in the physical captured piece area
        bin_coords = self.board.get_next_capture_slot()

        # Pick from board
        self.manager.goto_coordinate(target_coords[0], target_coords[1], self.Z_SAFE)
        self.manager.grip()

        # Drop in capture bin
        self.manager.goto_coordinate(bin_coords[0], bin_coords[1], self.Z_SAFE)
        self.manager.loose()

def execute_command(self, uci, status, side="white"):
        """
        The unified entry point for the Main program.
        :param uci: uci string (e.g., 'e2e4')
        :param status: 'Move', 'Capt', 'Same', 'Multi', etc.
        :param side: "white" or "black" perspective
        """
        if status == 'Same' or uci is None:
            logger.info("No move required.")
            return "Same"

        if status == 'Multi':
            logger.warning("Ambiguous move (Multi). Arm stands by for safety.")
            return "Multi"

        # 1. Handle Capture first if necessary
        if status == 'Capt':
            # In a capture like 'e2d3', the piece to remove is at 'd3'
            target_sq = uci[2:4]
            logger.info(f"Status is CAPT. Removing piece at {target_sq} first.")
            self.handle_capture(target_sq, side=side)

        # 2. Execute the actual move
        # This moves the piece from start_sq to end_sq
        logger.info(f"Status is {status}. Executing move: {uci}")
        self.execute_uci_move(uci, side=side)

        # 3. Always return to rest so the camera has a clear view for next turn
        self.rest()

        return "Success"
