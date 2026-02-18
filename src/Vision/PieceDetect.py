import cv2
import numpy as np
import pandas as pd
import joblib
import os

class ChessBoardDetector:
    def __init__(self, model_path="chess_model.pkl", config_path="chessboardcfg.csv"):
        """
        Initializes the ChessBoardDetector by loading the trained SVM model and the configuration for the chessboard squares.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}")

        data = joblib.load(model_path)
        self.model = data['svm_model']
        self.label_map = data['label_map']
        self.hp = data['hog_params']
        self.config_df = pd.read_csv(config_path)

        # Initialize HOG Descriptor with parameters from training
        self.hog = cv2.HOGDescriptor(
            self.hp['winSize'],
            self.hp['blockSize'],
            self.hp['blockStride'],
            self.hp['cellSize'],
            self.hp['nbins']
        )

    def _preprocess(self, img):
        """
        Internal method to preprocess the image for HOG feature extraction.
        This includes gamma correction, histogram equalization, and resizing to the expected input size.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gamma = 1.2
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        gray = cv2.LUT(gray, table)
        gray = cv2.equalizeHist(gray)
        return cv2.resize(gray, self.hp['winSize'])

    def detect_board(self, frame):
        board_status = {}
        for _, row in self.config_df.iterrows():
            square_name = row['label_name']
            x, y, w, h = int(row['bbox_x']), int(row['bbox_y']), int(row['bbox_width']), int(row['bbox_height'])

            roi = frame[y:y+h, x:x+w]
            processed_roi = self._preprocess(roi)
            features = self.hog.compute(processed_roi).flatten().reshape(1, -1)

            pred_id = self.model.predict(features)[0]
            board_status[square_name] = self.label_map[pred_id]

        return board_status

    def get_move(self, img_before, img_after):
        """
        Compares the detected board states before and after a move to determine the move made.
        """
        status_before = self.detect_board(img_before)
        status_after = self.detect_board(img_after)

        from_sq = ""
        to_sq = ""

        # Detect the move by comparing the two board states
        for sq in status_before.keys():
            s1 = status_before[sq]
            s2 = status_after[sq]

            if s1 != s2:
                # Start square: change from having a piece to being empty
                if s1 != 'empty' and s2 == 'empty':
                    from_sq = sq
                # Destination square: change from being empty to having a piece
                elif s2 != 'empty':
                    to_sq = sq

        if from_sq and to_sq:
            # Turn the move into standard algebraic notation (e.g., "E2E4")
            return f"{from_sq.lower()}{to_sq.lower()}"
        else:
            return None

    def get_matrix_view(self, board_status):
        # Get a matrix view of the board status for easier visualization
        rows = ['8', '7', '6', '5', '4', '3', '2', '1']
        cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        matrix = []
        for r in rows:
            row_data = [('W' if board_status.get(c+r) == 'white' else ('B' if board_status.get(c+r) == 'black' else '.')) for c in cols]
            matrix.append(row_data)
        return matrix
