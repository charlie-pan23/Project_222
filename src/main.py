import time
import sys
import threading
import select
import board
import busio
from adafruit_pca9685 import PCA9685
from rich.live import Live
from rich.console import Console
import readchar

# --- INTERNAL MODULES ---
from UI.Title import StartupUI
from UI.dashboard import ChessDashboard
from UI.Overlays import UIOverlays
from UI.CalibrationUI import CalibrationUI
from coordinator import GameCoordinator

# --- HARDWARE & CALIBRATION ---
from ServoControl.ArmCalibration import ArmCalibrator
from Vision.VisionCalibration import VisionCalibrator

# --- Logging ---
from Utils.Logger import get_logger
logger = get_logger(__name__)

import logging
from rich.logging import RichHandler
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)] # 这里的 console 是你定义的 Console 对象
)
logger = logging.getLogger("chess")

ssh_enter_pressed = False
ssh_input_buffer = ""


def ssh_input_handler():
    """Captures full instruction strings from SSH."""
    global ssh_enter_pressed, ssh_input_buffer
    while True:
        if select.select([sys.stdin], [], [], 0.1)[0]:
            line = sys.stdin.readline().strip()
            if line:
                ssh_input_buffer = line
                ssh_enter_pressed = True

def main():
    global ssh_enter_pressed
    console = Console(width=180)

    # --- 0. Start the SSH input handler thread ---
    input_thread = threading.Thread(target=ssh_input_handler, daemon=True)
    input_thread.start()

    # 1. INITIALIZATION
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        pca = PCA9685(i2c)
        pca.frequency = 50
        pca_channels = pca.channels
    except Exception as e:
        logger.error(f"Failed to initialize PCA9685: {e}")
        return

    coord = GameCoordinator(pca_channels)
    startup_ui = StartupUI()
    dashboard = ChessDashboard()

    # --- STAGE 1: STARTUP ANIMATION ---
    startup_ui.render("Loading System Core...")
    time.sleep(2)

    # --- STAGE 2: CALIBRATION DIALOG ---
    console.clear()
    console.print(UIOverlays.calibration_request())

    choice = console.input("\n[bold white]Perform calibration? (y/n): [/]").lower().strip()
    do_calibration = (choice == 'y')

    # --- STAGE 3: EXECUTE CALIBRATION ---
    if do_calibration:
        # A. Physical Arm Calibration
        arm_cal = ArmCalibrator(coord.arm_action)
        while True:
            point, success = arm_cal.move_to_next()
            startup_ui.render(f"ARM CALIBRATION: At {point}. Press SPACE for next, ENTER to finish.")

            key = readchar.readkey()
            if key == readchar.key.ENTER:
                break
            elif key == readchar.key.SPACE:
                continue

        arm_cal.reset_position()
        startup_ui.render("Arm Resetting... Preparing Vision Calibration.")
        time.sleep(1)

        # B. Vision Calibration
        vis_cal = VisionCalibrator(coord.vision)
        while True:
            vis_cal.run_calibration_frame()
            startup_ui.render(f"VISION CALIBRATION: {vis_cal.current_set_name}. Press SPACE to toggle, ENTER to finish.")

            key = readchar.readkey()
            if key == readchar.key.SPACE:
                vis_cal.toggle_set()
            elif key == readchar.key.ENTER:
                break
        vis_cal.close_window()
        logger.info("Vision calibration UI closed.")

    coord.arm_action.manager.arm_rest()

    # --- STAGE 4: INITIAL BOARD SETUP DETECTION ---

    # Initialize timing for the auto-start feature
    global ssh_enter_pressed
    ssh_enter_pressed = False
    stage4_start_time = time.time()
    TIMEOUT_LIMIT = 5.0

    logger.info("Entering Stage 4: Board Setup Verification.")

    while True:
        missing = coord.get_missing_initial_pieces()
        elapsed_time = time.time() - stage4_start_time

        if not missing or elapsed_time >= TIMEOUT_LIMIT or ssh_enter_pressed:
            if elapsed_time >= TIMEOUT_LIMIT:
                logger.warning(f"Detection timed out. Proceeding...")
                startup_ui.render("Timeout! Force Starting...")
            else:
                startup_ui.render("Board Verified! Starting...")

            try:
                try:
                    detected_color = coord.detect_robot_color()
                except Exception:
                    logger.error("Vision detection failed. Defaulting to BLACK.")
                    detected_color = "black"

                coord.logic.reset_game(robot_color=detected_color)
                coord.arm_action.board.set_perspective(detected_color)

            except Exception as e:
                logger.error(f"Critical error during sync: {e}")


            ssh_enter_pressed = False
            time.sleep(1.0)
            print("DEBUG: Exiting Stage 4 now.")
            break
        remaining_time = max(0, TIMEOUT_LIMIT - elapsed_time)
        missing_str = ", ".join(missing[:8]) + ("..." if len(missing) > 8 else "")

        message = (
            "[bold cyan]INITIALIZING BOARD...[/]\n\n"
            f"Auto-start in: [bold yellow]{remaining_time:.1f}s[/]\n"
            f"[bold red]Missing pieces at: {missing_str}[/]\n\n"
            "--------------------------------------------------\n"
            "[bold white]Press ENTER to start now[/]"
        )
        startup_ui.render(message)
        time.sleep(0.2)


    logger.info("Stage 4 complete. Transitioning to Dashboard.")

