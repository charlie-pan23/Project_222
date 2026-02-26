import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def rotation_matrix_z(theta):
    """绕Z轴旋转矩阵 (Yaw)"""
    rad = np.radians(theta)
    return np.array([
        [np.cos(rad), -np.sin(rad), 0],
        [np.sin(rad),  np.cos(rad), 0],
        [0,            0,           1]
    ])

def rotation_matrix_y(theta):
    """绕Y轴旋转矩阵 (Pitch)"""
    rad = np.radians(theta)
    return np.array([
        [ np.cos(rad), 0, np.sin(rad)],
        [ 0,           1, 0          ],
        [-np.sin(rad), 0, np.cos(rad)]
    ])

def plot_robot_arm(j1, j2, j3, j4):
    # --- 初始各段向量 (基于零位状态) ---
    v_base_h = np.array([1.5, 0, 0])   # 基座水平段
    v_base_v = np.array([0, 0, 9.5])   # 基座垂直段
    v_link2  = np.array([0, 0, 10.5])  # 第二段垂直
    v_link3  = np.array([10, 0, 0])    # 第三段水平
    v_link4_v = np.array([0, 0, -5])   # 第四段末端L形-垂直部分
    v_link4_h = np.array([4.5, 0, 0])  # 第四段末端L形-水平部分
    v_link5_down = np.array([0, 0, -10]) # 新增：末端竖直向下10cm

    # --- 计算变换矩阵 ---
    t1 = rotation_matrix_z(j1)
    t2 = t1 @ rotation_matrix_y(j2)
    t3 = t2 @ rotation_matrix_y(j3)
    t4 = t3 @ rotation_matrix_y(j4)

    # --- 计算各关键点坐标 ---
    p0 = np.array([0, 0, 0])
    p1 = p0 + t1 @ v_base_h
    p2 = p1 + t1 @ v_base_v            # 关节2位置
    p3 = p2 + t2 @ v_link2             # 关节3位置
    p4 = p3 + t3 @ v_link3             # 关节4位置
    p5 = p4 + t4 @ v_link4_v
    p6 = p5 + t4 @ v_link4_h           # 原末端位置
    p7 = p6 + t4 @ v_link5_down        # 新增末端位置

    points = np.array([p0, p1, p2, p3, p4, p5, p6, p7])

    # --- 绘图部分 ---
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制连杆 (线段)
    ax.plot(points[:, 0], points[:, 1], points[:, 2], '-o',
            linewidth=3, markersize=5, label='Robot Arm', color='#1f77b4')

    # 绘制关键关节 (红色球点)
    joints = np.array([p0, p2, p3, p4])
    ax.scatter(joints[:, 0], joints[:, 1], joints[:, 2], color='red', s=50, zorder=5)

    # 设置坐标轴范围
    ax.set_xlim([-25, 25])
    ax.set_ylim([-25, 25])
    ax.set_zlim([-5, 30])

    ax.set_xlabel('X (cm)')
    ax.set_ylabel('Y (cm)')
    ax.set_zlabel('Z (cm)')
    ax.set_title(f'Robot Arm Pose\nJ1={j1}°, J2={j2}°, J3={j3}°, J4={j4}°')

    ax.set_aspect('equal')
    plt.legend()
    plt.show()

# --- 测试角度 ---
angles = [0, 0, 0, 0]
plot_robot_arm(*angles)
