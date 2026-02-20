import chess
import chess.engine
import os
from Utils.Logger import get_logger

logger = get_logger(__name__)


class ZoraChessEngine:
    def __init__(self, engine_path=None):
        # Default to the standard Raspberry Pi installation path
        if engine_path is None:
            self.engine_path = "/usr/games/stockfish"
        else:
            self.engine_path = engine_path

        # Optional: Add a check to ensure the file exists
        if not os.path.exists(self.engine_path):
            raise FileNotFoundError(f"Stockfish engine not found at {self.engine_path}. Run 'sudo apt install stockfish'.")


    def start(self):
        """Start the engine process."""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            self.engine.configure({"Skill Level": 8})
            logger.info(f"Engine started successfully: {self.engine.id.get('name')} with Skill Level 8.")
        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            raise e

    def get_best_move(self, fen_string, time_limit=1.0):
        """
        Core Function: Calculates the best move for a given board state.
        :param fen_string: The standard FEN string representing the board.
        :param time_limit: Thinking time limit in seconds.
        :return: The best move in UCI format (e.g., 'e2e4').
        """
        if not self.engine:
            logger.warning("Engine not started. Attempting to start automatically...")
            self.start()

        board = chess.Board(fen_string)

        # Ask Stockfish to find the best move
        result = self.engine.play(board, chess.engine.Limit(time=time_limit))

        # Return the move in UCI string format
        return result.move.uci()

    def quit(self):
        """Stop the engine and release resources."""
        if self.engine:
            self.engine.quit()
            logger.info("Engine stopped.")
