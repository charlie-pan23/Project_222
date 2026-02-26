# import cv2
# import numpy as np
# import pandas as pd
# import joblib
# import os
# import matplotlib.pyplot as plt

# # ==========================================
# # 1. Configuration Area
# # ==========================================
# MODEL_PATH = "chess_8sets_model.pkl"       # 训练好的8分类模型路径
# CONFIG_PATH = "chessboardcfg.csv"          # 棋盘坐标配置文件路径
# TEST_IMG_PATH = "TestPictures/Test3.jpg"   # 测试图片路径

# WHITE_CONFIDENCE_THRESHOLD = 0.60

# # 字符映射 (用于矩阵显示)
# CHAR_MAP = {
#     'BLACK': 'B',
#     'WHITE': 'W',
#     'EMPTY': '.'
# }

# # 颜色定义 (BGR 格式)
# COLOR_MAP = {
#     'BLACK': (0, 0, 255),    # 红色框标黑棋
#     'WHITE': (0, 255, 0),    # 绿色框标白棋
#     'EMPTY': (200, 200, 200) # 灰色框标空位
# }

# # ==========================================
# # 2. 资源加载与初始化
# # ==========================================
# def load_resources():
#     # 检查文件是否存在
#     if not os.path.exists(MODEL_PATH):
#         print(f"Error: 模型文件 {MODEL_PATH} 未找到！")
#         return None, None, None, None
#     if not os.path.exists(CONFIG_PATH):
#         print(f"Error: 配置文件 {CONFIG_PATH} 未找到！")
#         return None, None, None, None

#     print(f"Loading model from {MODEL_PATH}...")
#     model_data = joblib.load(MODEL_PATH)
#     clf = model_data['svm_model']
#     label_map = model_data['label_map'] # ID -> Name (e.g., {5: 'empty_black'})
#     hog_params = model_data['hog_params']

#     # 重建 HOG 描述符
#     hog = cv2.HOGDescriptor(
#         hog_params['winSize'],
#         hog_params['blockSize'],
#         hog_params['blockStride'],
#         hog_params['cellSize'],
#         hog_params['nbins']
#     )

#     # 加载 CSV 配置
#     print(f"Loading board config from {CONFIG_PATH}...")
#     df = pd.read_csv(CONFIG_PATH)

#     return clf, hog, label_map, df

# # ==========================================
# # 3. 核心预测逻辑 (阵营加权 + 独立阈值)
# # ==========================================
# def predict_roi(img_roi, clf, hog, label_map):
#     # 1. 预处理：缩放并计算 HOG
#     # 必须缩放到训练时的大小 (64x128)
#     img_roi_resized = cv2.resize(img_roi, (64, 128))
#     descriptor = hog.compute(img_roi_resized)

#     if descriptor is None:
#         return 'EMPTY', 0.0

#     descriptor = descriptor.reshape(1, -1)

#     # 2. 获取所有 8 个类别的概率
#     # probs 顺序对应 clf.classes_
#     probs = clf.predict_proba(descriptor)[0]
#     classes = clf.classes_

#     # 3. 阵营概率聚合 (Faction Aggregation)
#     score_black = 0.0
#     score_white = 0.0
#     score_empty = 0.0

#     for i, class_id in enumerate(classes):
#         class_name = label_map[class_id] # 获取类别名称，如 'white_shadow'
#         prob = probs[i]

#         # 根据名称关键词归类
#         if 'empty' in class_name:
#             score_empty += prob
#         elif 'black' in class_name:
#             score_black += prob
#         elif 'white' in class_name:
#             score_white += prob

#     # 4. 决策逻辑 (Decision Logic)
#     # 找出三个阵营中的最高分
#     max_score = max(score_black, score_white, score_empty)

#     # 情况 A: Empty 得分最高 -> 直接判空
#     if max_score == score_empty:
#         return 'EMPTY', score_empty

#     # 情况 B: Black 得分最高 -> 只要最高就赢 (保持原标准)
#     elif max_score == score_black:
#         return 'BLACK', score_black

#     # 情况 C: White 得分最高 -> 需要过 0.7 的门槛
#     else: # max_score == score_white
#         if score_white >= WHITE_CONFIDENCE_THRESHOLD:
#             return 'WHITE', score_white
#         else:
#             # 虽然看起来最像白棋，但信度不够，强行判为空
#             # 这种情况通常是亮度较高的空地板
#             return 'EMPTY', score_white

# # ==========================================
# # 4. 主流程
# # ==========================================
# def main():
#     clf, hog, label_map, df_config = load_resources()
#     if clf is None: return

#     # 读取图片
#     if not os.path.exists(TEST_IMG_PATH):
#         print(f"Error: 测试图片 {TEST_IMG_PATH} 不存在")
#         return

