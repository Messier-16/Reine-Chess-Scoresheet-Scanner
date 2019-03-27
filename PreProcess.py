import cv2 as cv
import numpy as np
from scipy import ndimage


def pre_process(img):
    height, width = img.shape[:2]

    if height > width:
        # EMNIST was preprocessed based on NIST samples, which have 128x128 px.
        width = 128 * width // height
        height = 128
    else:
        height = 128 * height // width
        width = 128

    # Remove residual box borders.
    border_px_to_remove = 10
    img = cv.resize(img, (width + 2 * border_px_to_remove, height + 2 * border_px_to_remove))
    img = img[border_px_to_remove: border_px_to_remove + height, border_px_to_remove: border_px_to_remove + width]

    saturation_threshold = img.mean(axis=0).mean(axis=0) - 20
    _, img = cv.threshold(img, saturation_threshold, 255, cv.THRESH_BINARY)

    # Create square img while preserving aspect ratio.
    horizontal_border = (128 - width) // 2
    vertical_border = (128 - height) // 2
    img = cv.copyMakeBorder(img, top=vertical_border, bottom=vertical_border, left=horizontal_border,
                            right=horizontal_border, borderType=cv.BORDER_CONSTANT, value=[255, 255, 255])
    img = 255 - img

    if is_empty(img):
        box = (28, 28)
        img = cv.resize(img, box, interpolation=cv.INTER_CUBIC)
        return img

    blur_kernel = (7, 7)
    img = cv.GaussianBlur(img, blur_kernel, sigmaX=1, sigmaY=1)

    img = mass_center(img)

    while np.sum(img[0]) == 0 and np.sum(img[:, 0]) == 0 and np.sum(img[:, -1]) == 0 and np.sum(img[-1]) == 0:
        img = img[1: -1, 1: -1]

    # Stroke width normalization not in EMNIST but improves accuracy.
    stroke_width_normalization_scale_factor = 3
    img_size_threshold = 5
    side_length = img.shape[0]
    scaled_size = round(stroke_width_normalization_scale_factor * 128 / side_length)

    if scaled_size > img_size_threshold:
        kernel_size = scaled_size - img_size_threshold
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        img = cv.erode(img, kernel)
    elif scaled_size < img_size_threshold:
        kernel_size = img_size_threshold - scaled_size
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        img = cv.dilate(img, kernel)

    img = cv.resize(img, (27, 27))

    # EMNIST has 2 px but has a more consistent ROI size as it adapts NIST.
    row_padding = 1
    col_padding = 1

    img = cv.copyMakeBorder(img, top=col_padding, bottom=col_padding, left=row_padding,
                            right=row_padding, borderType=cv.BORDER_CONSTANT, value=[0, 0, 0])

    img = cv.resize(img, (28, 28), cv.INTER_CUBIC)
    return img


def is_empty(box):
    if box.mean(axis=0).mean(axis=0) < 3:
        return True
    return False


# As per EMNIST
def mass_center(img):
    shifts = get_shifts(img)
    img = shift(img, shifts)
    return img


def get_shifts(img):
    center_y, center_x = ndimage.measurements.center_of_mass(img)
    height, width = img.shape

    shift_x = np.round(width / 2.0 - center_x).astype(int)
    shift_y = np.round(height / 2.0 - center_y).astype(int)

    shifts = (shift_x, shift_y)
    return shifts


def shift(img, shifts):
    shift_x = shifts[0]
    shift_y = shifts[1]

    height, width = img.shape
    transformation_matrix = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
    shifted = cv.warpAffine(img, transformation_matrix, (width, height))

    return shifted
