import cv2
import pandas as pd
import os
import sys
from picamera2 import Picamera2

# ==========================================
# 1. Configuration Section
# ==========================================
# Path to the configuration file
CSV_PATH = "Vision/chessboardcfg.csv"
# Target squares to highlight for alignment (Corners + Center check points)
TARGET_SQUARES = ['A1', 'A8', 'H1', 'H8', 'F6', 'C3', 'D5', 'E4']
# Camera Resolution
WIDTH, HEIGHT = 1280, 960

def main():
    # Check if the CSV file exists
    if not os.path.exists(CSV_PATH):
        print(f"Error: Configuration file not found at {CSV_PATH}")
        return

    # Load coordinate data
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Extract target square coordinates into a dictionary
    rois = {}
    for target in TARGET_SQUARES:
        row = df[df['label_name'] == target]
        if not row.empty:
            rois[target] = {
                'x': int(row.iloc[0]['bbox_x']),
                'y': int(row.iloc[0]['bbox_y']),
                'w': int(row.iloc[0]['bbox_width']),
                'h': int(row.iloc[0]['bbox_height'])
            }
        else:
            print(f"Warning: Square {target} not found in CSV")

    # Initialize Picamera2
    print("Initializing Picamera2...")
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (WIDTH, HEIGHT), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()

    print("--- Chessboard Alignment Tool Started ---")
    print("Instructions:")
    print("1. Adjust the physical board so the highlighted squares fit inside the green boxes.")
    print("2. Press 'q' to quit the program.")

    window_name = "Chessboard Alignment Tool"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    try:
        while True:
            # Capture frame and convert to BGR for OpenCV
            frame_rgb = picam2.capture_array()
            frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            # Draw the target squares on the frame
            for name, pos in rois.items():
                x, y, w, h = pos['x'], pos['y'], pos['w'], pos['h']

                # Draw rectangle (Color: Green, Thickness: 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Put label text above the rectangle
                cv2.putText(frame, name, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Add on-screen instructions
            cv2.putText(frame, "Align highlighted squares. Press 'q' to quit.", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Display the result
            cv2.imshow(window_name, frame)

            # Exit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        picam2.stop()
        cv2.destroyAllWindows()
        print("Program closed.")

if __name__ == "__main__":
    main()
