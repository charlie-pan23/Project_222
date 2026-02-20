import cv2
import pandas as pd
import os
from Utils.Logger import get_logger

logger = get_logger(__name__)

class VisionCalibrator:
    """
    Handles visual board alignment by rendering live feed with calibration markers.
    Integrated with pandas to load bounding boxes from chessboardcfg.csv.
    """
    def __init__(self, vision_system):
        # Injected from coordinator
        self.vision = vision_system

        # Absolute path resolution for the CSV
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(current_dir, "chessboardcfg.csv")

        # Two sets of target squares to highlight for alignment
        self.sets = {
            "Set A": ['A1', 'A8', 'H1', 'H8', 'F6', 'C3', 'D5', 'E4'],
            "Set B": ['A4', 'D8', 'H5', 'E1', 'G2', 'G7', 'B2', 'B7']
        }
        self.current_set_name = "Set A"
        self.window_name = "Chess Camera Calibration"

        # Load all ROI data from CSV once during initialization
        self.all_rois = self._load_roi_data()

    def _load_roi_data(self):
        """Extracts all square coordinates into a dictionary."""
        if not os.path.exists(self.csv_path):
            logger.error(f"Calibration CSV not found at {self.csv_path}")
            return {}

        try:
            df = pd.read_csv(self.csv_path)
            rois = {}
            # Map every label_name to its bounding box
            for _, row in df.iterrows():
                rois[row['label_name']] = {
                    'x': int(row['bbox_x']),
                    'y': int(row['bbox_y']),
                    'w': int(row['bbox_width']),
                    'h': int(row['bbox_height'])
                }
            return rois
        except Exception as e:
            logger.error(f"Error loading calibration CSV: {e}")
            return {}

    def toggle_set(self):
        """Switches between Set A and Set B."""
        self.current_set_name = "Set B" if self.current_set_name == "Set A" else "Set A"
        logger.info(f"Vision set toggled to: {self.current_set_name}")

    def run_calibration_frame(self):
        """
        Captures frame, draws green boxes for the active set, and updates UI.
        """
        frame = self.vision.capture_frame()
        if frame is None:
            return None

        display_frame = frame.copy()
        active_target_labels = self.sets[self.current_set_name]

        # Draw the target squares on the frame
        for label in active_target_labels:
            if label in self.all_rois:
                pos = self.all_rois[label]
                x, y, w, h = pos['x'], pos['y'], pos['w'], pos['h']

                # Draw green rectangle and label
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                logger.warning(f"Square {label} not found in ROI data.")

        # Overlay on-screen instructions
        cv2.putText(display_frame, f"ACTIVE: {self.current_set_name}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(display_frame, "[Space] Toggle Set | [Enter] Finish", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        cv2.imshow(self.window_name, display_frame)
        cv2.waitKey(1) # Necessary for X11/SSH window refresh

        return display_frame

    def close_window(self):
        """Safely closes the OpenCV window."""
        cv2.destroyWindow(self.window_name)
