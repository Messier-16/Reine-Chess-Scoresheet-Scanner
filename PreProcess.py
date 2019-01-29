import cv2 as cv
import numpy as np
import math
from scipy import ndimage


def shift(img, sx, sy):
    rows, cols = img.shape
    m = np.float32([[1, 0, sx], [0, 1, sy]])
    shifted = cv.warpAffine(img, m, (cols, rows))
    return shifted


def get_best_shift(img):
    cy, cx = ndimage.measurements.center_of_mass(img)

    rows, cols = img.shape
    shift_x = np.round(cols/2.0-cx).astype(int)
    shift_y = np.round(rows/2.0-cy).astype(int)

    return shift_x, shift_y


def pre_process(img):
    images = np.zeros((1, 784))
    # and the correct values
    correct_vals = np.zeros((1, 10))

    # we want to test our images which you saw at the top of this page
    i = 0

    # read the image
    gray = cv.imread(img, cv.cv2.IMREAD_GRAYSCALE)

    # resize the images and invert it (black background)
    h, w = gray.shape[:2]
    width = 2 * int(28 * w / (2 * h))
    c = 1
    resize = cv.resize(gray, (width + c * 2, 28 + c * 2))

    # to remove possible borders
    crop = resize[c: c + 28, c: c + width]

    # threshold before adding whitespace
    threshold = crop.mean(axis=0).mean(axis=0) - 20
    ret, thresh = cv.threshold(crop, threshold, 255, cv.THRESH_BINARY)
    horizontal_border = int((28 - width) / 2)
    # add side borders to meet the 28x28 requirement
    box = cv.copyMakeBorder(thresh, top=0, bottom=0, left=horizontal_border, right=horizontal_border,
                             borderType=cv.BORDER_CONSTANT, value=[255, 255, 255])

    # save the processed images
    cv.imwrite('edited.png', box)
    invert = cv.resize(255 - box, (width, 28))

    try:
        gray = invert.copy()
        while np.sum(gray[0]) == 0:
            gray = gray[1:]

        while np.sum(gray[:, 0]) == 0:
            gray = np.delete(gray, 0, 1)

        while np.sum(gray[-1]) == 0:
            gray = gray[:-1]

        while np.sum(gray[:, -1]) == 0:
            gray = np.delete(gray, -1, 1)

        rows, cols = gray.shape

        if rows > cols:
            factor = 20.0 / rows
            rows = 20
            cols = int(round(cols * factor))
            gray = cv.resize(gray, (cols, rows))
        else:

            factor = 20.0 / cols
            cols = 20
            rows = int(round(rows * factor))
            gray = cv.resize(gray, (cols, rows))

        cols_padding = (int(math.ceil((28 - cols) / 2.0)), int(math.floor((28 - cols) / 2.0)))
        rows_padding = (int(math.ceil((28 - rows) / 2.0)), int(math.floor((28 - rows) / 2.0)))
        gray = np.lib.pad(gray, (rows_padding, cols_padding), 'constant')

        shift_x, shift_y = get_best_shift(gray)
        shifted = shift(gray, shift_x, shift_y)
        gray = shifted
        return gray / 255
    except IndexError:
        return box


# for testing only
final = pre_process('C:/Users/alexf/Desktop/reine/cropped_imgs/11.png')
cv.imwrite('C:/Users/alexf/ReineProjects/RithwikTest/test.png', final * 255)
cv.imshow('win', final)

cv.waitKey()
cv.destroyAllWindows()
