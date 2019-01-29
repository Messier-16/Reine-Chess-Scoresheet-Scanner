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
    shift_x = np.round(cols / 2.0 - cx).astype(int)
    shift_y = np.round(rows / 2.0 - cy).astype(int)

    return shift_x, shift_y


def pre_process(gray):
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
    if box.mean(axis=0).mean(axis=0) > 252:
        return 255 - box

    invert = 255 - box
    while np.sum(invert[0]) == 0:
        invert = invert[1:]

    while np.sum(invert[:, 0]) == 0:
        invert = np.delete(invert, 0, 1)

    while np.sum(invert[-1]) == 0:
        invert = invert[:-1]

    while np.sum(invert[:, -1]) == 0:
        invert = np.delete(invert, -1, 1)

    rows, cols = invert.shape

    if rows > cols:
        factor = 20 / rows
        rows = 20
        cols = int(round(cols * factor))
        new_box = cv.resize(invert, (cols, rows))
    else:

        factor = 20 / cols
        cols = 20
        rows = int(round(rows * factor))
        new_box = cv.resize(invert, (cols, rows))

    cols_padding = (int(math.ceil((28 - cols) / 2.0)), int(math.floor((28 - cols) / 2.0)))
    rows_padding = (int(math.ceil((28 - rows) / 2.0)), int(math.floor((28 - rows) / 2.0)))
    padded = np.lib.pad(new_box, (rows_padding, cols_padding), 'constant')

    shift_x, shift_y = get_best_shift(padded)
    return shift(padded, shift_x, shift_y)


# for testing only
for move in range(50):
    for player in range(2):
        for move_idx in range(5):
            path = 'C:/Users/alexf/Desktop/reine/cropped_imgs/'
            path += str(move + 1) + '.' + str(player + 1) + '.' + str(move_idx + 1) + '.png'
            final = pre_process(cv.imread(path, 0))
            cv.imwrite(path, final)