#     print(f"Processing image: {TEST_IMG_PATH}")
#     original_img = cv2.imread(TEST_IMG_PATH)
#     gray_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
#     output_img = original_img.copy()

#     results_dict = {} # 存储结果 {'A1': 'B', 'A2': '.', ...}

#     print(f"Running detection with WHITE_THRESHOLD = {WHITE_CONFIDENCE_THRESHOLD}...")

#     # 遍历配置文件中的每一个格子
#     for index, row in df_config.iterrows():
#         label = row['label_name']
#         x, y = int(row['bbox_x']), int(row['bbox_y'])
#         w, h = int(row['bbox_width']), int(row['bbox_height'])

#         # 提取 ROI (防止越界)
#         roi = gray_img[max(0, y):min(y+h, gray_img.shape[0]),
#                        max(0, x):min(x+w, gray_img.shape[1])]

#         if roi.size == 0:
#             results_dict[label] = '?'
#             continue

#         # 预测
#         result, confidence = predict_roi(roi, clf, hog, label_map)
#         results_dict[label] = CHAR_MAP[result]

#         # 绘图 (画框和文字)
#         color = COLOR_MAP[result]
#         cv2.rectangle(output_img, (x, y), (x+w, y+h), color, 2)

#         # 只有非空才显示详细信息，保持画面整洁
#         if result != 'EMPTY':
#             label_text = f"{result[0]}:{confidence:.2f}"
#             # 绘制文字背景条
#             cv2.rectangle(output_img, (x, y-15), (x+55, y), color, -1)
#             cv2.putText(output_img, label_text, (x+2, y-3),
#                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

#     # =================输出结果矩阵=================
#     # 按照 H->A (上到下), 8->1 (左到右) 的顺序打印

#     rows = ['H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
#     cols = ['8', '7', '6', '5', '4', '3', '2', '1']

#     print("\n====== Chessboard Recognition Matrix ======")
#     print("   " + " ".join(cols)) # 打印列号
#     print("  " + "-"*17)

#     for r_char in rows:
#         row_str = f"{r_char}| "
#         for c_char in cols:
#             key = f"{r_char}{c_char}"
#             val = results_dict.get(key, '?')
#             row_str += f"{val} "
#         print(row_str)
#     print("==========================================")

#     # 保存结果图
#     save_path = "Result_Output_Threshold.jpg"
#     cv2.imwrite(save_path, output_img)
#     print(f"\nResult image saved to '{save_path}'")

#     # 显示图片
#     plt.figure(figsize=(12, 12))
#     plt.imshow(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB))
#     plt.title(f"Detected (White Threshold >= {WHITE_CONFIDENCE_THRESHOLD})")
#     plt.axis('off')
#     plt.show()

