import cv2
import numpy as np


def order_points(pts: np.ndarray) -> np.ndarray:

    rect = np.zeros((4, 2), dtype=np.float32)

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # tl
    rect[2] = pts[np.argmax(s)]   # br

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # tr
    rect[3] = pts[np.argmax(diff)]  # bl

    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxW = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxH = int(max(heightA, heightB))

    maxW = max(maxW, 1)
    maxH = max(maxH, 1)

    dst = np.array([
        [0, 0],
        [maxW - 1, 0],
        [maxW - 1, maxH - 1],
        [0, maxH - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxW, maxH))


def find_board_quad(img_bgr: np.ndarray, debug: bool = True) -> np.ndarray | None:

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)


    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # 自适应阈值：对木纹/光照不均更稳
    th = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31, 5
    )


    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)


    th = cv2.dilate(th, np.ones((3, 3), np.uint8), iterations=1)


    contours, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        if debug:
            cv2.imshow("debug_threshold", th)
        return None

    h, w = gray.shape[:2]
    img_area = float(h * w)

    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    best = None
    for cnt in contours[:50]:
        area = cv2.contourArea(cnt)


        if area < img_area * 0.10:
            break

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        if not cv2.isContourConvex(approx):
            continue

        pts = approx.reshape(4, 2).astype(np.float32)


        rect = cv2.minAreaRect(approx)
        (rw, rh) = rect[1]
        if rw <= 1 or rh <= 1:
            continue
        aspect = max(rw, rh) / min(rw, rh)
        if aspect > 1.8:
            continue

        best = pts
        break

    if debug:
        dbg = img_bgr.copy()
        if best is not None:
            cv2.polylines(dbg, [best.astype(int)], True, (0, 0, 255), 3)
        cv2.imshow("debug_threshold", th)
        cv2.imshow("debug_contour", dbg)

    return best


def detect_and_transform_chessboard(image_path: str, debug: bool = True):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Unable to read image file: {image_path}")
        return

    original = img.copy()


    scale = 0.5
    small = cv2.resize(original, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    quad_small = find_board_quad(small, debug=debug)
    if quad_small is None:
        print("Unable to perform perspective transformation: No valid chessboard corners detected")
        if debug:
            cv2.imshow("original", original)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return

    quad_orig = quad_small / scale

    warped = four_point_transform(original, quad_orig)


    show = original.copy()
    cv2.polylines(show, [quad_orig.astype(int)], True, (0, 0, 255), 4)

    cv2.namedWindow("yuantu", cv2.WINDOW_NORMAL)
    cv2.imshow("yuantu", show)

    cv2.namedWindow("zhentu", cv2.WINDOW_NORMAL)
    cv2.imshow("zhentu", warped)

    cv2.imwrite("detected_chessboard.png", show)
    cv2.imwrite("transformed_chessboard.png", warped)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_and_transform_chessboard("11.jpg", debug=True)
