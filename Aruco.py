# Created by Alex Fung on 1/5/19!!

import time
import cv2 as cv
from cv2 import aruco
import numpy as np


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


# returns color img but can be modified to return gray by moving cv.cvtColor from find_markers to get_transform
def aruco_align(gray):
    try:
        return get_transform(gray, gray)  # fails if the ArUco markers aren't detected
    except IndexError:
        thresh = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 115, 0)
        return get_transform(gray, thresh)


# just for testing
start = time.time()
file = cv.imread('C:\\Users\\alexf\\Desktop\\reine\\scoresheet_samples\\IMG_1457.JPG', 0)
align = aruco_align(file)  # parameter is gray-scale image
try:
    final = cv.resize(align, (1100, 1700))
    cv.imwrite('C:\\Users\\alexf\\Desktop\\reine\\scoresheet_samples\\1457.png', final)
except IndexError:  # occurs when the corners are not found
    print('We couldn\'t detect the corners of your scoresheet. Make sure the black boxes are clearly visible!.')

end = time.time()
print('Time: ' + str(end - start) + ' s')
