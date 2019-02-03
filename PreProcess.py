import cv2 as cv
import numpy as np
from scipy import ndimage
from CutUp import box_extraction


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


def pre_process(gray, b, by_mass, boundary):
    # resize the images and invert it (black background)
    h, w = gray.shape[:2]
    width = 2 * int(128 * w / (2 * h))

    c = 10
    resize = cv.resize(gray, (width + c * 2, 128 + c * 2))

    # to remove possible borders
    crop = resize[c: c + 128, c: c + width]

    # threshold before adding whitespace
    threshold = crop.mean(axis=0).mean(axis=0) - 20
    ret, thresh = cv.threshold(crop, threshold, 255, cv.THRESH_BINARY)
    horizontal_border = int((128 - width) / 2)
    # add side borders to meet the 28x28 requirement
    box = cv.copyMakeBorder(thresh, top=0, bottom=0, left=horizontal_border, right=horizontal_border,
                            borderType=cv.BORDER_CONSTANT, value=[255, 255, 255])

    # if there is no character we return a box with value < 3
    if box.mean(axis=0).mean(axis=0) > 252:
        final = cv.resize(255 - box, (28, 28), interpolation=cv.INTER_CUBIC)
        return np.reshape(final, (1, 784))

    invert = cv.GaussianBlur(255 - box, (b, b), sigmaX=1, sigmaY=1)

    if by_mass:
        shift_x, shift_y = get_best_shift(invert)
        shifted = shift(invert, shift_x, shift_y)

        while np.sum(shifted[0]) == 0 and np.sum(shifted[:, 0]) == 0 and np.sum(shifted[:, -1]) == 0 and \
                np.sum(shifted[-1]) == 0:
            shifted = shifted[1: -1, 1: -1]

        e = 5  # scale factor for erosion
        # the smaller the region of interest, the more we erode the image to provide uniform, readable stroke width
        scale = round(e * 128 / shifted.shape[0])  # width and length the same
        if scale > boundary:
            k = scale - boundary
            kernel = np.ones((k, k), np.uint8)
            no_pad = cv.erode(shifted, kernel)
        elif scale < boundary:
            k = boundary - scale
            kernel = np.ones((k, k), np.uint8)
            no_pad = cv.dilate(shifted, kernel)
        else:
            no_pad = shifted

        row_padding = 2
        col_padding = 2

    else:
        while np.sum(invert[0]) == 0:
            invert = invert[1:]

        while np.sum(invert[:, 0]) == 0:
            invert = np.delete(invert, 0, 1)

        while np.sum(invert[-1]) == 0:
            invert = invert[:-1]

        while np.sum(invert[:, -1]) == 0:
            invert = np.delete(invert, -1, 1)

        e = 5  # scale factor for erosion
        # erode/dilate based on size to provide uniform, readable stroke width
        scale = round(e * min(128 / invert.shape[0], 128 / invert.shape[1]))
        if scale > boundary:
            k = scale - boundary
            kernel = np.ones((k, k), np.uint8)
            no_pad = cv.erode(invert, kernel)
        elif scale < boundary:
            k = boundary - scale
            kernel = np.ones((k, k), np.uint8)
            no_pad = cv.dilate(invert, kernel)
        else:
            no_pad = invert

        cols, rows = no_pad.shape

        if rows > cols:
            row_padding = 2
            col_padding = round((rows - cols) / 2) + 2

        else:  # cols > rows
            row_padding = round((cols - rows) / 2) + 2
            col_padding = 2

    square = cv.copyMakeBorder(no_pad, top=col_padding, bottom=col_padding, left=row_padding,
                               right=row_padding, borderType=cv.BORDER_CONSTANT, value=[0, 0, 0])

    final = cv.resize(square, (28, 28), cv.INTER_CUBIC)
    return np.reshape(final, (1, 784))


# b is Gaussian Blur kernel size
blur = 5
by_mass = True
bound = 8

if by_mass:
    method = 'mass'
else:
    method = 'fixed'

file = 'C:\\Users\\alexf\\Desktop\\reine\\scoresheet_samples\\1388.png'
numpy = cv.imread(file, 0)
cut_imgs = box_extraction(numpy)

for a in range(500):
    cv.imwrite('C:/Users/alexf/desktop/reine/cropped_imgs/' + str(a) + '_gaussian' + str(blur) + '_center' + method
               + '_bound' + str(bound) + '.png', pre_process(cut_imgs[a], b=blur, by_mass=by_mass, boundary=bound))
