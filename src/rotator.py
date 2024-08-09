import cv2
import numpy as np
from PIL import Image

from logger import logger


def is_horizontal(line):
    x1, y1, x2, y2 = line
    return True if abs(x1-x2) > abs(y1-y2) else False


def get_rotation_angle(image: np.array):
    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image

    low_threshold, high_threshold = 50, 150
    edges = cv2.Canny(gray, low_threshold, high_threshold)

    rho = 5  # distance resolution in pixels of the Hough grid
    theta = np.pi / 180  # angular resolution in radians of the Hough grid
    threshold = 450  # minimum number of votes (intersections in Hough grid cell)
    min_line_length = 100  # minimum number of pixels making up a line
    max_line_gap = 10  # maximum gap in pixels between connectable line segments

    # Run Hough on edge detected image
    # Output "lines" is an array containing endpoints of detected line segments
    lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
                            min_line_length, max_line_gap)

    no_lines_detected = False
    if lines is None:
        logger.print('no lines, threshhold -> 300')
        no_lines_detected = True
    else:
        hor_lines = []
        for line in lines:
            if is_horizontal(line[0]):
                hor_lines.append(line[0])
        if not hor_lines:
            logger.print('no horizontal lines, threshhold -> 300')
            no_lines_detected = True

    if no_lines_detected:
        threshold = 300
        lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
                                min_line_length, max_line_gap)
        if lines is None:
            logger.print('threshhold=300, no lines')
            return 0
        else:
            hor_lines = []
            for line in lines:
                if is_horizontal(line[0]):
                    hor_lines.append(line[0])
            if not hor_lines:
                logger.print('threshhold=300, no horizontal lines')
                return 0

    angles = []
    for line in hor_lines:
        x1,y1,x2,y2 = line
        dx, dy = x1-x2, y1-y2
        angles.append(np.arctan2(dx, dy)* 180 / np.pi)
    angle = (- 90 - np.median(angles))

    return angle


def rotate_image(image: np.array, angle, center=None, scale=1.0):
    (h, w) = image.shape[:2] # Получаем размеры изображения
    if center is None:
        center = (w / 2, h / 2)
    # Получаем матрицу преобразования для поворота
    M = cv2.getRotationMatrix2D(center, angle, scale)
    # Поворачиваем изображение
    rotated_image = cv2.warpAffine(image, M, (w, h))
    return rotated_image


def main(image: str | np.ndarray) -> np.ndarray:
    if isinstance(image, np.ndarray):
        pass
    elif isinstance(image, str):
        image = np.array(Image.open(image))

    angle = get_rotation_angle(image)
    rotated_image = rotate_image(image, angle)
    return rotated_image


# ----  -----  FOR DEBUG  -----  -------

#
# import cv2
# from PIL import Image
# import numpy as np
#
#
# def is_horizontal(line):
#     x1, y1, x2, y2 = line
#     return True if abs(x1-x2) > abs(y1-y2) else False
#
#
# def get_rotation_angle(image: np.array):
#     gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
#
#     low_threshold, high_threshold = 50, 150
#     edges = cv2.Canny(gray, low_threshold, high_threshold)
#
#     rho = 1  # distance resolution in pixels of the Hough grid
#     theta = np.pi / 180  # angular resolution in radians of the Hough grid
#     threshold = 300  # minimum number of votes (intersections in Hough grid cell)
#     min_line_length = 100  # minimum number of pixels making up a line
#     max_line_gap = 10  # maximum gap in pixels between connectable line segments
#     line_image = np.copy(cv2.cvtColor(image, cv2.COLOR_RGB2BGR)) * 0  # creating a blank to draw lines on
#
#     # Run Hough on edge detected image
#     # Output "lines" is an array containing endpoints of detected line segments
#     lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
#                             min_line_length, max_line_gap)
#     hor_lines = []
#     for line in lines:
#         if is_horizontal(line[0]):
#             hor_lines.append(line[0])
#         for x1,y1,x2,y2 in line: # draw all red lines
#             cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
#     for x1, y1, x2, y2 in hor_lines:  # draw horiz green lines
#         cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 5)
#
#     # Draw the lines on the  image
#     lines_edges = cv2.addWeighted(image, 0.8, line_image, 1, 0)
#
#     angles = []
#     for line in hor_lines:
#         x1,y1,x2,y2 = line
#         dx, dy = x1-x2, y1-y2
#         angles.append(np.arctan2(dx, dy)* 180 / np.pi)
#     angle = (- 90 - np.mean(angles))
#     print(angle)
#
#     return {'angle': angle, 'drawing': lines_edges}
#
#
# def rotate_image(image: np.array, angle, center=None, scale=1.0):
#     (h, w) = image.shape[:2] # Получаем размеры изображения
#     if center is None:
#         center = (w / 2, h / 2)
#     # Получаем матрицу преобразования для поворота
#     M = cv2.getRotationMatrix2D(center, angle, scale)
#     # Поворачиваем изображение
#     rotated_image = cv2.warpAffine(image, M, (w, h))
#     return rotated_image
#
#
# def main(img_path):
#     image = np.array(Image.open(img_path))
#     results = get_rotation_angle(image)
#     angle = results['angle']
#     drawing = results['drawing']
#     rotated_image = rotate_image(image, angle)
#     return rotated_image, drawing
