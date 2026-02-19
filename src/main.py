import time
import sys
import keyboard  # Requires sudo on Raspberry Pi
from rich.live import Live
from rich.console import Console

# --- INTERNAL MODULES ---
from UI.Title import StartupUI
from UI.dashboard import ChessDashboard
from UI.Overlays import UIOverlays
from UI.CalibrationUI import CalibrationUI
from coordinator import GameCoordinator

# --- HARDWARE & CALIBRATION ---
from ServoControl.ArmCalibration import ArmCalibrator
from Vision.VisionCalibration import VisionCalibrator

def main():
    console = Console(width=180, height=50)

    # 1. INITIALIZATION
    # In a real setup, you would pass the actual PCA9685 channels here
    pca_channels = None
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
    while True:
        if keyboard.is_pressed('y'):
            do_calibration = True
            break
        if keyboard.is_pressed('n'):
            break
        time.sleep(0.1)

    # --- STAGE 3: EXECUTE CALIBRATION (IF REQUESTED) ---
    if do_calibration:
        # A. Physical Arm Calibration
        arm_cal = ArmCalibrator(coord.arm_action)
        while True:
            point, success = arm_cal.move_to_next()
            # Overlay guidance on top of Title or specialized screen
            startup_ui.render(f"ARM CALIBRATION: Move to {point}. Press SPACE to next, ENTER to finish.")

            # Wait for Space to move next or Enter to exit
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == 'enter': break
                elif event.name == 'space': continue

        # B. Vision Calibration
        vis_cal = VisionCalibrator(coord.vision)
        while True:
            # Note: This displays an OpenCV window for the camera feed
            frame = vis_cal.run_calibration_frame()
            # Update console with instructions
            startup_ui.render(f"VISION CALIBRATION: {vis_cal.current_set_name}. Press SPACE to toggle, ENTER to finish.")

            # Simulated wait for key in CV2 or Keyboard
            if keyboard.is_pressed('space'):
                vis_cal.toggle_set()
                time.sleep(0.3) # Debounce
            if keyboard.is_pressed('enter'):
                break

    # --- STAGE 4: INITIAL BOARD SETUP DETECTION ---
    while not coord.check_ready_to_start():
        startup_ui.render("Waiting for board setup (Ranks 1,2,7,8)...")
        time.sleep(0.5)

    # --- STAGE 5: MAIN GAME LOOP (DASHBOARD) ---
    with Live(dashboard.layout, refresh_per_second=4, screen=True) as live:
        while True:
            # Update dynamic data from Coordinator
            ui_data = coord.get_ui_data()

            # Render all Dashboard components
            dashboard.layout["board_zone"].update(dashboard.make_board(ui_data["fen"]))
            dashboard.layout["hardware"].update(dashboard.make_system_status())
            dashboard.layout["machine_state"].update(
                dashboard.make_state_box("STATUS", ui_data["m_state"], "yellow" if ui_data["m_state"] == "WAITING" else "magenta")
            )
            dashboard.layout["check_state"].update(
                dashboard.make_state_box("STATE", ui_data["c_state"], "white" if ui_data["c_state"] == "NORMAL" else "red")
            )
            dashboard.layout["captured_zone"].update(
                dashboard.make_taken_panel(ui_data["white_taken"], ui_data["black_taken"])
            )
            # steps update could go here

            # --- INPUT HANDLING: USER MOVE TRIGGER ---
            if keyboard.is_pressed('enter'):
                # 1. Process User Move
                is_valid, move_msg = coord.handle_user_move_event()

                if is_valid:
                    # 2. Process Robot Counter-move
                    coord.execute_robot_response()
                else:
                    # Logic for handling illegal moves/errors
                    pass

                # Debounce Enter key
                while keyboard.is_pressed('enter'): time.sleep(0.1)

            if keyboard.is_pressed('esc'):
                break

    # 6. CLEANUP
    coord.close_all()
    sys.exit(0)

if __name__ == "__main__":
    main()
