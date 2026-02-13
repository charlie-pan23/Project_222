import numpy as np
from Sim import plot_robot_arm

def solve_ik(target_x, target_y, target_z):
    """
    4 servos:   J1 - s0_yaw
                J2 - s1_pitch
                J3 - s2_pitch
                J4 - s3_pitch
    Angle limited [-90, 90] degrees for each joint.
    """
    # physical dimensions in cm
    L1_h, L1_v = 1, 9.5
    L2 = 10.5
    L3 = 10.0
    L4_v, L4_h = -5.0, 4.5
    L5_v = -10.0

    # J1
    j1_rad = np.arctan2(target_y, target_x)
    j1 = np.degrees(j1_rad)

    if not (-90 <= j1 <= 90):
        return None, "J1 Out of Range"

    # map target to 2D plane for J2, J3, J4 calculation
    r = np.sqrt(target_x**2 + target_y**2)

    target_r_p4 = r - L4_h
    target_z_p4 = target_z - (L4_v + L5_v) # target_z + 15

    tx = target_r_p4 - L1_h
    tz = target_z_p4 - L1_v
    dist_sq = tx**2 + tz**2
    dist = np.sqrt(dist_sq)

    # cheak reachability
    if not (abs(L2 - L3) <= dist <= (L2 + L3)):
        return None, "Target Unreachable"

    # J2, J3, J4
    # sign=1/-1

    K = (dist_sq + L2**2 - L3**2) / (2 * L2 * dist)
    K = np.clip(K, -1.0, 1.0)
    phi = np.arctan2(tx, tz)
    alpha = np.arccos(K)

    best_solution = None

    for sign in [1, -1]:
        j2_rad = phi - sign * alpha

        # theta_sum = j2 + j3
        #  10 * cos(sum) = tx - 10.5 * sin(j2)
        # -10 * sin(sum) = tz - 10.5 * cos(j2)
        term_x = tx - L2 * np.sin(j2_rad)
        term_z = tz - L2 * np.cos(j2_rad)
        sum_rad = np.arctan2(-term_z, term_x)

        j3_rad = sum_rad - j2_rad
        j4_rad = -sum_rad # When j2 + j3 + j4 = 0 the end effector is horizontal

        # Uniformization
        angles = [
            j1,
            np.degrees(j2_rad),
            np.degrees(j3_rad),
            np.degrees(j4_rad)
        ]

        angles = [(a + 180) % 360 - 180 for a in angles]

        # Check if all angles are within limits
        if all(-90.1 <= a <= 90.1 for a in angles): # 0.1 degree tolerance
            best_solution = [round(a, 2) for a in angles]
            break

    if best_solution:
        return best_solution, "Success"
    else:
        return None, "No solution within joint limits"

# --- Test ---
target = [15.5, 0, 5]
angles, status = solve_ik(*target)

if angles:
    print(f"Coordinate {target} | Angles: {angles}")
    plot_robot_arm(*angles)
else:
    print(f"Coordinate {target} | Calculate failed: {status}")

