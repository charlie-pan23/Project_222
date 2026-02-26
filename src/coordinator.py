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
    def __init__(self, pca_channels, enable_vision=True, enable_arm=True):
        self.enable_vision = enable_vision
        self.enable_arm = enable_arm

        # --- 1. VISION MODULE INITIALIZATION ---
        if self.enable_vision:
            self.vision = VisionSystem()
            logger.info("Vision System initialized.")
        else:
            self.vision = None
            logger.warning("Vision System is DISABLED.")

        # --- 2. LOGIC MODULE INITIALIZATION ---
        # Logic is always required for game rules and state
        self.logic = ChessLogicManager(robot_color=chess.BLACK)
        self.logic.start_engine()

        # --- 3. SERVO CONTROL MODULE INITIALIZATION ---
        if self.enable_arm and pca_channels is not None:
            self.arm_action = ArmAction(pca_channels=pca_channels)
            self.arm_action.initialize()
            logger.info("Arm Module initialized.")
        else:
            self.arm_action = None
            logger.warning("Arm Module is DISABLED.")

        # State variables
        self.base_frame = None
        self.current_m_state = "IDLE"
        self.move_history = []

    def check_ready_to_start(self):
        """Phase 1: Monitor board setup. Auto-ready if vision is disabled."""
        if not self.enable_vision:
            return True

        frame = self.vision.capture_frame()
        if frame is not None and self.vision.check_initial_setup(frame):
            self.base_frame = frame
            return True
        return False

    def handle_manual_move(self, uci_str):
        """
        Processes a manual move string from the UI.
        The logic manager automatically detects if it's a move or a capture.
        """
        self.current_m_state = "THINKING"

        # --- LOGIC CALL: Validate Human Move ---
        is_legal, info = self.logic.update_human_move(uci_str)

        if is_legal:
            self.move_history.append(f"User: {uci_str}")
            logger.info(f"Manual move validated: {uci_str} ({info['move_type']})")
            return True, uci_str
        else:
            logger.error(f"Invalid manual move: {uci_str}")
            self.current_m_state = "WAITING"
            return False, "Illegal Move"

    def handle_user_move_event(self):
        """Phase 2: Vision-based move detection."""
        if not self.enable_vision:
            return False, "Vision Disabled"

        self.current_m_state = "THINKING"
        time.sleep(0.5)
        frame_after_user = self.vision.capture_frame()

        user_uci = self.vision.get_move_uci(self.base_frame, frame_after_user)

        if not user_uci:
            logger.warning("No move detected via vision.")
            self.current_m_state = "WAITING"
            return False, "No Move"

        is_legal, info = self.logic.update_human_move(user_uci)

        if is_legal:
            self.move_history.append(f"User: {user_uci}")
            logger.info(f"Vision move validated: {user_uci} ({info['move_type']})")
            return True, user_uci
        else:
            logger.error(f"Illegal move attempted: {user_uci}")
            self.current_m_state = "WAITING"
            return False, "Illegal Move"

    def detect_robot_color(self):
        """Detects robot color. Defaults to black if vision is disabled."""
        if not self.enable_vision:
            return "black"

        frame = self.vision.capture_frame()
        if frame is None: return "black"

        matrix = self.vision.detector.detect_board(frame)
        view = self.vision.detector.get_matrix_view(matrix)

        white_count, black_count = 0, 0
        for r in [0, 1]:
            for cell in view[r]:
                if cell.isupper(): white_count += 1
                elif cell.islower(): black_count += 1

        robot_color = "white" if white_count > black_count else "black"

        # self.logic.set_robot_color(robot_color)
        self.logic.robot_color = (robot_color == "white")
        if self.enable_arm:
            self.arm_action.board.set_perspective(robot_color)

        return robot_color

    def execute_robot_response(self):
        """Phase 3: AI calculation and optional physical execution."""
        self.current_m_state = "THINKING"

        # --- LOGIC CALL: Get best move ---
        robot_uci, info = self.logic.get_robot_move()
        self.move_history.append(f"AI: {robot_uci}")

        # --- SERVO CALL: Physical Execution (If Enabled) ---
        if self.enable_arm and self.arm_action:
            self.current_m_state = "MOVING"

            # Handle capture if the logic says so
            if info.get("move_type") == "capture":
                # The square being captured is the destination of the UCI move
                target_sq = robot_uci[2:4]
                logger.info(f"AI Capture on {target_sq}. Moving arm to clear...")
                self.arm_action.handle_capture(target_sq, side="black")

            # Move the piece
            self.arm_action.execute_uci_move(robot_uci, side="black")
        else:
            logger.info(f"[SOFTWARE MODE] Robot move {robot_uci} applied to logic only.")

        # Update vision base frame if enabled
        if self.enable_vision:
            time.sleep(1.0)
            self.base_frame = self.vision.capture_frame()

        self.current_m_state = "WAITING"
        return robot_uci, info

    def get_ui_data(self):
        """Aggregates data. Ensure logic manager is tracking captures."""
        return {
            "fen": self.logic.get_current_fen(),
            "m_state": self.current_m_state,
            "c_state": "CHECK" if self.logic.board.is_check() else "NORMAL",
            "steps": self.move_history,
            # Ensure these are lists of piece characters (e.g., ['p', 'n'])
            "white_taken": getattr(self.logic, 'taken_by_white', []),
            "black_taken": getattr(self.logic, 'taken_by_black', [])
        }

    def get_missing_initial_pieces(self):
        """Check for missing pieces. Returns empty if vision is disabled."""
        # <--- NEW: Guard clause
        if not self.enable_vision:
            return []

        frame = self.vision.capture_frame()
        if frame is None: return []

        matrix = self.vision.detector.detect_board(frame)
        view = self.vision.detector.get_matrix_view(matrix)

        missing_squares = []
        rows_to_check = [0, 1, 6, 7]
        cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

        for r in rows_to_check:
            rank_num = 8 - r
            for c_idx, cell in enumerate(view[r]):
                if cell == ".":
                    square_name = f"{cols[c_idx]}{rank_num}"
                    missing_squares.append(square_name.upper())
        return missing_squares

    def close_all(self):
        """Clean up resources on shutdown with safety checks."""
        # <--- MODIFIED: Added safety checks for optional modules
        if self.enable_vision and hasattr(self, 'vision') and self.vision:
            logger.info("Closing Vision module...")
            self.vision.close()

        if hasattr(self, 'logic') and self.logic:
            logger.info("Stopping Chess Engine...")
            self.logic.stop()

        if self.enable_arm and hasattr(self, 'arm_action') and self.arm_action:
            logger.info("Releasing Servo torque...")
            self.arm_action.manager.release_all()
