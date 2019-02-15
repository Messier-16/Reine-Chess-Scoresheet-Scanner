import cv2 as cv
from cv2 import aruco  # from opencv-contrib-python
import numpy as np


def shadow_remover(img):
    rgb_planes = cv.split(img)

    result_planes = []
    result_norm_planes = []
    for plane in rgb_planes:
        dilated_img = cv.dilate(plane, np.ones((7, 7), np.uint8))
        bg_img = cv.medianBlur(dilated_img, 21)
        diff_img = 255 - cv.absdiff(plane,
        norm_img = cv.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv.NORM_MINMAX, dtype=cv.CV_8UC1)
        _, thr_img = cv.threshold(norm_img, 230, 0, cv.THRESH_TRUNC)
        cv.normalize(thr_img, thr_img, al bg_img)
        # norm_img = diff_imgpha=0, beta=255, norm_type=cv.NORM_MINMAX, dtype=cv.CV_8UC1)
        result_planes.append(diff_img)
        result_norm_planes.append(norm_img)

    # result = cv.merge(result_planes)
    result_norm = cv.merge(result_norm_planes)

    return result_norm


# detect marker
def find_markers(img):
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    # res[0] is the coordinates, res[1] is the marker ids
    res = aruco.detectMarkers(img, aruco_dict)
    return res


# finds the coordinates on the image that will become the edges of the transformed image (outermost marker corners)
def get_data(marker_pos, marker_id, aruco_res):
    # np.where() returns a tuple with two elem is only one column
    data_point = aruco_res[0][np.where(aruco_res[1] == [marker_id])[0][0]][0][marker_pos]
    return data_point


def get_transform(numpy, marker_numpy):
    rect = np.zeros((4, 2), dtype='float32')
    for marker in range(4):
        # marker used twice because we use markers # 0, 1, 2, and 3
        rect[marker] = (get_data(marker, marker, find_markers(marker_numpy)))
    # top-left, top-right, bottom-right, bottom-left
    (tl, tr, br, bl) = rect

    # width of new image = max distance between br/bl and tr/tl
    width_1 = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_2 = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_1), int(width_2))

    # height, same calculation
    height_1 = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_2 = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_1), int(height_2))

    dimensions = np.array([
        [0, 0],
        [max_width - 1, 0],  # minus one to make sure it all fits
        [max_width - 1, max_height - 1],
        [0, max_height - 1]], dtype='float32')

    transform_mat = cv.getPerspectiveTransform(rect, dimensions)
    aligned_image = cv.warpPerspective(numpy, transform_mat, (max_width, max_height))
    return aligned_image


# input/output are each a grayscale numpy array
def aruco_align(gray):
    try:
        align = get_transform(gray, gray)  # fails if the ArUco markers aren't detected
    except IndexError:
        # thresholded image may be easier to find markers on
        thresh = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 115, 0)
        align = get_transform(gray, thresh)
    resize = cv.resize(align, (1100, 1700))  # it may be better to resize the image as the first step of the program
    no_shadow = shadow_remover(resize)

    return no_shadow
