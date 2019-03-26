import cv2 as cv
import numpy as np


class Contour:
    def __init__(self, contour_data):
        self.x, self.y, self.width, self.height = cv.boundingRect(contour_data)
        return

    def get_precedence(self, row_and_column_classifiers):
        y_values_of_rows, horizontal_midpoint_x = row_and_column_classifiers
        x, y, width, height = self.x, self.y, self.width, self.height

        for row_y in y_values_of_rows:
            if row_y - height / 3 < y < row_y + height / 3:
                row_num = y_values_of_rows.index(row_y)
                break

        first_column = x + round(width / 2) < horizontal_midpoint_x  # Two columns: moves 1-25, and moves 26-50.
        if first_column:
            column = 0
        else:
            column = 1
        return column * 10000000 + row_num * 10000 + x


def box_extraction(img):
    # Crop ArUco markers out of image.
    height, width = img.shape[:2]

    y_start = int(height / 40)
    y_end = int(height * 39 / 40)

    x_start = int(width / 50)
    x_end = int(width * 49 / 50)

    img = img[y_start: y_end, x_start: x_end]

    extraction_template = cv.adaptiveThreshold(img, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, 2)
    extraction_template = 255 - extraction_template  # Invert the image

    kernel_length = np.array(img).shape[1] // 40
    vertical_kernel = cv.getStructuringElement(cv.MORPH_RECT, (1, kernel_length))
    horizontal_kernel = cv.getStructuringElement(cv.MORPH_RECT, (kernel_length, 1))

    vertical_template = cv.erode(extraction_template, vertical_kernel, iterations=3)
    vertical_lines = cv.dilate(vertical_template, vertical_kernel, iterations=3)

    horizontal_template = cv.erode(extraction_template, horizontal_kernel, iterations=3)
    horizontal_lines = cv.dilate(horizontal_template, horizontal_kernel, iterations=3)

    alpha = 0.5  # Weighting parameters for adding two images.
    beta = 1.0 - alpha
    kernel_3x3 = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))

    template_sum = cv.addWeighted(vertical_lines, alpha, horizontal_lines, beta, 0.0)
    template_sum = cv.erode(~template_sum, kernel_3x3, iterations=2)
    (thresh, template_sum) = cv.threshold(template_sum, 128, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)

    extraction_template = cv.morphologyEx(template_sum, cv.MORPH_OPEN, vertical_kernel)
    extraction_template = cv.morphologyEx(extraction_template, cv.MORPH_OPEN, horizontal_kernel)

    _, contours, hierarchy = cv.findContours(extraction_template, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for contour_index in range(len(contours)):
        contours[contour_index] = Contour(contours[contour_index])

    contours = filter_contours(contours)

    y_values_of_rows = get_row_y_values(contours)
    horizontal_midpoint_x = round(extraction_template.shape[1] / 2)
    row_and_column_classifiers = (y_values_of_rows, horizontal_midpoint_x)

    contours.sort(key=lambda contour: Contour.get_precedence(contour, row_and_column_classifiers))

    extracted_boxes = []
    for contour in contours:
        x, y, width, height = contour.x, contour.y, contour.width, contour.height
        extracted_boxes.append(img[y:y + height, x:x + width])
    return extracted_boxes


def filter_contours(contours):
    filtered_contours = []
    for contour in contours:
        x, y, width, height = contour.x, contour.y, contour.width, contour.height
        if 20 < width < 55 and 30 < height < 65 and width < height:  # Input image is 1100x1700 px.
            filtered_contours.append(contour)
    return filtered_contours


def get_row_y_values(contours):
    y_values = []

    for contour in contours:
        x, y, width, height = contour.x, contour.y, contour.width, contour.height
        new_row = True

        for row_y in y_values:
            same_row = y - height / 3 < row_y < y + height / 3
            if same_row:
                new_row = False
        if new_row:
            y_values.append(y)

    y_values.sort(key=lambda y_value: y_value)
    return y_values
