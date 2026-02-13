import cv2
import numpy as np
import os

def verify_perspective(image_path):
    # 1. Load the original image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: {image_path} not found.")
        return

    # 2. Define the 4 corners (This is for manual testing)
    # You should replace these with the points from your manual calibration or identify_chessboard.py
    # Order: Top-Left, Top-Right, Bottom-Right, Bottom-Left
    # Based on your camera y < 0 (left-top), a1 is likely near the bottom-left in image
    print("Click the 4 outer corners of the chessboard grid:")
    print("Order: a8 (TL), h8 (TR), h1 (BR), a1 (BL)")

    points = []
    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append([x, y])
            cv2.circle(img_copy, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow("Calibration", img_copy)

    img_copy = img.copy()
    cv2.namedWindow("Calibration")
    cv2.setMouseCallback("Calibration", click_event)

    while len(points) < 4:
        cv2.imshow("Calibration", img_copy)
        if cv2.waitKey(1) & 0xFF == 27: break

    cv2.destroyWindow("Calibration")

    if len(points) == 4:
        print("\n" + "="*30)
        print("DETECTED CORNER PIXELS (Copy these):")
        print(f"pts = np.float32({points})")
        print("="*30)
        print(f"a8 (Top-Left):     {points[0]}")
        print(f"h8 (Top-Right):    {points[1]}")
        print(f"h1 (Bottom-Right): {points[2]}")
        print(f"a1 (Bottom-Left):  {points[3]}")
        print("="*30 + "\n")

    # 3. Apply Perspective Transform
    # We want a 800x800 square output
    size = 800
    src_pts = np.float32(points)
    dst_pts = np.float32([[0, 0], [size, 0], [size, size], [0, size]])

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(img, M, (size, size))

    # 4. Draw Verification Grid (8x8)
    grid_img = warped.copy()
    step = size // 8

    # Draw vertical and horizontal lines
    for i in range(9):
        # Vertical lines
        cv2.line(grid_img, (i * step, 0), (i * step, size), (0, 0, 255), 2)
        # Horizontal lines
        cv2.line(grid_img, (0, i * step), (size, i * step), (0, 0, 255), 2)

    # 5. Label squares for sanity check (a1 should be index 0,0 in your logic)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for row in range(8):
        for col in range(8):
            label = f"{chr(ord('a')+col)}{8-row}"
            cv2.putText(grid_img, label, (col*step + 10, row*step + 30),
                        font, 0.5, (0, 255, 0), 1)

    # 6. Show results
    cv2.imshow("Warped Verification", grid_img)
    print("Check if the red lines align with the board's black/white edges.")
    print("If the lines don't match, re-run and pick corners more accurately.")

    cv2.imwrite("verify_result.png", grid_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test with the sample image you provided
    verify_perspective("chess_data/Empty_Board_1.jpg")
