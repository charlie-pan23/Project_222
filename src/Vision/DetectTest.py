import cv2
import numpy as np
import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt

# ==========================================
# 1. Configuration Area
# ==========================================
MODEL_PATH = "chess_8sets_model.pkl"       # 训练好的8分类模型路径
CONFIG_PATH = "chessboardcfg.csv"          # 棋盘坐标配置文件路径
TEST_IMG_PATH = "TestPictures/Test3.jpg"   # 测试图片路径

WHITE_CONFIDENCE_THRESHOLD = 0.60

# 字符映射 (用于矩阵显示)
CHAR_MAP = {
    'BLACK': 'B',
    'WHITE': 'W',
    'EMPTY': '.'
}

# 颜色定义 (BGR 格式)
COLOR_MAP = {
    'BLACK': (0, 0, 255),    # 红色框标黑棋
    'WHITE': (0, 255, 0),    # 绿色框标白棋
    'EMPTY': (200, 200, 200) # 灰色框标空位
}

# ==========================================
# 2. 资源加载与初始化
# ==========================================
def load_resources():
    # 检查文件是否存在
    if not os.path.exists(MODEL_PATH):
        print(f"Error: 模型文件 {MODEL_PATH} 未找到！")
        return None, None, None, None
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: 配置文件 {CONFIG_PATH} 未找到！")
        return None, None, None, None

    print(f"Loading model from {MODEL_PATH}...")
    model_data = joblib.load(MODEL_PATH)
    clf = model_data['svm_model']
    label_map = model_data['label_map'] # ID -> Name (e.g., {5: 'empty_black'})
    hog_params = model_data['hog_params']

    # 重建 HOG 描述符
    hog = cv2.HOGDescriptor(
        hog_params['winSize'],
        hog_params['blockSize'],
        hog_params['blockStride'],
        hog_params['cellSize'],
        hog_params['nbins']
    )

    # 加载 CSV 配置
    print(f"Loading board config from {CONFIG_PATH}...")
    df = pd.read_csv(CONFIG_PATH)

    return clf, hog, label_map, df

# ==========================================
# 3. 核心预测逻辑 (阵营加权 + 独立阈值)
# ==========================================
def predict_roi(img_roi, clf, hog, label_map):
    # 1. 预处理：缩放并计算 HOG
    # 必须缩放到训练时的大小 (64x128)
    img_roi_resized = cv2.resize(img_roi, (64, 128))
    descriptor = hog.compute(img_roi_resized)

    if descriptor is None:
        return 'EMPTY', 0.0

    descriptor = descriptor.reshape(1, -1)

    # 2. 获取所有 8 个类别的概率
    # probs 顺序对应 clf.classes_
    probs = clf.predict_proba(descriptor)[0]
    classes = clf.classes_

    # 3. 阵营概率聚合 (Faction Aggregation)
    score_black = 0.0
    score_white = 0.0
    score_empty = 0.0

    for i, class_id in enumerate(classes):
        class_name = label_map[class_id] # 获取类别名称，如 'white_shadow'
        prob = probs[i]

        # 根据名称关键词归类
        if 'empty' in class_name:
            score_empty += prob
        elif 'black' in class_name:
            score_black += prob
        elif 'white' in class_name:
            score_white += prob

    # 4. 决策逻辑 (Decision Logic)
    # 找出三个阵营中的最高分
    max_score = max(score_black, score_white, score_empty)

    # 情况 A: Empty 得分最高 -> 直接判空
    if max_score == score_empty:
        return 'EMPTY', score_empty

    # 情况 B: Black 得分最高 -> 只要最高就赢 (保持原标准)
    elif max_score == score_black:
        return 'BLACK', score_black

    # 情况 C: White 得分最高 -> 需要过 0.7 的门槛
    else: # max_score == score_white
        if score_white >= WHITE_CONFIDENCE_THRESHOLD:
            return 'WHITE', score_white
        else:
            # 虽然看起来最像白棋，但信度不够，强行判为空
            # 这种情况通常是亮度较高的空地板
            return 'EMPTY', score_white

# ==========================================
# 4. 主流程
# ==========================================
def main():
    clf, hog, label_map, df_config = load_resources()
    if clf is None: return

    # 读取图片
    if not os.path.exists(TEST_IMG_PATH):
        print(f"Error: 测试图片 {TEST_IMG_PATH} 不存在")
        return

    print(f"Processing image: {TEST_IMG_PATH}")
    original_img = cv2.imread(TEST_IMG_PATH)
    gray_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    output_img = original_img.copy()

    results_dict = {} # 存储结果 {'A1': 'B', 'A2': '.', ...}

    print(f"Running detection with WHITE_THRESHOLD = {WHITE_CONFIDENCE_THRESHOLD}...")

    # 遍历配置文件中的每一个格子
    for index, row in df_config.iterrows():
        label = row['label_name']
        x, y = int(row['bbox_x']), int(row['bbox_y'])
        w, h = int(row['bbox_width']), int(row['bbox_height'])

        # 提取 ROI (防止越界)
        roi = gray_img[max(0, y):min(y+h, gray_img.shape[0]),
                       max(0, x):min(x+w, gray_img.shape[1])]

        if roi.size == 0:
            results_dict[label] = '?'
            continue

        # 预测
        result, confidence = predict_roi(roi, clf, hog, label_map)
        results_dict[label] = CHAR_MAP[result]

        # 绘图 (画框和文字)
        color = COLOR_MAP[result]
        cv2.rectangle(output_img, (x, y), (x+w, y+h), color, 2)

        # 只有非空才显示详细信息，保持画面整洁
        if result != 'EMPTY':
            label_text = f"{result[0]}:{confidence:.2f}"
            # 绘制文字背景条
            cv2.rectangle(output_img, (x, y-15), (x+55, y), color, -1)
            cv2.putText(output_img, label_text, (x+2, y-3),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

    # =================输出结果矩阵=================
    # 按照 H->A (上到下), 8->1 (左到右) 的顺序打印

    rows = ['H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
    cols = ['8', '7', '6', '5', '4', '3', '2', '1']

    print("\n====== Chessboard Recognition Matrix ======")
    print("   " + " ".join(cols)) # 打印列号
    print("  " + "-"*17)

    for r_char in rows:
        row_str = f"{r_char}| "
        for c_char in cols:
            key = f"{r_char}{c_char}"
            val = results_dict.get(key, '?')
            row_str += f"{val} "
        print(row_str)
    print("==========================================")

    # 保存结果图
    save_path = "Result_Output_Threshold.jpg"
    cv2.imwrite(save_path, output_img)
    print(f"\nResult image saved to '{save_path}'")

    # 显示图片
    plt.figure(figsize=(12, 12))
    plt.imshow(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB))
    plt.title(f"Detected (White Threshold >= {WHITE_CONFIDENCE_THRESHOLD})")
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    main()
