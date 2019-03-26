import cv2 as cv
from cv2 import aruco  # opencv-contrib-python
import numpy as np


def aruco_align(gray):
    try:
        aligned_img = get_transform(gray, gray)  # Fails when ArUco markers not detected.
    except IndexError:
        # Thresholded image may be easier to detect markers on.
        thresholded_img = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 115, 0)
        aligned_img = get_transform(gray, thresholded_img)
    resize = cv.resize(aligned_img, (1100, 1700))
    no_shadow = shadow_remover(resize)
    return no_shadow


def get_transform(img, template_to_detect_markers):
    bounding_rectangle = np.zeros((4, 2), dtype='float32')
    detected_coordinates_and_ids = detect_markers(template_to_detect_markers)

    for marker in range(4):  # 4 markers on Reine scoresheet.
        search_position = marker  # Which of marker's 4 corners, clockwise starting from top-left.
        search_id = marker
        search_position_and_id = (search_position, search_id)

        corner_coordinate = get_coordinate(search_position_and_id, detected_coordinates_and_ids)
        bounding_rectangle[marker] = corner_coordinate

    (top_left, top_right, bottom_right, bottom_left) = bounding_rectangle

    width_bottom = np.sqrt(((bottom_right[0] - bottom_left[0]) ** 2) + ((bottom_right[1] - bottom_left[1]) ** 2))
    width_top = np.sqrt(((top_right[0] - top_left[0]) ** 2) + ((top_right[1] - top_left[1]) ** 2))
    max_width = int(max(width_bottom, width_top))

    height_right = np.sqrt(((top_right[0] - bottom_right[0]) ** 2) + ((top_right[1] - bottom_right[1]) ** 2))
    height_left = np.sqrt(((top_left[0] - bottom_left[0]) ** 2) + ((top_left[1] - bottom_left[1]) ** 2))
    max_height = int(max(height_right, height_left))

    transform_dimensions = np.array([
        [0, 0],
        [max_width, 0],
        [max_width, max_height],
        [0, max_height]
    ], dtype='float32')

    transform_matrix = cv.getPerspectiveTransform(bounding_rectangle, transform_dimensions)
    img = cv.warpPerspective(img, transform_matrix, (max_width, max_height))
    return img


def detect_markers(img):
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    detected_coordinates_and_ids = aruco.detectMarkers(img, aruco_dict)
    return detected_coordinates_and_ids


def get_coordinate(search_coordinates_and_ids, detected_coordinates_and_ids):
    search_position = search_coordinates_and_ids[0]
    search_id = search_coordinates_and_ids[1]

    detected_coordinates = detected_coordinates_and_ids[0]
    detected_ids = detected_coordinates_and_ids[1]

    search_marker = detected_coordinates[np.where(detected_ids == [search_id])[0][0]]
    coordinate = search_marker[0][search_position]
    return coordinate


def shadow_remover(img):
    grayscale_plane = cv.split(img)[0]
    dilated_img = cv.dilate(grayscale_plane, np.ones((7, 7), np.uint8))
    bg_img = cv.medianBlur(dilated_img, 21)
    diff_img = 255 - cv.absdiff(grayscale_plane, bg_img)
    normalized_img = cv.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv.NORM_MINMAX, dtype=cv.CV_8UC1)
    return normalized_img
