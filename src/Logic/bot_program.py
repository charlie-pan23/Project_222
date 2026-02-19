# Abandoned
import chess
from chess_engine import ZoraChessEngine
import time
# UPDATED: Importing Teammate B's file "MovePiece.py"
import MovePiece # Abandoned


# --- Helper Function: State Consistency Check ---
def is_valid_transition(prev_fen, current_fen, is_robot_turn):
    """
    Validates if the transition from the previous board state to the current
    board state is legal according to chess rules.

    :param prev_fen: The FEN string of the board before the move.
    :param current_fen: The FEN string of the board after the move (from camera).
    :param is_robot_turn: Boolean. True if it was the Robot's turn to move.
    :return: (Boolean is_valid, String reason)
    """
    # 1. First turn or reset state is always valid
    if not prev_fen or prev_fen == chess.STARTING_FEN:
        return True, "Start"

    try:
        prev_board = chess.Board(prev_fen)
        curr_board = chess.Board(current_fen)
    except ValueError:
        return False, "FEN_Error"

    # 2. Check if the board hasn't changed at all
    # (User pressed Enter without making a move)
    if prev_board.fen().split(' ')[0] == curr_board.fen().split(' ')[0]:
        return False, "No_Move"

    # 3. Validation Logic
    # We generate all legal moves from the previous state and see if
    # any of them result in the current state.
    for move in prev_board.legal_moves:
        prev_board.push(move)
        # Compare only piece placement (ignoring move counters)
        if prev_board.fen().split(' ')[0] == curr_board.fen().split(' ')[0]:
            return True, "Legal"
        prev_board.pop()  # Undo and try next move

    # 4. If no legal move matches the new state
    return False, "Illegal_State"


def main():
    print("[System] Initializing Chess Robot Brain...")

    # 1. Instantiate the engine
    brain = ZoraChessEngine()

    try:
        brain.start()

        # ==========================================
        # PHASE 1: SIDE SELECTION (Integration with User A)
        # ==========================================
        print("[System] Checking board orientation with Vision Module...")

        # --- TODO: Replace with actual call to User A's code ---
        # Example: is_white = vision_module.is_robot_white()
        # For simulation, we assume Robot is BLACK (False)
        vision_says_im_white = False
        # -------------------------------------------------------

        if vision_says_im_white:
            my_color = chess.WHITE
            print("[Vision] Orientation confirmed: Robot plays WHITE.")
        else:
            my_color = chess.BLACK
            print("[Vision] Orientation confirmed: Robot plays BLACK.")

        # Initialize memory of the board state
        last_known_fen = chess.STARTING_FEN

        # ==========================================
        # PHASE 2: MAIN GAME LOOP
        # ==========================================
        while True:
            print("\n" + "-" * 50)

            # 2. Input Block (Integration with User A)
            print("[State] Waiting for human opponent...")
            input_fen = input(">> Press Enter to capture board FEN (or type manually): ").strip()

            # Use default start if empty (for testing convenience)
            if not input_fen:
                if last_known_fen == chess.STARTING_FEN:
                    input_fen = chess.STARTING_FEN
                else:
                    input_fen = last_known_fen

            print(f"[Data] Received FEN: {input_fen}")

            # 3. Validate the Human's Move (Anti-Cheating)
            try:
                board = chess.Board(input_fen)
            except ValueError:
                print("[Error] Invalid FEN format received from Vision. Retrying...")
                continue

            # Only check for cheating if it's the Robot's turn to move (meaning Human just moved)
            if board.turn == my_color:
                is_legal, reason = is_valid_transition(last_known_fen, input_fen, is_robot_turn=False)

                if not is_legal:
                    if reason == "No_Move":
                        print("[Warning] No move detected. Please make a move before pressing Enter.")
                        continue
                    elif reason == "Illegal_State":
                        print("[Error] Illegal board state detected! Rules violation or piece displacement.")
                        print("[Action] Please restore the board to the previous valid state.")
                        continue
                    elif reason == "FEN_Error":
                        print("[Error] Vision data corrupted.")
                        continue

                # If valid, update our memory
                last_known_fen = input_fen
                print("[System] Board state validated successfully.")

            # 4. Check Game Over
            if board.is_game_over():
                print("[Game] Game Over condition reached.")
                print(f"[Result] {board.result()}")
                break

            # 5. Turn Logic
            if board.turn == my_color:
                turn_str = "White" if my_color == chess.WHITE else "Black"
                print(f"[Game] Robot Turn ({turn_str}). Calculating best move...")

                # --- CORE LOGIC: Get move from Stockfish ---
                best_move_uci = brain.get_best_move(input_fen, time_limit=1.0)

                print(f"[Decision] Best Move: {best_move_uci}")
                print(f"[Output] Sending command to Arm Controller: {best_move_uci}")

                # --- Integration with User B (Arm) ---
                # 1. Send the Move Command (Using file: MovePiece.py)
                # Note: Assuming the function inside is still called move_piece()
                MovePiece.move_piece(best_move_uci)

                # ==========================================
                # PHASE 3: BLOCKING / SAFETY (Integration with User B)
                # ==========================================
                print("[System] Waiting for Arm execution...")

                # --- REAL LOGIC: Busy Waiting ---
                # Requirement: get_status() returns False when Moving.
                # So we wait WHILE status IS False.

                while MovePiece.get_status() == False:
                    # Check every 0.1 seconds to prevent CPU overload
                    time.sleep(0.1)

                print("[System] Arm signal: Movement Complete (Status is True).")

                # CRITICAL STEP:
                # We must update last_known_fen to reflect the move the ROBOT just made.
                board.push_uci(best_move_uci)
                last_known_fen = board.fen()
                print(f"[System] Internal state updated. Expecting: {last_known_fen}")
                # ==========================================

            else:
                opponent_str = "Black" if my_color == chess.WHITE else "White"
                print(f"[Game] Opponent's Turn ({opponent_str}). Waiting...")
                # Loop back and wait for new camera input

    except KeyboardInterrupt:
        print("\n[System] Program stopped by user.")
    except Exception as e:
        print(f"\n[Critical Error] {e}")
    finally:
        brain.quit()
        print("[System] Brain Offline.")


if __name__ == "__main__":
    main()
