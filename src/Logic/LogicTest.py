from Logic.chess_logic_manager import ChessLogicManager
import time

def print_board_ui(manager, title="当前棋盘状态"):
    """美化输出矩阵"""
    matrix = manager.get_board_matrix()
    print(f"\n===== {title} =====")
    print("    a b c d e f g h")
    print("  +-----------------+")
    for i, row in enumerate(matrix):
        print(f"{8-i} | {' '.join(row)} | {8-i}")
    print("  +-----------------+")
    print("    a b c d e f g h")
    print(f"FEN: {manager.get_current_fen()}\n")

def run_extended_test():
    # 1. 初始化 (机械臂设为黑棋)
    # 注意：根据你的导入规范，内部会调用 Logic.chess_engine
    manager = ChessLogicManager(robot_color=False)
    manager.start_engine()

    try:
        # ---- 初始状态 ----
        print_board_ui(manager, "游戏开始：初始状态")

        # ---- 步骤 1: 人类走棋 (白方) ----
        human_move = "a2a4"
        print(f"[人类行动] 尝试执行: {human_move}...")
        success, info = manager.update_human_move(human_move)

        if success:
            print_board_ui(manager, f"人类走子后 ({human_move})")
        else:
            print(f"人类移动失败: {info}")
            return

        # ---- 步骤 2: 机器人回应 (黑方) ----
        print("[机器人行动] Stockfish 思考中...")
        # 模拟思考延迟
        time.sleep(1)

        # 调用引擎获取最佳走法
        robot_uci, robot_info = manager.get_robot_move()

        print(f"\n>>> 机器人(Stockfish) 决策完成！")
        print(f">>> 走法: {robot_uci}")
        print(f">>> 动作类型: {robot_info['move_type']} (是否有吃子: {robot_info['move_type'] == 'capture'})")
        print(f">>> 是否将军: {robot_info['is_check']}")

        # ---- 最终状态 ----
        print_board_ui(manager, f"机器人走子后 ({robot_uci})")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        # 必须关闭引擎，否则 stockfish.exe 进程会残留在后台
        manager.stop()
        print("测试结束，引擎已安全关闭。")

if __name__ == "__main__":
    run_extended_test()
