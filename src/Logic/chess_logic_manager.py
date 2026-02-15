import chess
from Logic.chess_engine import ZoraChessEngine

class ChessLogicManager:
    def __init__(self, robot_color=chess.BLACK):
        """
        :param robot_color: chess.WHITE or chess.BLACK, indicating which side the robot is playing.
        """
        self.board = chess.Board()
        self.engine = ZoraChessEngine()
        self.robot_color = robot_color

    def start_engine(self):
        self.engine.start()

    def update_human_move(self, uci_str):
        """
        :param uci_str: A move in UCI format (e.g., 'e2e4') representing the human's move.
        :return: (is_legal, move_info)
        """
        try:
            move = chess.Move.from_uci(uci_str)
            if move in self.board.legal_moves:
                is_capture = self.board.is_capture(move)
                self.board.push(move)

                info = {
                    "move_type": "capture" if is_capture else "move",
                    "is_check": self.board.is_check(),
                    "is_game_over": self.board.is_game_over(),
                    "result": self.board.result() if self.board.is_game_over() else None
                }
                return True, info
            else:
                return False, "Illegal Move"
        except Exception as e:
            return False, str(e)

    def get_robot_move(self):
        """
        Get the best move for the robot.
        :return: (best_move_uci, move_info)
        """
        current_fen = self.board.fen()
        best_move_uci = self.engine.get_best_move(current_fen)
        move = chess.Move.from_uci(best_move_uci)

        is_capture = self.board.is_capture(move)

        self.board.push(move)

        info = {
            "move_type": "capture" if is_capture else "move",
            "is_check": self.board.is_check(),
            "is_game_over": self.board.is_game_over(),
            "result": self.board.result() if self.board.is_game_over() else None
        }
        return best_move_uci, info

    def get_board_matrix(self):
        """
        Return the current board state as an 8x8 matrix of piece symbols.
        Empty squares are represented by '.'.
        """
        matrix = []
        for rank in range(7, -1, -1):
            row = []
            for file in range(8):
                square = chess.square(file, rank)
                piece = self.board.piece_at(square)
                # Use piece.symbol() for pieces and '.' for empty squares
                row.append(piece.symbol() if piece else ".")
            matrix.append(row)
        return matrix

    def get_current_fen(self):
        return self.board.fen()

    def reset_game(self, robot_color=chess.BLACK):
        self.board.reset()
        self.robot_color = robot_color

    def stop(self):
        self.engine.quit()


