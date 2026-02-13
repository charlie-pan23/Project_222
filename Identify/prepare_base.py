import cv2
import numpy as np
import os

def generate_base():
    folder = "chess_data"
    files = [os.path.join(folder, f"Empty_Board_{i}.jpg") for i in range(1, 6)]

    print("Reading and averaging 5 images...")
    imgs = []
    for f in files:
        img = cv2.imread(f)
        if img is None:
            print(f"Error: {f} not found!")
            return
        imgs.append(img.astype(np.float32))

    avg_img = np.mean(imgs, axis=0).astype(np.uint8)

    src_pts = np.float32([[330, 259], [849, 227], [946, 720], [264, 764]])
    dst_pts = np.float32([[0, 0], [800, 0], [800, 800], [0, 800]])

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_base = cv2.warpPerspective(avg_img, M, (800, 800))

    output_path = "chess_data/Empty_Board.jpg"
    cv2.imwrite(output_path, warped_base)
    print(f"Success! Warped base image saved to {output_path}")

if __name__ == "__main__":
    generate_base()
