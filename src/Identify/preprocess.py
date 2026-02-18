import cv2
import numpy as np
import pandas as pd
import os

CSV_PATH = "chess_data/chessboardcfg.csv"

TARGET_SQUARE = "A8"
INPUT_IMAGE_PATH = "templates/bQ/bQ_E5_3.jpg"

OUTPUT_DIR = "dataset/empty"
# OUTPUT_FILENAME = "068.jpg"

START_FILE_INDEX = 132

HOG_WIN_SIZE = (64, 128)


# Image Preprocessing Function
def preprocess_for_hog(img):

    if img is None:
        return None

    # Turn to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # A. Gamma implementation
    gamma = 1.2
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    gray = cv2.LUT(gray, table)

    # B. Histogram Equalization
    gray = cv2.equalizeHist(gray)

    # C. Resize to HOG window size
    processed_img = cv2.resize(gray, HOG_WIN_SIZE)

    return processed_img

def batch_process_sequential():
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file {CSV_PATH} does not exist.")
        return
    if not os.path.exists(INPUT_IMAGE_PATH):
        print(f"Error: Input image {INPUT_IMAGE_PATH} does not exist.")
        return

    df = pd.read_csv(CSV_PATH)

    full_img = cv2.imread(INPUT_IMAGE_PATH)
    if full_img is None:
        print("Error: Cannot read input image.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    print(f"Start processing: {INPUT_IMAGE_PATH}")
    print(f"File name starts from: {START_FILE_INDEX:03}.jpg")

    current_index = START_FILE_INDEX
    count = 0

    for index, row in df.iterrows():
        x, y, w, h = int(row['bbox_x']), int(row['bbox_y']), int(row['bbox_width']), int(row['bbox_height'])

        roi_img = full_img[y:y+h, x:x+w]

        processed_img = preprocess_for_hog(roi_img)

        if processed_img is not None:
            file_name = f"{current_index:03}.jpg"
            save_path = os.path.join(OUTPUT_DIR, file_name)

            cv2.imwrite(save_path, processed_img)

            current_index += 1
            count += 1

    print(f"Processed {count} preprocessed samples (file numbers {START_FILE_INDEX:03} to {current_index-1:03}).")

if __name__ == "__main__":
    batch_process_sequential()
