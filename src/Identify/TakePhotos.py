import cv2
import os
import time
from picamera2 import Picamera2

def main():

    width, height = 1280, 960
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (width, height), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()


    save_dir = "chess_data"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"Camera Ready. Resolution: {width}x{height}")
    print("Commands: [Space] - Capture | [S] - Confirm & Save | [Q] - Discard/Retake | [Esc] - Exit")

    captured_frame = None

    try:
        while True:

            frame_rgb = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)


            if captured_frame is None:
                display_frame = frame_bgr.copy()
                cv2.putText(display_frame, "LIVE - Press SPACE to capture", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow("Chess Camera", display_frame)
            else:

                display_captured = captured_frame.copy()
                cv2.putText(display_captured, "CAPTURED - [S] Save / [Q] Retake", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.imshow("Chess Camera", display_captured)

            key = cv2.waitKey(1) & 0xFF


            if key == ord(' '):
                captured_frame = frame_bgr.copy()
                print("Photo captured! Please verify.")

            elif key == ord('s') or key == ord('S'):
                if captured_frame is not None:

                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(save_dir, f"board_{timestamp}.jpg")
                    cv2.imwrite(filename, captured_frame)
                    print(f"Saved: {filename}")
                    captured_frame = None
                else:
                    print("Error: Capture a photo first (Press Space)!")

            elif key == ord('q') or key == ord('Q'):
                if captured_frame is not None:
                    captured_frame = None
                    print("Photo discarded. Back to Live view.")
                else:
                    break

            elif key == 27:
                break

    finally:
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
