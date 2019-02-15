import cv2 as cv
import numpy as np
from scipy import ndimage


# we center images by center of mass, as this is what EMNIST creators did. This function carries out the shift
def shift(img, sx, sy):
    rows, cols = img.shape
    m = np.float32([[1, 0, sx], [0, 1, sy]])
    shifted = cv.warpAffine(img, m, (cols, rows))

    return shifted


# getting the shift values
def get_best_shift(img):
    cy, cx = ndimage.measurements.center_of_mass(img)

    rows, cols = img.shape
    shift_x = np.round(cols / 2.0 - cx).astype(int)
    shift_y = np.round(rows / 2.0 - cy).astype(int)

    return shift_x, shift_y


def pre_process(gray):
    # resize the images and invert it (black background)
    h, w = gray.shape[:2]
    # resizing to 128 like EMNIST
    width = 2 * int(128 * w / (2 * h))

    # 'c' is number of pixels that will be cut off from the sides of the image, as we do not want overlapping lines
    c = 10
    resize = cv.resize(gray, (width + c * 2, 128 + c * 2))

    # to remove possible borders
    crop = resize[c: c + 128, c: c + width]

    threshold = crop.mean(axis=0).mean(axis=0) - 20
    ret, thresh = cv.threshold(crop, threshold, 255, cv.THRESH_BINARY)
    # vertical is set to 128 px and we have to increase/decrease horizontal to maintain proportionality
    horizontal_border = int((128 - width) / 2)
    # add side borders to meet the 28x28 requirement
    box = cv.copyMakeBorder(thresh, top=0, bottom=0, left=horizontal_border, right=horizontal_border,
                            borderType=cv.BORDER_CONSTANT, value=[255, 255, 255])

    # if the mean pixel value > 252 we assume there is no character written in the box
    if box.mean(axis=0).mean(axis=0) > 252:
        final = cv.resize(255 - box, (28, 28), interpolation=cv.INTER_CUBIC)
        return np.reshape(final, (1, 784))  # we iterate through all 500 images later

    b = 7  # size of the blur kernel
    invert = cv.GaussianBlur(255 - box, (b, b), sigmaX=1, sigmaY=1)

    # as defined above
    shift_x, shift_y = get_best_shift(invert)
    shifted = shift(invert, shift_x, shift_y)

    # remove 1px-wide "rings" of whitespace on edges of image, preserving shift
    while np.sum(shifted[0]) == 0 and np.sum(shifted[:, 0]) == 0 and np.sum(shifted[:, -1]) == 0 and \
            np.sum(shifted[-1]) == 0:
        shifted = shifted[1: -1, 1: -1]

    # this was not done in EMNIST but improves accuracy. Normalizes stroke width by eroding small images which
    # are scaled up a lot and dilating large images which have not been magnified
    e = 5  # scale factor for erosion
    boundary = 8

    scale = round(e * 128 / shifted.shape[0])  # width and length the same so we can use shape[0]

    if scale > boundary:  # if the image is large
        k = scale - boundary
        kernel = np.ones((k, k), np.uint8)
        no_pad = cv.erode(shifted, kernel)
    elif scale < boundary:  # if the image is small
        k = boundary - scale
        kernel = np.ones((k, k), np.uint8)
        no_pad = cv.dilate(shifted, kernel)
    else:
        no_pad = shifted

    # as per EMNIST
    row_padding = 2
    col_padding = 2

    square = cv.copyMakeBorder(no_pad, top=col_padding, bottom=col_padding, left=row_padding,
                               right=row_padding, borderType=cv.BORDER_CONSTANT, value=[0, 0, 0])

    final = cv.resize(square, (28, 28), cv.INTER_CUBIC)
    return np.reshape(final, (1, 784))
