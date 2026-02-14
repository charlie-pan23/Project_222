import cv2
import numpy as np
import os

points = []


def square_name(row, col):
    return chr(ord("a") + col) + str(row + 1)


def build_homographies(corners_img):
    src = np.array(corners_img, dtype=np.float32)
    dst = np.array([
        [0.0, 0.0],
        [8.0, 0.0],
        [8.0, 8.0],
        [0.0, 8.0],
    ], dtype=np.float32)

    H_img2board = cv2.getPerspectiveTransform(src, dst)
    H_board2img = cv2.getPerspectiveTransform(dst, src)
    return H_img2board, H_board2img


def project_board_to_image(u, v, H_board2img):
    pt = np.array([[[float(u), float(v)]]], dtype=np.float32)
    xy = cv2.perspectiveTransform(pt, H_board2img)[0, 0]
    return int(xy[0]), int(xy[1])


def draw_grid_and_labels(image, corners_img, draw_grid=True, draw_labels=True):
    out = image.copy()
    _, H_board2img = build_homographies(corners_img)

    cv2.polylines(out, [np.array(corners_img, dtype=np.int32)], True, (0, 0, 255), 3)

    if draw_grid:
        for i in range(1, 8):
            x1, y1 = project_board_to_image(i, 0, H_board2img)
            x2, y2 = project_board_to_image(i, 8, H_board2img)
            cv2.line(out, (x1, y1), (x2, y2), (0, 255, 0), 2)

            x3, y3 = project_board_to_image(0, i, H_board2img)
            x4, y4 = project_board_to_image(8, i, H_board2img)
            cv2.line(out, (x3, y3), (x4, y4), (0, 255, 0), 2)

    if draw_labels:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 2

        for row in range(8):
            for col in range(8):
                row_top = 7 - row
                u = col + 0.5
                v = row_top + 0.5

                x, y = project_board_to_image(u, v, H_board2img)

                label = square_name(row, col)
                (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
                x0 = x - tw // 2
                y0 = y + th // 2

                cv2.putText(out, label, (x0, y0), font, font_scale, (0, 0, 0),
                            thickness + 2, cv2.LINE_AA)
                cv2.putText(out, label, (x0, y0), font, font_scale, (255, 255, 255),
                            thickness, cv2.LINE_AA)

    return out


def main():
    global points

    img = cv2.imread("11.jpg")
    if img is None:
        print("Image not found: 11.jpg")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, "11_labeled_manual.png")

    vis = img.copy()
    win = "Click 4 corners: TL -> TR -> BR -> BL"
    cv2.imshow(win, vis)

    state = {"result": None}

    def save_result():
        if state["result"] is None:
            print("Nothing to save yet (need 4 points).")
            return
        ok = cv2.imwrite(out_path, state["result"])
        print("Save path:", out_path)
        print("Saved OK" if ok else "Save FAILED")

    def on_mouse(event, x, y, flags, param):
        nonlocal vis
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
            points.append((x, y))
            cv2.circle(vis, (x, y), 6, (0, 0, 255), -1)
            cv2.imshow(win, vis)

            if len(points) == 4:
                result = draw_grid_and_labels(img, points, draw_grid=True, draw_labels=True)
                state["result"] = result
                cv2.imshow("labeled", result)
                save_result()

    cv2.setMouseCallback(win, on_mouse)

    while True:
        key = cv2.waitKey(10) & 0xFF
        if key == 27:  # ESC
            break
        if key in (ord("s"), ord("S")):
            save_result()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
