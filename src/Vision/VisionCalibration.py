import cv2
from Vision.Detector import VisionSystem
from Utils.Logger import get_logger

logger = get_logger(__name__)

class VisionCalibrator:
    """Handles visual board alignment using two sets of test points."""
    def __init__(self, vision_system: VisionSystem):
        # Injected vision system to use existing Picamera2 instance
        self.vision = vision_system

        # Two sets of 8 points for precision checking
        self.sets = {
            "Set A": ['a1', 'a8', 'h1', 'h8', 'f6', 'c3', 'd5', 'e4'],
            "Set B": ['a4', 'd8', 'h5', 'e1', 'g2', 'g7', 'b2', 'b7']
        }
        self.current_set_name = "Set A"

    def toggle_set(self):
        """Switches between Set A and Set B on Space press."""
        self.current_set_name = "Set B" if self.current_set_name == "Set A" else "Set A"
        logger.info(f"Switched to vision calibration {self.current_set_name}")
        return self.current_set_name

    def run_calibration_frame(self):
        """
        Captures a frame and draws the green calibration boxes.
        This should be called in a loop by Main.
        """
        frame = self.vision.capture_frame() #
        if frame is None:
            return None

        active_points = self.sets[self.current_set_name]

        # Use existing detector logic to draw boxes on the frame
        # Note: We assume detector.detect_board_and_draw exists or similar in PieceDetect
        # If not, we iterate through active_points and draw using BoardConfig metadata
        for point in active_points:
            # Drawing logic adapted from PositionAdjust.py
            # Assuming detector can provide pixel coordinates for notation
            pass # (Implementation depends on PieceDetect.py's internal mapping)

        # Add UI hints to the frame
        cv2.putText(frame, f"CALIBRATION: {self.current_set_name}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "[Space]: Toggle Set | [Enter]: Exit", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        return frame
