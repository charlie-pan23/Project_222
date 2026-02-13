import os
import cv2
import numpy as np


NORM_SIZE = 96
MIN_FG_RATIO = 0.03
CANNY1, CANNY2 = 60, 160
MATCH_METHOD = cv2.TM_CCOEFF_NORMED
TOPK = 3



def script_dir():
    """Return directory of this script"""
    return os.path.dirname(os.path.abspath(__file__))


def center_crop(img, pad_ratio=0.12):
    """Safe center crop"""
    h, w = img.shape[:2]
    pad = int(min(h, w) * pad_ratio)
    pad = max(0, min(pad, (min(h, w) // 2) - 1))

    if pad <= 0:
        return img.copy()

    return img[pad:h - pad, pad:w - pad].copy()


def segment_foreground(square_bgr):
    """
    Input: square BGR image
    Output: mask (0/255), foreground ratio
    """
    roi = center_crop(square_bgr, 0.12)

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    th = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        5
    )

    kernel = np.ones((3, 3), np.uint8)

    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)

    fg_ratio = float(np.count_nonzero(th)) / th.size

    return th, fg_ratio


def shape_descriptor(square_bgr):
    """
    square -> mask -> edges -> resize
    Return: descriptor, fg_ratio
    """
    mask, fg_ratio = segment_foreground(square_bgr)

    if fg_ratio < MIN_FG_RATIO:
        return None, fg_ratio

    edges = cv2.Canny(mask, CANNY1, CANNY2)

    edges = cv2.dilate(
        edges,
        np.ones((3, 3), np.uint8),
        iterations=1
    )

    desc = cv2.resize(
        edges,
        (NORM_SIZE, NORM_SIZE),
        interpolation=cv2.INTER_AREA
    )

    return desc, fg_ratio


def load_templates(template_root="/templates"):
    """
    Load template library
    Return: dict[label] = [desc1, desc2, ...]
    """
    root = os.path.join(script_dir(), template_root)

    if not os.path.isdir(root):
        raise FileNotFoundError(f"Template directory not found: {root}")

    db = {}

    for label in sorted(os.listdir(root)):

        folder = os.path.join(root, label)

        if not os.path.isdir(folder):
            continue

        descs = []

        for fn in sorted(os.listdir(folder)):

            if not fn.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                continue

            path = os.path.join(folder, fn)

            img = cv2.imread(path)

            if img is None:
                print("[WARN] Cannot read:", path)
                continue

            desc, _ = shape_descriptor(img)

            if desc is not None:
                descs.append(desc)

        if descs:
            db[label] = descs

    if not db:
        raise RuntimeError("No valid templates loaded")

    return db


def match_score(query_desc, template_desc):
    """Template matching score"""
    res = cv2.matchTemplate(query_desc, template_desc, MATCH_METHOD)
    return float(res[0, 0])


class PieceRecognizer:

    def __init__(self, template_root="templates"):
        self.db = load_templates(template_root)

    def classify_square(self, square_bgr):
        """
        Input: square BGR image
        Output: (label, confidence, fg_ratio)
        """
        if square_bgr is None:
            raise ValueError("Input image is None")

        qdesc, fg_ratio = shape_descriptor(square_bgr)

        if qdesc is None:
            return None, 0.0, fg_ratio

        best_label = None
        best_score = -1e9

        for label, tdescs in self.db.items():

            scores = []

            for td in tdescs:

                if td.shape != qdesc.shape:
                    td = cv2.resize(
                        td,
                        (qdesc.shape[1], qdesc.shape[0]),
                        interpolation=cv2.INTER_AREA
                    )

                scores.append(match_score(qdesc, td))

            scores.sort(reverse=True)

            score = float(np.mean(scores[:min(TOPK, len(scores))]))

            if score > best_score:
                best_score = score
                best_label = label

        return best_label, best_score, fg_ratio


def read_test_image(path):
    """
    Read image using script directory if relative path
    """
    if not os.path.isabs(path):
        path = os.path.join(script_dir(), path)

    img = cv2.imread(path)

    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")

    return img


# ---------- Added: saving helper ----------
def save_one_square(square_bgr, out_name="one_square.png"):
    """Save one square image into script directory"""
    out_path = os.path.join(script_dir(), out_name)
    ok = cv2.imwrite(out_path, square_bgr)
    if not ok:
        raise RuntimeError(f"Failed to write image: {out_path}")
    print("Saved:", out_path)
    return out_path


# (Optional) If you do not already have split_board elsewhere, you can use this:
def split_board(warped_bgr):
    """Split a top-down board image into an 8x8 list of square BGR images."""
    h, w = warped_bgr.shape[:2]
    step_y = h // 8
    step_x = w // 8
    squares = []
    for r in range(8):
        row = []
        for c in range(8):
            y1, y2 = r * step_y, (r + 1) * step_y
            x1, x2 = c * step_x, (c + 1) * step_x
            row.append(warped_bgr[y1:y2, x1:x2].copy())
        squares.append(row)
    return squares


# ================== Main Test ==================

if __name__ == "__main__":

    print("Script dir:", script_dir())
    print("Working dir:", os.getcwd())

    recognizer = PieceRecognizer("templates")

    # ---- Option A: If you already have squares from your pipeline, do this there ----
    # squares = split_board(warped)
    # save_one_square(squares[0][0], "one_square.png")

    # ---- Option B: If you only want to test this file, load a test image and also save it ----
    test_img = read_test_image("one_square.png")

    # Save a copy (useful to confirm paths)
    save_one_square(test_img, "one_square_copy.png")

    label, conf, fg = recognizer.classify_square(test_img)

    print("Result:", label)
    print("Confidence:", conf)
    print("Foreground ratio:", fg)
