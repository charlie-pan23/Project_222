import time
import sys
import threading
import select
import board
import busio
from adafruit_pca9685 import PCA9685
from rich.live import Live
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
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
from Utils.Logger import get_logger, LOG_BUFFER
logger = get_logger(__name__)

ssh_enter_pressed = False
ssh_input_buffer = ""
coord = None


def ssh_input_handler():
    """Captures keyboard input with robust backspace support for different terminals."""
    global ssh_enter_pressed, ssh_input_buffer
    while True:
        try:
            # Captures a single key press
            key = readchar.readkey()

            # 1. Handle ENTER key to submit the command
            if key in (readchar.key.ENTER, '\r', '\n'):
                if ssh_input_buffer.strip():
                    ssh_enter_pressed = True

            # 2. Handle BACKSPACE / DELETE keys
            # \x7f is standard for Linux/Ubuntu terminals; \x08 is common in some SSH clients
            elif key in (readchar.key.BACKSPACE, '\x7f', '\x08'):
                if len(ssh_input_buffer) > 0:
                    ssh_input_buffer = ssh_input_buffer[:-1] # Remove last character

            # 3. Handle CTRL+C for clean exit
            elif key == readchar.key.CTRL_C:
                # Triggering KeyboardInterrupt to initiate cleanup block
                import os
                import signal
                os.kill(os.getpid(), signal.SIGINT)

            # 4. Handle standard printable characters
            elif len(key) == 1 and key.isprintable():
                ssh_input_buffer += key # Append to buffer

        except Exception as e:
            # Silence internal errors during input capture to avoid TUI flickering
            pass
def main():
    global ssh_enter_pressed, ssh_input_buffer, coord
    console = Console(width=180)

    # --- 1. STARTUP ANIMATION ---
    startup_ui = StartupUI()
    startup_ui.render("Initializing System Core...") #
    time.sleep(1)

    # --- 2. MODULE SELECTION MENU ---
    # This prevents competition for the terminal input (stdin).
    console.clear()
    menu_panel = Panel(Align.center(
        "[bold cyan]ROBOT CONFIGURATION[/]\n\n"
        "1. Enable Vision (Camera)? [y/n]\n"
        "2. Enable Arm (Servos)? [y/n]\n\n"
        "[dim]Disable both to run in 'Software Only' debug mode.[/]",
        vertical="middle"), title="STARTUP", border_style="bright_blue", width=80, height=12)
    console.print(menu_panel)

    v_choice = console.input("\n[bold white]Enable Vision? (y/n): [/]").lower().strip() == 'y'
    a_choice = console.input("\n[bold white]Enable Arm? (y/n): [/]").lower().strip() == 'y'

    # --- 3. START INPUT LISTENER ---
    input_thread = threading.Thread(target=ssh_input_handler, daemon=True)
    input_thread.start()

    # --- 4. CONDITIONAL HARDWARE INITIALIZATION ---
    pca_channels = None
    if a_choice:
        try:
            # Only access physical I2C pins if the arm is explicitly enabled
            i2c = busio.I2C(board.SCL, board.SDA)
            pca = PCA9685(i2c)
            pca.frequency = 50
            pca_channels = pca.channels
            logger.info("Hardware I2C and PCA9685 initialized successfully.")
        except Exception as e:
            # If initialization fails (e.g., on a VM), fallback to software mode
            logger.error(f"Hardware init failed: {e}. Falling back to No-Arm mode.")
            a_choice = False

    # Initialize the Coordinator with user preferences
    coord = GameCoordinator(pca_channels, enable_vision=v_choice, enable_arm=a_choice)
    dashboard = ChessDashboard()

    # --- 5. CALIBRATION (OPTIONAL) ---
    if v_choice or a_choice:
        console.clear()
        console.print(UIOverlays.calibration_request()) #

        if console.input("\n[bold white]Start Calibration? (y/n): [/]").lower().strip() == 'y':
            # Physical Arm Alignment
            if a_choice:
                arm_cal = ArmCalibrator(coord.arm_action)
                while True:
                    point, _ = arm_cal.move_to_next()
                    startup_ui.render(f"ARM CALIBRATION: At {point}. [SPACE] Next, [ENTER] Finish.")
                    key = readchar.readkey() #
                    if key == readchar.key.ENTER: break
                arm_cal.reset_position()

            # Visual Camera Alignment
            if v_choice:
                vis_cal = VisionCalibrator(coord.vision)
                while True:
                    vis_cal.run_calibration_frame()
                    startup_ui.render(f"VISION CALIBRATION: {vis_cal.current_set_name}. [SPACE] Toggle, [ENTER] Finish.")
                    key = readchar.readkey()
                    if key == readchar.key.SPACE: vis_cal.toggle_set()
                    elif key == readchar.key.ENTER: break
                vis_cal.close_window()

    # --- 6. GAME INITIALIZATION ---
    if v_choice:
        startup_ui.render("Verifying Board Setup...")
        # Loops until the board matches the starting chess position
        while not coord.check_ready_to_start():
            missing = coord.get_missing_initial_pieces()
            startup_ui.render(f"Waiting for pieces... Missing: {', '.join(missing[:5])}")
            time.sleep(0.5)

    # Sync perspective and robot color
    detected_color = coord.detect_robot_color()
    logger.info(f"Setup complete. Robot is playing as {detected_color.upper()}.")
    time.sleep(1)

