import cv2
import numpy as np

# --- 1. SETTINGS ---
# Path to your PRE-SAVED warped empty board
EMPTY_BOARD_PATH = "chess_data/Empty_Board_1.jpg"

def get_e4_cell(warped_img):
    """ Extracts the e4 square (Row 4, Col 4 in 0-indexing) """
    h, w = warped_img.shape[:2]
    cell_h, cell_w = h // 8, w // 8
    # e4 is at row index 4, column index 4
    return warped_img[4*cell_h:5*cell_h, 4*cell_w:5*cell_w]

def main():
    # Load your empty calibration board
    warped_empty = cv2.imread(EMPTY_BOARD_PATH)
    if warped_empty is None:
        print("Error: Could not find warped_empty.jpg! Please calibrate first.")
        return

    empty_e4 = get_e4_cell(warped_empty)

    cap = cv2.VideoCapture(0) # 0 is usually the default camera
    print("\n=== Interactive Feature Collector ===")
    print("1. Place your piece on square E4.")
    print("2. Press [SPACE] to capture and extract features.")
    print("3. Press [Q] to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # IMPORTANT: Replace the next line with your actual perspective transform function
        # warped_frame = your_perspective_transform(frame)
        warped_frame = frame  # Placeholder

        # Draw a simple UI on the live feed
        cv2.putText(frame, "Ready - Press SPACE to Capture", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Live Feed", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '): # Space bar
            print("\n--- Capturing E4 Square ---")
            curr_e4 = get_e4_cell(warped_frame)

            # Use the integrated function we built (extract_and_verify_features)
            # This will show the [Original | Mask | Result] window
            features = extract_and_verify_features(empty_e4, curr_e4, "Testing_Piece")

            if features:
                print("\nCopy these values to your JSON:")
                print(f"Area:   {features['area']}")
                print(f"Height: {features['height']}")
                print(f"Ratio:  {features['aspect_ratio']}")
                print(f"Extent: {features['extent']}")
                print("-" * 30)
                print("Returning to live feed...")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# --- RE-INCLUDE THE CORE FUNCTION HERE ---
def extract_and_verify_features(empty_cell, current_cell, piece_name):
    # (Copy the English version of the function I provided in the previous turn here)
    # ... code for diff, threshold, morphology, contours, etc.
    # ... include the imshow("Verification", final_view) code
    pass

if __name__ == "__main__":
    main()
