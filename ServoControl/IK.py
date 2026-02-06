import ikpy.chain
import json
import numpy as np
import math
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
urdf_path = os.path.join(current_dir, "arm.urdf")
config_path = os.path.join(current_dir, "armconfig.json")

my_chain = ikpy.chain.Chain.from_urdf_file(
    urdf_path,
    active_links_mask=[False, True, True, True, True, False, False]
)

with open('armconfig.json', 'r') as f:
    config = json.load(f)


def get_servo_command(target_xyz):
    initial_guess = [0.0] * len(my_chain.links)
    if len(initial_guess) > 6:
        initial_guess[6] = 0.5

    joint_angles_rad = my_chain.inverse_kinematics(
        target_xyz,
        initial_position=initial_guess
    )

    servo_results = {}

    active_joints = ["s0_yaw", "s1_pitch", "s2_pitch", "s3_pitch", "s4_roll"]

    for i, joint_name in enumerate(active_joints):
        servo_info = next(item for item in config["servos"] if item["id"] == joint_name)

        deg_from_ik = math.degrees(joint_angles_rad[i+1])

        final_angle = servo_info["zero_offset"] + (servo_info["direction"] * deg_from_ik)

        final_angle = max(servo_info["min_limit"], min(servo_info["max_limit"], final_angle))
        servo_results[joint_name] = round(final_angle, 2)

    return servo_results


# target = [0.10, 0.10, 0.00]
# try:
#     commands = get_servo_command(target)
#     print(f"target: {target} ,command: {commands}")
# except Exception as e:
#     print(f"calculate error: {e}")
