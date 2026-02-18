import cv2
from PieceDetect import ChessBoardDetector

def main():
    # 1. 初始化检测器
    try:
        detector = ChessBoardDetector(
            model_path="chess_model.pkl",
            config_path="chessboardcfg.csv"
        )
    except Exception as e:
        print(f"Initialization Error: {e}")
        return

    # 2. 读取两张测试图 (移动前和移动后)
    img1 = cv2.imread("TestPictures/before_move.jpg")
    img2 = cv2.imread("TestPictures/after_move.jpg")

    if img1 is None or img2 is None:
        print("Error: Could not load test images. Please check file paths.")
        return

    # 3. 获取移动指令
    print("Analyzing movement...")
    move_str = detector.get_move(img1, img2)

    if move_str:
        print(f"Detected Move: {move_str}")
        # 这里你可以直接把 move_str 发送给 Stockfish 引擎了
    else:
        print("No clear move detected or multiple changes found.")

    # 4. (可选) 打印棋盘对比矩阵
    s1 = detector.detect_board(img1)
    s2 = detector.detect_board(img2)

    print("\nBefore Move:")
    for row in detector.get_matrix_view(s1): print(" ".join(row))

    print("\nAfter Move:")
    for row in detector.get_matrix_view(s2): print(" ".join(row))

if __name__ == "__main__":
    main()
