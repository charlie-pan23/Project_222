import cv2
import numpy as np
import pandas as pd
import joblib
import os
import time

class ChessBoardDetector:
    def __init__(self, model_path="chess_8sets_model.pkl", config_path="chessboardcfg.csv"):
        """
        Initialize the detector by loading the SVM model and the board configuration.
        """
        # 1. Check if files exist
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # 2. Load Model Resources
        print(f"[PieceDetect] Loading model from {model_path}...")
        model_data = joblib.load(model_path)
        self.clf = model_data['svm_model']
        self.label_map = model_data['label_map']  # e.g. {5: 'empty_black'}
        hog_params = model_data['hog_params']

        # 3. Initialize HOG Descriptor with training parameters
        self.hog = cv2.HOGDescriptor(
            hog_params['winSize'],
            hog_params['blockSize'],
            hog_params['blockStride'],
            hog_params['cellSize'],
            hog_params['nbins']
        )

        # 4. Load Board Coordinates
        self.df_config = pd.read_csv(config_path)

        # 5. Configuration Constants
        self.resize_dim = (64, 128)  # Must match training size

        # Threshold for white pieces (strict).
        # Since we use average score of 3 frames, we keep this logic consistent.
        self.white_threshold = 0.62

        # Character mapping for output matrix
        self.char_map = {
            'BLACK': 'B',
            'WHITE': 'W',
            'EMPTY': '.'
        }

    def _get_faction_scores(self, img_roi):
        """
        Internal helper: Returns the raw probabilities for the 3 factions
        (Black, White, Empty) for a single ROI image.
        Returns tuple: (score_black, score_white, score_empty)
        """
        # Resize and Compute HOG
        img_resized = cv2.resize(img_roi, self.resize_dim)
        descriptor = self.hog.compute(img_resized)

        if descriptor is None:
            return 0.0, 0.0, 1.0

        descriptor = descriptor.reshape(1, -1)

        # Get probabilities for all 8 classes
        probs = self.clf.predict_proba(descriptor)[0]
        classes = self.clf.classes_

        # Aggregation: Sum probabilities into 3 Factions
        score_black = 0.0
        score_white = 0.0
        score_empty = 0.0

        for i, class_id in enumerate(classes):
            class_name = self.label_map[class_id]
            prob = probs[i]

            if 'empty' in class_name:
                score_empty += prob
            elif 'black' in class_name:
                score_black += prob
            elif 'white' in class_name:
                score_white += prob

        return score_black, score_white, score_empty

    def detect_pieces(self, picam2_obj):
        """
        Main method called by Detector.py.

        ARGS:
            picam2_obj: An initialized and started libcamera.Picamera2 object.

        LOGIC:
            1. Captures 3 arrays using picam2.capture_array().
            2. Handles XRGB8888 (4-channel) to Gray conversion.
            3. Averages the probabilities to reduce noise.
            4. Determines the final state based on average scores.
        """

        # Initialize a dictionary to accumulate scores for all 64 squares
        accumulated_scores = {}
        for _, row in self.df_config.iterrows():
            accumulated_scores[row['label_name']] = {'b': 0.0, 'w': 0.0, 'e': 0.0}

        SHOTS_COUNT = 3
        INTERVAL = 0.5

        # print(f"[PieceDetect] Starting multi-frame analysis ({SHOTS_COUNT} shots via Picamera2)...")

        # --- Phase 1: Capture and Accumulate ---
        for i in range(SHOTS_COUNT):
            # 1. Capture Array directly from Picamera2
            # Note: Picamera2 'capture_array' returns the image data directly
            try:
                frame = picam2_obj.capture_array()
            except Exception as e:
                print(f"[PieceDetect] Error capturing array: {e}")
                continue

            # 2. Convert Color Space (Handle XRGB8888/RGBA)
            # Picamera2 usually returns RGB or RGBA (if XRGB8888 is set)
            # OpenCV HOG needs Gray, but usually expects BGR input for cvtColor

            if frame is None:
                continue

            # Check channels: if 4 channels (XRGB/RGBA), convert to Gray directly or via BGR
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                # Assuming XRGB/RGBA -> Gray
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2GRAY)
            elif len(frame.shape) == 3 and frame.shape[2] == 3:
                # Assuming RGB -> Gray (Libcamera usually outputs RGB, OpenCV uses BGR)
                # But for Gray conversion, RGB2GRAY is safer if source is RGB
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            else:
                # Fallback
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 3. Process all squares
            for index, row in self.df_config.iterrows():
                label = row['label_name']
                x, y = int(row['bbox_x']), int(row['bbox_y'])
                w, h = int(row['bbox_width']), int(row['bbox_height'])

                # Crop ROI
                roi = gray_frame[max(0, y):min(y+h, gray_frame.shape[0]),
                                 max(0, x):min(x+w, gray_frame.shape[1])]

                if roi.size == 0:
                    s_b, s_w, s_e = 0.0, 0.0, 1.0
                else:
                    s_b, s_w, s_e = self._get_faction_scores(roi)

                accumulated_scores[label]['b'] += s_b
                accumulated_scores[label]['w'] += s_w
                accumulated_scores[label]['e'] += s_e

            # 4. Wait before next shot
            if i < SHOTS_COUNT - 1:
                time.sleep(INTERVAL)

        # --- Phase 2: Average and Decide ---
        results_map = {}

        for label, scores in accumulated_scores.items():
            avg_black = scores['b'] / SHOTS_COUNT
            avg_white = scores['w'] / SHOTS_COUNT
            avg_empty = scores['e'] / SHOTS_COUNT

            max_score = max(avg_black, avg_white, avg_empty)

            final_result = 'EMPTY'

            if max_score == avg_empty:
                final_result = 'EMPTY'
            elif max_score == avg_black:
                final_result = 'BLACK'
            else: # max_score == avg_white
                if avg_white >= self.white_threshold:
                    final_result = 'WHITE'
                else:
                    final_result = 'EMPTY'

            results_map[label] = self.char_map[final_result]

        # --- Phase 3: Construct Matrix ---
        row_indices = {'H': 0, 'G': 1, 'F': 2, 'E': 3, 'D': 4, 'C': 5, 'B': 6, 'A': 7}
        col_indices = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}

        board_matrix = [['.' for _ in range(8)] for _ in range(8)]

        for label, val in results_map.items():
            r_char = label[0]
            c_char = label[1]
            if r_char in row_indices and c_char in col_indices:
                r = row_indices[r_char]
                c = col_indices[c_char]
                board_matrix[r][c] = val

        return board_matrix