# --- 7. MAIN GAME LOOP (TUI) ---
    # 'screen=True' creates a dedicated full-screen buffer for the Dashboard
    with Live(dashboard.layout, refresh_per_second=4, screen=True) as live:
        logger.info("Dashboard Active. System ready for move commands.")

        while True:
            # 7a. FETCH DATA FROM COORDINATOR
            # Aggregates logic state, move history, and captured pieces
            ui_data = coord.get_ui_data()

            # 7b. UPDATE GRAPHICAL PANELS
            # Update the 8x8 Chessboard visualization
            dashboard.layout["board_zone"].update(dashboard.make_board(ui_data["fen"]))

            # Update Hardware status (CPU/RAM/Temp)
            dashboard.layout["hardware"].update(dashboard.make_system_status())

            # Update Move History (Prevents the "Layout(name='steps')" metadata display)
            dashboard.layout["steps"].update(dashboard.make_steps_panel(ui_data["steps"]))

            # Update Captured Pieces Panel
            dashboard.layout["captured_zone"].update(
                dashboard.make_taken_panel(ui_data["white_taken"], ui_data["black_taken"])
            )

            # 7c. UPDATE STATE INDICATORS
            # Machine State: IDLE, THINKING, MOVING, WAITING
            m_color = "yellow" if ui_data["m_state"] == "WAITING" else "magenta"
            dashboard.layout["machine_state"].update(
                dashboard.make_state_box("STATUS", ui_data["m_state"], m_color)
            )

            # Game State: NORMAL, CHECK, CHECKMATE
            c_color = "white" if ui_data["c_state"] == "NORMAL" else "red"
            dashboard.layout["check_state"].update(
                dashboard.make_state_box("STATE", ui_data["c_state"], c_color)
            )

            # 7d. UPDATE LOGS & INPUT BUFFER
            # Pull formatted logs from the global LOG_BUFFER
            dashboard.layout["log_zone"].update(dashboard.make_log_panel())

            # Display the real-time typing buffer (e.g., as you type 'e2e4')
            dashboard.layout["input_zone"].update(dashboard.make_input_panel(ssh_input_buffer))

            # 7e. PROCESS USER INPUT EVENTS
            if ssh_enter_pressed:
                # Capture the command and immediately reset buffer to clear UI
                command = ssh_input_buffer.lower().strip()
                ssh_input_buffer = ""
                ssh_enter_pressed = False

                # CASE 1: Manual UCI Move (e.g., "d2d4")
                if len(command) >= 4 and command[0].isalpha():
                    logger.info(f"PROCESSING MANUAL MOVE: {command}")
                    is_valid, _ = coord.handle_manual_move(command)
                    if is_valid:
                        # AI thinks and Arm executes if enabled
                        coord.execute_robot_response()
                    else:
                        logger.warning(f"ILLEGAL MOVE: {command}")

                # CASE 2: Vision Trigger (Enter pressed without text)
                elif v_choice and not command:
                    logger.info("VISION TRIGGER: Scanning board state...")
                    is_valid, move_msg = coord.handle_user_move_event()
                    if is_valid:
                        logger.info(f"HUMAN MOVE DETECTED: {move_msg}")
                        coord.execute_robot_response()
                    else:
                        logger.warning(f"SCAN ERROR: {move_msg}")

                else:
                    logger.warning("INVALID COMMAND or Vision Module Disabled.")

            # 7f. CHECK END GAME
            if "MAT" in ui_data["c_state"]:
                logger.info("CHECKMATE DETECTED. Game Over.")
                time.sleep(5)
                break

            # Responsive delay to keep CPU usage low on Raspberry Pi
            time.sleep(0.05)

# --- GLOBAL ERROR HANDLING & CLEANUP ---
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        logger.info("\nShutdown signal received from keyboard.")
    except Exception as e:
        # Unhandled fatal errors
        logger.exception(f"Fatal crash: {e}")
    finally:
        # Critical: Ensure all resources are released regardless of how the app closed
        if coord is not None:
            logger.info("Initiating resource teardown...")
            coord.close_all()
        logger.info("System clean. Goodbye.")
        sys.exit(0)
