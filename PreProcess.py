import cv2 as cv
import numpy as np


def pre_process(gray):
    # resize the images and invert it (black background)
    scale = 3  # helps conserve pixels for higher resolution at end, 3 seems to have no diff. compared to 4
    h, w = gray.shape[:2]
    width = 2 * int(28 * scale * w / (2 * h))

    c = 2 * scale
    resize = cv.resize(gray, (width + c * 2, 28 * scale + c * 2))

    # to remove possible borders
    crop = resize[c: c + 28 * scale, c: c + width]

    # threshold before adding whitespace
    threshold = crop.mean(axis=0).mean(axis=0) - 20
    ret, thresh = cv.threshold(crop, threshold, 255, cv.THRESH_BINARY)
    horizontal_border = int((28 * scale - width) / 2)
    # add side borders to meet the 28x28 requirement
    box = cv.copyMakeBorder(thresh, top=0, bottom=0, left=horizontal_border, right=horizontal_border,
                            borderType=cv.BORDER_CONSTANT, value=[255, 255, 255])
    if box.mean(axis=0).mean(axis=0) > 252:
        return cv.resize(255 - box, (28, 28))

    invert = 255 - box
    while np.sum(invert[0]) == 0:
        invert = invert[1:]

    while np.sum(invert[:, 0]) == 0:
        invert = np.delete(invert, 0, 1)

    while np.sum(invert[-1]) == 0:
        invert = invert[:-1]

    while np.sum(invert[:, -1]) == 0:
        invert = np.delete(invert, -1, 1)

    cols, rows = invert.shape
    padding = 1  # one pixel minimum padding around each char
    if rows > cols:
        x = 28 - 2 * padding
        y = 2 * round(((28 * cols / rows) - 2 * padding) / 2)
        right_size = cv.resize(invert, (x, y))
        row_padding = padding
        col_padding = int((28 - right_size.shape[0]) / 2)

    else:  # cols > rows
        x = 2 * round(((28 * rows / cols) - 2 * padding) / 2)
        y = 28 - 2 * padding
        right_size = cv.resize(invert, (x, y))
        row_padding = int((28 - right_size.shape[1]) / 2)
        col_padding = padding

    return cv.copyMakeBorder(right_size, top=col_padding, bottom=col_padding, left=row_padding, right=row_padding,
                             borderType=cv.BORDER_CONSTANT, value=[0, 0, 0])


'''
# for testing only
for move in range(50):
    for player in range(2):
        for move_idx in range(5):
            path = 'C:/Users/alexf/Desktop/reine/cropped_imgs/'
            path += str(move + 1) + '.' + str(player + 1) + '.' + str(move_idx + 1) + '.png'
            final = pre_process(cv.imread(path, 0))
            cv.imwrite(path, final)
'''
