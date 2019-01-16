# Created by Alex Fung on 1/5/19!!

import time
start = time.time()
import cv2 as cv
from cv2 import aruco
import numpy as np

# detect marker
def find_aruco(img):
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    # res[0] is the coordinates, res[1] is the marker ids
    res = aruco.detectMarkers(img, aruco_dict)
    return res


# finds the coordinates on the image that will become the edges of the transformed image (outermost marker corners)
def get_data(marker_pos, marker_id, aruco_res):
    # np.where() returns a tuple with two elem is only one column
    data_point = aruco_res[0][np.where(aruco_res[1] == [marker_id])[0][0]][0][marker_pos]
    return data_point


# from Adrian Rosebrock
def get_transform():
    rect = np.zeros((4, 2), 'float32')  # dtype = 'float32'
    for marker in range(4): rect[marker] = (
        get_data(marker, marker, find_aruco(input_img)))  # marker used twice because we use markers # 0, 1, 2, and 3
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
        [0, max_height - 1]], 'float32')  # dtype = "float32

    transform_mat = cv.getPerspectiveTransform(rect, dimensions)
    # gray b/c color is not needed for this program
    aligned_image = cv.warpPerspective(input_img, transform_mat, (max_width, max_height))
    return aligned_image


'''
# remove noise
def clean(img):
    # adaptive threshold changes threshold value based on surrounding pixels, binary to 0 or 255
    # 115 = block size to take the avg of, 5 = amt (out of 255) over avg a pixel must be to be considered black
    thresh_img = cv.adaptiveThreshold(img, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 115, 5)
    # kernel = np.ones((2, 2), np.uint8)
    # opened_img = cv.morphologyEx(thresh_img, cv.MORPH_OPEN, kernel)
    # closed_img = cv.morphologyEx(opened_img, cv.MORPH_CLOSE, kernel)
    # resized_image = cv.resize(aligned_image, (width, height))  # width, height are scoresheet-specific
    return thresh_img
'''


file = cv.imread("C:\\Users\\alexf\\Desktop\\reine\\scoresheet_samples\\IMG_1377.JPG")
# these values are scoresheet-specific, dim. are multiples of 11 x 17
width = 506 # 11 * 46
height = 770 # 17 * 46 - 12

input_img = cv.cvtColor(file, cv.COLOR_BGR2GRAY)

read = False
while not read:
    try:
        # fails if the ArUco markers aren't detected
        aligned_img = get_transform()
        read = True
    except IndexError:
        print("Please take another picture, align corners, and try not to have too much shadow")
        # write some code to ask them to take another pic and wait until they do


# big_img = cv.resize(aligned_img, (width * 2, height * 2))
# clean_img = clean(big_img)
right_size_img = cv.resize(aligned_img, (width, height))
ret, final_img = cv.threshold(right_size_img, 254, 255, cv.THRESH_BINARY)

# just for testing
cv.imshow('TransformedImage', final_img)
cv.imwrite("C:\\Users\\alexf\\Desktop\\reine\\scoresheet_samples\\1377.png", final_img)
end = time.time()
print(end - start)
cv.waitKey()
cv.destroyAllWindows()