# if __name__ == "__main__":
#     main()



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
        self.label_map = model_data['label_map']
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
        self.white_threshold = 0.63

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
        # 1. Resize and Compute HOG
        img_resized = cv2.resize(img_roi, self.resize_dim)
        descriptor = self.hog.compute(img_resized)

        if descriptor is None:
            # If HOG fails, assume empty
            return 0.0, 0.0, 1.0

        descriptor = descriptor.reshape(1, -1)

        # 2. Get probabilities for all 8 classes
        probs = self.clf.predict_proba(descriptor)[0]
        classes = self.clf.classes_

        # 3. Aggregation: Sum probabilities into 3 Factions
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

    def detect_pieces(self, video_capture):
        """
        Main method called by Detector.py.
        MODIFIED: Now takes 'video_capture' (cv2.VideoCapture object) instead of a single frame.

        Logic:
        1. Captures 3 frames with 0.5s interval.
        2. Calculates probabilities for each square in each frame.
        3. Averages the probabilities to reduce noise.
        4. Determines the final state based on average scores.
        """

        # Initialize a dictionary to accumulate scores for all 64 squares
        # Format: {'A1': {'b': 0.0, 'w': 0.0, 'e': 0.0}, ...}
        accumulated_scores = {}
        for _, row in self.df_config.iterrows():
            accumulated_scores[row['label_name']] = {'b': 0.0, 'w': 0.0, 'e': 0.0}

        SHOTS_COUNT = 3
        INTERVAL = 0.5

        print(f"[PieceDetect] Starting multi-frame analysis ({SHOTS_COUNT} shots)...")

        # --- Phase 1: Capture and Accumulate ---
        for i in range(SHOTS_COUNT):
            # 1. Capture Frame
            ret, frame = video_capture.read()
            if not ret:
                print(f"[PieceDetect] Error: Failed to read frame {i+1}")
                continue

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 2. Process all squares
            for index, row in self.df_config.iterrows():
                label = row['label_name']
                x, y = int(row['bbox_x']), int(row['bbox_y'])
                w, h = int(row['bbox_width']), int(row['bbox_height'])

                # Crop ROI
                roi = gray_frame[max(0, y):min(y+h, gray_frame.shape[0]),
                                 max(0, x):min(x+w, gray_frame.shape[1])]

                if roi.size == 0:
                    # If ROI invalid, treat as empty (add 1.0 to empty score)
                    s_b, s_w, s_e = 0.0, 0.0, 1.0
                else:
                    # Get raw probability scores for this shot
                    s_b, s_w, s_e = self._get_faction_scores(roi)

                # Accumulate
                accumulated_scores[label]['b'] += s_b
                accumulated_scores[label]['w'] += s_w
                accumulated_scores[label]['e'] += s_e

            # 3. Wait before next shot (if not the last one)
            if i < SHOTS_COUNT - 1:
                time.sleep(INTERVAL)

        # --- Phase 2: Average and Decide ---

        # Dictionary to store final classification labels
        results_map = {}

        for label, scores in accumulated_scores.items():
            # Calculate Average Scores
            avg_black = scores['b'] / SHOTS_COUNT
            avg_white = scores['w'] / SHOTS_COUNT
            avg_empty = scores['e'] / SHOTS_COUNT

            # Decision Logic (Same as before, but using Average Scores)
            max_score = max(avg_black, avg_white, avg_empty)

            final_result = 'EMPTY' # Default

            if max_score == avg_empty:
                final_result = 'EMPTY'

            elif max_score == avg_black:
                final_result = 'BLACK'

            else: # max_score == avg_white
                # Apply Threshold check on the AVERAGE score
                if avg_white >= self.white_threshold:
                    final_result = 'WHITE'
                else:
                    final_result = 'EMPTY'

            results_map[label] = self.char_map[final_result]

        # --- Phase 3: Construct Matrix ---

        # Mapping visual board layout to matrix indices
        row_indices = {'H': 0, 'G': 1, 'F': 2, 'E': 3, 'D': 4, 'C': 5, 'B': 6, 'A': 7}
        col_indices = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}

        # Initialize 8x8 empty board
        board_matrix = [['.' for _ in range(8)] for _ in range(8)]

        for label, val in results_map.items():
            r_char = label[0] # 'A'
            c_char = label[1] # '1'

            if r_char in row_indices and c_char in col_indices:
                r = row_indices[r_char]
                c = col_indices[c_char]
                board_matrix[r][c] = val

        return board_matrix

class MockCamera:
    def __init__(self, image_paths):
        self.frames = []
        print(f"[MockCamera] Loading {len(image_paths)} test frames...")
        for path in image_paths:
            if not os.path.exists(path):
                print(f"[Error] Image not found: {path}")
                continue
            img = cv2.imread(path)
            if img is None:
                print(f"[Error] Failed to read image: {path}")
                continue
            self.frames.append(img)

        self.current_frame_index = 0

    def read(self):
        """
        Simulates cv2.VideoCapture.read()
        Returns: (ret, frame)
        """
        if self.current_frame_index < len(self.frames):
            frame = self.frames[self.current_frame_index]
            self.current_frame_index += 1
            # Return True (success) and the frame
            # Simulate a slight delay to mimic camera reading if needed
            time.sleep(0.1)
            return True, frame
        else:
            # If we run out of images, define behavior (loop or stop)
            # For this test, let's loop the last frame or return False
            print("[MockCamera] No more frames, reusing last frame.")
            if self.frames:
                return True, self.frames[-1]
            return False, None

    def release(self):
        pass

if __name__ == "__main__":
    try:
        # 1. Initialize Detector
        detector = ChessBoardDetector()
        print("Initialization successful.")

        # 2. Define Test Images
        # Ensure these files exist in your 'TestPictures' folder
        test_images = [
            "TestPictures/Test2.jpg",
            "TestPictures/Test2.jpg",
            "TestPictures/Test2.jpg"
        ]

        # 3. Create Mock Camera
        # This object behaves exactly like cv2.VideoCapture logic inside detect_pieces
        mock_cap = MockCamera(test_images)

        # 4. Run Detection
        if mock_cap.frames:
            print("-" * 30)
            print("Testing detection with static images...")

            # The detector will call mock_cap.read() 3 times internally
            board_matrix = detector.detect_pieces(mock_cap)

            # 5. Print Result Matrix
            print("\n====== Recognition Result ======")
            rows = ['H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
            cols = ['8', '7', '6', '5', '4', '3', '2', '1']

            print("   " + " ".join(cols))
            print("  " + "-"*17)

            for r_idx, row_data in enumerate(board_matrix):
                print(f"{rows[r_idx]}| {' '.join(row_data)}")
            print("================================")

        else:
            print("Error: No valid images loaded into MockCamera.")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
