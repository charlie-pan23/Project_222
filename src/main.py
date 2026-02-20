import time
import sys
import threading
import sys
import select
user_trigger_detected = False

# --- UI and RENDERING ---
import keyboard  # Requires sudo on Raspberry Pi
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
import board
import busio
from adafruit_pca9685 import PCA9685

#--- Logging ---
from Utils.Logger import get_logger
logger = get_logger(__name__)

ssh_enter_pressed = False

def ssh_input_listener():
    """Background thread to catch Enter key from SSH terminal."""
    global user_trigger_detected
    while True:
        if select.select([sys.stdin], [], [], 0.1)[0]:
            line = sys.stdin.readline()
            if line:
                user_trigger_detected = True



def main():
    console = Console(width=180, height=50)

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
    cal_ui = CalibrationUI()

    # --- STAGE 1: STARTUP ANIMATION ---
    startup_ui.render("Loading System Core...")
    time.sleep(2)

    # --- STAGE 2: CALIBRATION DIALOG ---
    console.clear()
    console.print(UIOverlays.calibration_request())

    do_calibration = False
    choice = console.input("\n[bold white]Perform calibration? (y/n): [/]").lower().strip()
    do_calibration = (choice == 'y')

    # --- STAGE 3: EXECUTE CALIBRATION (IF REQUESTED) ---
    if do_calibration:
        # A. Physical Arm Calibration
        arm_cal = ArmCalibrator(coord.arm_action)
        while True:
            point, success = arm_cal.move_to_next()
            startup_ui.render(f"ARM CALIBRATION: At {point}. Press SPACE for next, ENTER to finish.")

            # Using SSH-compatible readchar as discussed
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
            frame = vis_cal.run_calibration_frame()
            startup_ui.render(f"VISION CALIBRATION: {vis_cal.current_set_name}. Press SPACE to toggle, ENTER to finish.")

            key = readchar.readkey()
            if key == readchar.key.SPACE:
                vis_cal.toggle_set()
            elif key == readchar.key.ENTER:
                break
        vis_cal.close_window()
        logger.info("Vision calibration UI closed, returning to terminal.")
    coord.arm_action.manager.arm_rest()

    # --- STAGE 4: INITIAL BOARD SETUP DETECTION ---
    # while True:
    #     missing = coord.get_missing_initial_pieces()

    #     if not missing:
    #         startup_ui.render("All pieces detected! Starting game...")
    #         time.sleep(1)
    #         break

    #     # Format the missing squares into a readable string
    #     # Display up to 8 squares to avoid cluttering the UI
    #     missing_str = ", ".join(missing[:8]) + ("..." if len(missing) > 8 else "")

    #     message = (
    #         f"Waiting for board setup...\n"
    #         f"[bold red]Missing pieces at: {missing_str}[/]\n"
    #         f"Please fill Ranks 1, 2, 7, & 8."
    #     )

    #     startup_ui.render(message)
    #     time.sleep(0.8) # Refresh rate for vision check
    # # while not coord.check_ready_to_start():
    # #     startup_ui.render("Waiting for board setup (Ranks 1,2,7,8)...")
    # #     time.sleep(0.5)

    # --- STAGE 4: INITIAL BOARD SETUP DETECTION ---
    # Reset the global flag to ensure a fresh listener state for this stage
    global ssh_enter_pressed

    logger.info("Entering Stage 4: Board Setup Verification.")

    while True:
        # 1. Retrieve the list of squares missing pieces in Ranks 1, 2, 7, and 8
        # This calls the internal vision system to analyze the board occupancy
        missing = coord.get_missing_initial_pieces()

        # 2. Case A: Automatic Success
        # If the list is empty, all required 32 pieces are in their starting positions.
        if not missing:
            startup_ui.render("All pieces detected! Starting game engine...")
            time.sleep(1.5)
            break

        # 3. Case B: Manual Force Initialization (via SSH Enter)
        # Allows the user to skip visual detection if lighting or minor errors persist.
        if ssh_enter_pressed:
            logger.warning("Manual force initialization triggered by user via SSH.")
            startup_ui.render("Force Initializing... Synchronizing logical board state.")

            # Synchronize the internal chess engine to the standard starting FEN
            coord.logic.reset_board()

            # Clear flag for use in Stage 5 main loop
            ssh_enter_pressed = False
            time.sleep(1.5)
            break

        # 4. Construct Feedback Message for TUI
        # We display up to 8 missing squares to keep the UI clean.
        missing_str = ", ".join(missing[:8]) + ("..." if len(missing) > 8 else "")

        message = (
            "[bold cyan]INITIALIZING BOARD...[/]\n\n"
            "Please place pieces on Ranks 1, 2, 7, & 8.\n"
            f"[bold red]Missing pieces at: {missing_str}[/]\n\n"
            "--------------------------------------------------\n"
            "[bold white]Press ENTER to force start (Skip visual check)[/]"
        )

        # Render the updated status to the terminal
        startup_ui.render(message)

        # Scanning frequency: 2Hz to reduce CPU load while maintaining responsiveness
        time.sleep(0.5)

    # --- STAGE 5: MAIN GAME LOOP (DASHBOARD) ---
    input_thread = threading.Thread(target=ssh_input_listener, daemon=True)
    input_thread.start()
    with Live(dashboard.layout, refresh_per_second=4, screen=True) as live:
        while True:
            # 1. Fetch current game and hardware data from Coordinator
            ui_data = coord.get_ui_data()

            # 2. Update Dashboard UI Components
            # Update the FEN-based chessboard
            dashboard.layout["board_zone"].update(dashboard.make_board(ui_data["fen"]))

            # Update Raspberry Pi 4B hardware stats
            dashboard.layout["hardware"].update(dashboard.make_system_status())

            # Update Robot status (WAITING / THINKING / MOVING)
            dashboard.layout["machine_state"].update(
                dashboard.make_state_box("STATUS", ui_data["m_state"],
                                    "yellow" if ui_data["m_state"] == "WAITING" else "magenta")
            )

            # Update Chess State (NORMAL / CHECK / MATE)
            dashboard.layout["check_state"].update(
                dashboard.make_state_box("STATE", ui_data["c_state"],
                                    "white" if ui_data["c_state"] == "NORMAL" else "red")
            )

            # Update Captured Pieces Panel
            dashboard.layout["captured_zone"].update(
                dashboard.make_taken_panel(ui_data["white_taken"], ui_data["black_taken"])
            )

            # 3. Handle User Input via the SSH Flag
            if ssh_enter_pressed:
                # Update UI immediately to show the system is processing
                dashboard.layout["machine_state"].update(
                    dashboard.make_state_box("STATUS", "THINKING", "blue")
                )

                # Step A: Process Human Move via Vision
                is_valid, move_msg = coord.handle_user_move_event()

                if is_valid:
                    # Step B: Calculate and Execute Robot Counter-move
                    coord.execute_robot_response()
                else:
                    # Log error or invalid move to the TUI logger
                    logger.warning(f"Invalid Move Attempted: {move_msg}")

                # Reset the flag to wait for the next input
                ssh_enter_pressed = False

            # 4. Break condition (Optional: Add a specific SSH command to exit)
            # Since we are in SSH, Ctrl+C is usually handled by the OS to terminate.
            time.sleep(0.1)

    # 6. CLEANUP
    coord.close_all()
    sys.exit(0)

if __name__ == "__main__":
    main()
