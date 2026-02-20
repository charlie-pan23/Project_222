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

ssh_enter_pressed = False

def ssh_input_handler():
    """Background thread to catch Enter key from SSH terminal."""
    global ssh_enter_pressed
    while True:
        if select.select([sys.stdin], [], [], 0.1)[0]:
            line = sys.stdin.readline()
            if line:
                ssh_enter_pressed = True
                logger.debug("SSH input signal received.")

def main():
    global ssh_enter_pressed
    console = Console(width=180, height=50)

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
    ssh_enter_pressed = False
    logger.info("Entering Stage 4: Board Setup Verification.")

    while True:
        # 1. Retrieve the list of squares missing pieces in Ranks 1, 2, 7, and 8
        # This calls the vision system to analyze the starting positions
        missing = coord.get_missing_initial_pieces()

        # Check for success triggers: either all pieces are found OR user hits Enter
        if not missing or ssh_enter_pressed:
            if ssh_enter_pressed:
                logger.warning("Manual force initialization triggered via SSH.")
                startup_ui.render("Force Initializing... Skipping visual verification.")
            else:
                startup_ui.render("All pieces detected! Finalizing setup...")
                time.sleep(1)

            # 2. AUTOMATIC COLOR & PERSPECTIVE DETECTION
            # Identify if White or Black is placed near the arm (Ranks 7 & 8)
            detected_color = coord.detect_robot_color()

            # 3. SYNCHRONIZATION
            # Reset the logical engine to the standard start FEN
            coord.logic.reset_board()

            # Update UI to notify user of the detected identity
            msg = f"SUCCESS! Robot is playing as [bold yellow]{detected_color.upper()}[/]"
            startup_ui.render(msg)

            # Reset flag for use in Stage 5
            ssh_enter_pressed = False
            time.sleep(2)
            break

        # 4. UI FEEDBACK FOR MISSING PIECES
        # Limit display to 8 squares for readability
        missing_str = ", ".join(missing[:8]) + ("..." if len(missing) > 8 else "")

        message = (
            "[bold cyan]VERIFYING BOARD SETUP...[/]\n\n"
            "Please place pieces on Ranks 1, 2, 7, & 8.\n"
            f"[bold red]Missing pieces at: {missing_str}[/]\n\n"
            "--------------------------------------------------\n"
            "[bold white]Press ENTER to force start (Detects color & skips check)[/]"
        )

        # Update the terminal display
        startup_ui.render(message)

        # Frequency: 2Hz to keep CPU usage low on Raspberry Pi 4B
        time.sleep(0.5)

    # --- STAGE 5: MAIN GAME LOOP (DASHBOARD) ---
    with Live(dashboard.layout, refresh_per_second=4, screen=True) as live:
        while True:
            ui_data = coord.get_ui_data()

            # Update Dashboard Components
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

            if ssh_enter_pressed:
                dashboard.layout["machine_state"].update(
                    dashboard.make_state_box("STATUS", "THINKING", "blue")
                )
                is_valid, move_msg = coord.handle_user_move_event()
                if is_valid:
                    coord.execute_robot_response()
                else:
                    logger.warning(f"Invalid Move: {move_msg}")

                ssh_enter_pressed = False

            time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
    finally:
        sys.exit(0)
