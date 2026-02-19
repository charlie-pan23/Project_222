import cv2
import time
from picamera2 import Picamera2
from PieceDetect import ChessBoardDetector

class VisionSystem:
    """
    Refined Vision System using Picamera2 and OpenCV.
    Integrates with the main loop for event-driven capture.
    """
    def __init__(self, model_path="chess_model.pkl", config_path="chessboardcfg.csv"):
        # 1. Initialize Camera (Picamera2 logic from your script)
        self.width, self.height = 1280, 960
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

        # 2. Initialize Logic Detector
        try:
            self.detector = ChessBoardDetector(
                model_path=model_path,
                config_path=config_path
            )
        except Exception as e:
            raise Exception(f"ChessBoardDetector Init Error: {e}")

    def capture_frame(self):
        """Captures a frame and converts it to BGR for OpenCV."""
        # Capture from Picamera2
        frame_rgb = self.picam2.capture_array()
        # Convert RGB to BGR for OpenCV compatibility
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return frame_bgr

    def check_initial_setup(self, frame):
        """Verify if ranks 1, 2, 7, 8 are fully occupied to start game."""
        occupancy_matrix = self.detector.detect_board(frame)
        view = self.detector.get_matrix_view(occupancy_matrix)

        # Rank 8, 7 (top) and Rank 2, 1 (bottom)
        top_ready = all(cell != "." for cell in view[0]) and all(cell != "." for cell in view[1])
        bottom_ready = all(cell != "." for cell in view[6]) and all(cell != "." for cell in view[7])
        return top_ready and bottom_ready

    def get_move_uci(self, img_before, img_after):
        """Interface to call the move detection logic."""
        return self.detector.get_move(img_before, img_after)

    def close(self):
        """Safely stop the camera."""
        self.picam2.stop()