# --- STAGE 5: MAIN GAME LOOP (Scrolling Log Mode) ---

    # screen=False allows the logs to scroll underneath the Dashboard
    with Live(dashboard.layout, refresh_per_second=4, screen=False) as live:
        logger.info("Game Dashboard Active. Real-time vision logs will appear below.")

        while True:
            # 1. Update Graphical UI Panels
            ui_data = coord.get_ui_data()
            dashboard.layout["board_zone"].update(dashboard.make_board(ui_data["fen"]))
            dashboard.layout["hardware"].update(dashboard.make_system_status())

            dashboard.layout["machine_state"].update(
                dashboard.make_state_box("STATUS", ui_data["m_state"],
                                    "yellow" if ui_data["m_state"] == "WAITING" else "magenta")
            )
            dashboard.layout["check_state"].update(
                dashboard.make_state_box("STATE", ui_data["c_state"],
                                    "white" if ui_data["c_state"] == "NORMAL" else "red")
            )
            dashboard.layout["captured_zone"].update(
                dashboard.make_taken_panel(ui_data["white_taken"], ui_data["black_taken"])
            )

            # 2. Process Input (Manual or Vision)
            if ssh_enter_pressed:
                instruction = ssh_input_buffer.lower().strip()
                ssh_enter_pressed = False

                # Case A: Manual Move (e.g., "d2d4")
                if len(instruction) == 4 and instruction[0].isalpha() and instruction[1].isdigit():
                    logger.info(f"MANUAL MOVE: {instruction}")
                    coord.logic.apply_move(instruction)
                    coord.arm_action.move_piece(instruction[:2], instruction[2:])

                # Case B: Vision Move (Pressing Enter)
                else:
                    logger.info("VISION TRIGGERED: Capturing board state...")

                    # --- Vision Distribution Logging ---
                    # Capture current frame and get raw occupancy matrix
                    frame = coord.vision.capture_frame()
                    if frame is not None:
                        raw_matrix = coord.vision.detector.detect_board(frame)
                        # Use the helper method you specified to get the 8x8 view
                        view = coord.vision.detector.get_matrix_view(raw_matrix)

                        logger.info("Current Piece Distribution (Vision):")
                        for row in view:
                            # Log each row of the 8x8 grid
                            logger.info(" ".join(row))

                    # --- Detected Move Logging ---
                    is_valid, move_msg = coord.handle_user_move_event()

                    if is_valid:
                        # move_msg typically contains the UCI string like 'e2e4'
                        logger.info(f"MOVE DETECTED: [bold green]{move_msg}[/]")
                        coord.execute_robot_response()
                    else:
                        logger.warning(f"Detection Error: {move_msg}")

                ssh_input_buffer = ""

            time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
    finally:
        sys.exit(0)
