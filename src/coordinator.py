import time
import chess
from Vision.Detector import VisionSystem
from Logic.chess_logic_manager import ChessLogicManager
from ServoControl.ArmActions import ArmAction
from Utils.Logger import get_logger

logger = get_logger(__name__)

class GameCoordinator:
    """
    The central controller managing game states, vision-logic-servo synchronization,
    and multi-point image verification.
    """
    def __init__(self, pca_channels):
        # --- VISION MODULE INITIALIZATION ---
        # Initialize Picamera2 and board detection
        self.vision = VisionSystem()

        # --- LOGIC MODULE INITIALIZATION ---
        # Initialize Stockfish engine and internal board state
        self.logic = ChessLogicManager(robot_color=chess.BLACK)
        self.logic.start_engine()

        # --- SERVO CONTROL MODULE INITIALIZATION ---
        # Initialize robotic arm action layer
        self.arm_action = ArmAction(pca_channels=pca_channels)
        self.arm_action.initialize()

        # State variables
        self.base_frame = None  # Reference for differencing
        self.current_m_state = "IDLE"
        self.move_history = []

    def check_ready_to_start(self):
        """
        Phase 1: Monitor board until ranks 1,2 and 7,8 are filled.
        """
        frame = self.vision.capture_frame() #
        if frame is not None and self.vision.check_initial_setup(frame): #
            self.base_frame = frame  # Set the first base frame for the game
            return True
        return False

    def handle_user_move_event(self):
        """
        Phase 2: Triggered when user presses 'Enter'.
        Captures move and verifies logic.
        """
        self.current_m_state = "THINKING"

        # Capture Point A: Post-user move
        time.sleep(0.5) # Image stabilization
        frame_after_user = self.vision.capture_frame()

        # --- VISION CALL: Get UCI Move ---
        user_uci = self.vision.get_move_uci(self.base_frame, frame_after_user) #

        if not user_uci:
            logger.warning("No move detected via vision.")
            self.current_m_state = "WAITING"
            return False, "No Move"

        # --- LOGIC CALL: Validate Human Move ---
        is_legal, info = self.logic.update_human_move(user_uci) #

        if is_legal:
            self.move_history.append(f"User: {user_uci}")
            logger.info(f"Human move validated: {user_uci}")

            # --- VISION CALL: Verification Point B (Pre-Robot Move) ---
            # Ensure no illegal secondary movement occurred
            safety_frame = self.vision.capture_frame()
            # In a strict setup, you could compare frame_after_user and safety_frame here

            return True, user_uci
        else:
            logger.error(f"Illegal move attempted: {user_uci}")
            self.current_m_state = "WAITING"
            return False, "Illegal Move"

    def execute_robot_response(self):
        """
        Phase 3: Logic calculates best move and ServoControl executes it.
        """
        self.current_m_state = "MOVING"

        # --- LOGIC CALL: Get Stockfish Move ---
        robot_uci, info = self.logic.get_robot_move() #
        self.move_history.append(f"AI: {robot_uci}")

        # --- SERVO CALL: Physical Execution ---
        # 1. Handle capture if necessary
        if info.get("is_capture"):
            target_sq = info.get("target_square")
            logger.info(f"AI Capture detected on {target_sq}. Clearing board...")
            self.arm_action.handle_capture(target_sq) #

        # 2. Move the piece
        self.arm_action.execute_uci_move(robot_uci) # Includes rest() to clear view

        # Capture Point C: Post-Robot move reference update
        time.sleep(1.0) # Wait for arm to be fully clear
        self.base_frame = self.vision.capture_frame() #

        self.current_m_state = "WAITING"
        return robot_uci, info

    def get_ui_data(self):
        """
        Aggregates data for the Dashboard without the UI calling sub-modules directly.
        """
        return {
            "fen": self.logic.get_current_fen(), #
            "m_state": self.current_m_state,
            "c_state": "CHECK" if self.logic.board.is_check() else "NORMAL",
            "steps": self.move_history,
            "white_taken": self.logic.taken_by_white, #
            "black_taken": self.logic.taken_by_black  #
        }

    def get_missing_initial_pieces(self):
        """
        Analyzes the board and returns a list of squares in ranks 1, 2, 7, 8
        that are expected to have pieces but are detected as empty.
        """
        frame = self.vision.capture_frame()
        if frame is None:
            return []

        # Get the 8x8 occupancy matrix
        matrix = self.vision.detector.detect_board(frame)
        view = self.vision.detector.get_matrix_view(matrix)

        missing_squares = []
        # Ranks to check: 1, 2 (bottom/White) and 7, 8 (top/Black)
        # In matrix view: index 0, 1 (Ranks 8, 7) and 6, 7 (Ranks 2, 1)
        rows_to_check = [0, 1, 6, 7]
        cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

        for r in rows_to_check:
            rank_num = 8 - r
            for c_idx, cell in enumerate(view[r]):
                if cell == ".": # If detected as empty
                    square_name = f"{cols[c_idx]}{rank_num}"
                    missing_squares.append(square_name.upper())

        return missing_squares

    def close_all(self):
        """Clean up resources on shutdown."""
        self.vision.close()
        self.logic.stop()
        self.arm_action.manager.release_all()
