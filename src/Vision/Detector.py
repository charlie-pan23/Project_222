import os
import json
import time
import numpy as np
from picamera2 import Picamera2
from Vision.PieceDetect import ChessBoardDetector
from Utils.Logger import get_logger
logger = get_logger(__name__)

class VisionSystem:
    def __init__(self, model_path="chess_8sets_model.pkl", config_path="chessboardcfg.csv", history_file="cache/board_history.json"):
        """
        Initializes the VisionSystem.
        Args:
            model_path: Path to the trained SVM model.
            config_path: Path to the chessboard coordinate config.
            history_file: Path to the JSON file where board states are stored.
        """
        logger.info("Initializing VisionSystem...")

        history_dir = os.path.dirname(self.history_file)
        if history_dir and not os.path.exists(history_dir):
            try:
                os.makedirs(history_dir)
                logger.info(f"Created cache directory: {history_dir}")
            except OSError as e:
                logger.error(f"Failed to create cache directory: {e}")
                # Fallback to current directory if cache creation fails
                self.history_file = "board_history.json"

        # Initialize Vision Engine
        try:
            self.detector = ChessBoardDetector(model_path=model_path, config_path=config_path)
            logger.info("Vision Engine loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ChessBoardDetector: {e}")
            raise e

        # Initialize Picamera2
        try:
            self.picam2 = Picamera2()
            # Configure camera for high resolution capture (matches PieceDetect requirements)
            config = self.picam2.create_configuration(
                main={"size": (1280, 960), "format": "XRGB8888"}
            )
            self.picam2.configure(config)
            self.picam2.start()
            logger.info("Picamera2 started successfully.")

            # Warm up
            self.warm_up_camera()

        except Exception as e:
            logger.error(f"Failed to initialize Picamera2: {e}")
            raise RuntimeError("Camera start failed")

        # Coordinate Mapping: Matrix Index -> Chess Notation
        # Rows: 0=H (Top), 7=A (Bottom) | Cols: 0=8 (Left), 7=1 (Right)
        self.rows_map = {0: 'H', 1: 'G', 2: 'F', 3: 'E', 4: 'D', 5: 'C', 6: 'B', 7: 'A'}
        self.cols_map = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}

    def warm_up_camera(self):
        """Captures a few dummy frames to stabilize AWB and exposure."""
        logger.info("Warming up camera sensor...")
        for _ in range(3):
            self.picam2.capture_array()
            time.sleep(0.1)

    def get_coords_from_index(self, r, c):
        """Converts matrix indices (row, col) to Board Label (e.g., 'a1')."""
        # Note: UCI standard usually uses lowercase (e.g., e2e4)
        if r in self.rows_map and c in self.cols_map:
            return f"{self.rows_map[r].lower()}{self.cols_map[c]}"
        return "??"

    def save_board_state(self, stage_name, board_matrix):
        """
        Saves the current board matrix to a local JSON file keyed by stage_name.
        """
        data = {}

        # Load existing data if file exists
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("History file corrupted, starting fresh.")
                data = {}

        # Update data
        data[stage_name] = board_matrix

        # Write back
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=4)

        logger.info(f"Saved board state for stage: '{stage_name}'")

    def load_board_state(self, stage_name):
        """Loads a board matrix from the local JSON file."""
        if not os.path.exists(self.history_file):
            return None

        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return data.get(stage_name)
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return None

    def analyze_diff(self, current_board, reference_board):
        """
        Compares two 8x8 matrices and determines the chess move.
        Returns: (uci_move, status_code)
        """
        if reference_board is None:
            logger.error("Reference board is None.")
            return None, 'Error'

        changes = []
        # Iterate to find all differences
        for r in range(8):
            for c in range(8):
                curr_val = current_board[r][c]
                ref_val = reference_board[r][c]

                if curr_val != ref_val:
                    pos = self.get_coords_from_index(r, c)
                    changes.append({
                        'pos': pos,
                        'old': ref_val,
                        'new': curr_val
                    })

        # Logic Analysis
        change_count = len(changes)

        # Case 1: No changes
        if change_count == 0:
            return None, 'Same'

        # Case 2: Too many changes (Multi-piece move or noise)
        if change_count > 2:
            logger.warning(f"Too many changes detected ({change_count}). Returning Multi.")
            return None, 'Multi'

        # Case 3: Exact move analysis (Count == 2 usually, maybe 1 if pure add/remove error)
        # A standard move involves 2 squares:
        #   1. Source square becomes Empty (Piece -> '.')
        #   2. Dest square becomes Occupied ('.' -> Piece) OR (Piece A -> Piece B [Capture])

        source = None
        target = None

        for ch in changes:
            # Check for Source: Was not empty, Now is empty
            if ch['old'] != '.' and ch['new'] == '.':
                source = ch
            # Check for Target: Now is not empty
            elif ch['new'] != '.':
                target = ch

        # Validate Move
        if source and target:
            uci_move = f"{source['pos']}{target['pos']}"

            # Check Status
            if target['old'] == '.':
                return uci_move, 'Move' # Normal move into empty space
            else:
                return uci_move, 'Capt' # Capture (target was not empty)

        # Case 4: Ambiguous changes (e.g., 2 pieces disappeared, or 2 appeared)
        logger.warning(f"Ambiguous changes: {changes}")
        return None, 'Multi'

    def process_stage(self, current_stage_name, reference_stage_name):
        """
        Main API method for the external scheduler.
        1. Captures current board (3-shot fusion).
        2. Saves to history.
        3. Loads reference board.
        4. Compares and returns result.

        Returns:
            tuple: (uci_string, status_code)
            - uci_string: e.g., 'e2e4' or None
            - status_code: 'Move', 'Capt', 'Same', 'Multi', 'Error'
        """
        logger.info(f"Processing Stage: Current='{current_stage_name}', Ref='{reference_stage_name}'")

        # 1. Capture Current State
        # Pass self.picam2 directly to PieceDetect logic
        current_board = self.detector.detect_pieces(self.picam2)

        # 2. Save Current State
        self.save_board_state(current_stage_name, current_board)

        # 3. Load Reference State
        reference_board = self.load_board_state(reference_stage_name)

        if reference_board is None:
            logger.warning(f"Reference stage '{reference_stage_name}' not found. First run?")
            # If no reference, we can't calculate a move, but we successfully saved current state.
            return None, 'Error'

        # 4. Analyze Differences
        uci, status = self.analyze_diff(current_board, reference_board)

        logger.info(f"Result: UCI={uci}, Status={status}")
        return uci, status

    def close(self):
        """Releases camera resources."""
        if hasattr(self, 'picam2'):
            logger.info("Stopping Picamera2...")
            self.picam2.stop()
            self.picam2.close()

