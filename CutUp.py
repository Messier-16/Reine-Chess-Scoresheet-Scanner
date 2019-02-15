import cv2 as cv
import numpy as np


# sort the contours from left to right, top to bottom (left column before right column)
def get_contour_precedence(contour, row_y, half):
    # completely dependent on the fact that the contouring (besides sorting) is perfect
    x, y, w, h = cv.boundingRect(contour)
    row_num = None
    for row in row_y:
        if row - h / 3 < y < row + h / 3:
            row_num = row_y.index(row)

    # the boxes in the second half of the page will all be sorted after the first half
    if x + round(w / 2) < half:
        return 10000 * (row_num + 1) + x
    else:
        return 1000000 * (row_num + 1) + x


def box_extraction(uncropped):
    # cropping image so we don't get the aruco markers as contours
    h, w = uncropped.shape[:2]
    img = uncropped[int(0 + h / 40): int(h - h / 40), int(0 + w / 50): int(w - w / 50)]

    # Thresholding the image
    img_bin = cv.adaptiveThreshold(img, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, 2)
    img_bin = 255 - img_bin  # Invert the image

    # Defining a kernel length
    kernel_length = np.array(img).shape[1] // 40

    # A vertical kernel of (1 X kernel_length), which will detect all the vertical lines from the image.
    vertical_kernel = cv.getStructuringElement(cv.MORPH_RECT, (1, kernel_length))
    # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
    hori_kernel = cv.getStructuringElement(cv.MORPH_RECT, (kernel_length, 1))
    # A kernel of (3 X 3) ones.
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))

    # Morphological operation to detect vertical lines from an image
    img_temp1 = cv.erode(img_bin, vertical_kernel, iterations=3)
    vertical_lines_img = cv.dilate(img_temp1, vertical_kernel, iterations=3)

    # Morphological operation to detect horizontal lines from an image
    img_temp2 = cv.erode(img_bin, hori_kernel, iterations=3)
    horizontal_lines_img = cv.dilate(img_temp2, hori_kernel, iterations=3)

    # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
    alpha = 0.5
    beta = 1.0 - alpha
    # This function helps to add two image with specific weight parameter to get a third image as
    # summation of two image.
    img_final_bin = cv.addWeighted(vertical_lines_img, alpha, horizontal_lines_img, beta, 0.0)
    img_final_bin = cv.erode(~img_final_bin, kernel, iterations=2)
    (thresh, img_final_bin) = cv.threshold(img_final_bin, 128, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)

    # closing the lines so all contours are detected
    vert_close = cv.morphologyEx(img_final_bin, cv.MORPH_OPEN, vertical_kernel)
    hori_close = cv.morphologyEx(vert_close, cv.MORPH_OPEN, hori_kernel)

    # Find contours for image, which will detect all the boxes
    im2, contours, hierarchy = cv.findContours(
        hori_close, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    half = round(hori_close.shape[1] / 2)

    # only contours of about the size of one box, etc. not the whole scoresheet
    def get_true_contours(pre_contours):
        post_contours = []
        for pre_contour in pre_contours:
            the_x, the_y, the_w, the_h = cv.boundingRect(pre_contour)
            if 20 < the_w < 55 and 30 < the_h < 65 and the_w < the_h:  # scoresheet-specific but we resize so all good
                post_contours.append(pre_contour)
        return post_contours

    # finding the general positions of each row (25 moves therefore 25 rows) so we can sort contours top to bottom
    # x value will be used to sort left to right
    def set_row_y(the_true_contours):
        the_row_y = []
        for contour in the_true_contours:
            the_x, the_y, the_w, the_h = cv.boundingRect(contour)
            add = True
            for row in the_row_y:
                if the_y - the_h / 3 < row < the_y + the_h / 3:
                    add = False
            if add:
                the_row_y.append(the_y)
        the_row_y.sort(key=lambda value: value)  # sorting the rows based on y value
        return the_row_y
    true_contours = get_true_contours(contours)
    row_y = set_row_y(true_contours)

    # second output was originally img.shape[1]
    true_contours.sort(key=lambda the_contours: get_contour_precedence(the_contours, row_y, half))

    cut_images = []
    for c in range(500):
        # Returns the location and width,height for every contour
        x, y, w, h = cv.boundingRect(true_contours[c])

        # from contours to 500 numpy arrays (50 moves, 5 max chars/move, 2 players/move)
        cut_images.append(img[y:y + h, x:x + w])

    return cut_images
