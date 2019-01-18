import cv2
import numpy as np
import time

start = time.time()


def get_contour_precedence(contour, row_y):
    # dependent on the fact that the contouring (besides sorting) is perfect
    x, y, w, h = cv2.boundingRect(contour)
    row_num = None
    for row in row_y:
        if row - h / 3 < y < row + h / 3:
            row_num = row_y.index(row)
    return 10000 * row_num + x


def sort_contours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index
    reverse = False
    i = 0

    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1

    # construct the list of bounding boxes and sort them from top to
    # bottom
    bounding_boxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, bounding_boxes),
                                        key=lambda b: b[1][i], reverse=reverse))

    # return the list of sorted contours and bounding boxes
    return cnts, bounding_boxes


def box_extraction(img_for_box_extraction_path, cropped_dir_path):
    img = cv2.imread(img_for_box_extraction_path, 0)  # Read the image
    # Thresholding the image
    img_bin = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 2)
    img_bin = 255 - img_bin  # Invert the image

    cv2.imwrite("Image_bin.jpg", img_bin)

    # Defining a kernel length
    kernel_length = np.array(img).shape[1] // 40

    # A vertical kernel of (1 X kernel_length), which will detect all the vertical lines from the image.
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
    # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
    hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
    # A kernel of (3 X 3) ones.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    # Morphological operation to detect vertical lines from an image
    img_temp1 = cv2.erode(img_bin, vertical_kernel, iterations=3)
    vertical_lines_img = cv2.dilate(img_temp1, vertical_kernel, iterations=3)
    # cv2.imwrite("vertical_lines.jpg", vertical_lines_img)

    # Morphological operation to detect horizontal lines from an image
    img_temp2 = cv2.erode(img_bin, hori_kernel, iterations=3)
    horizontal_lines_img = cv2.dilate(img_temp2, hori_kernel, iterations=3)
    # cv2.imwrite("horizontal_lines.jpg", horizontal_lines_img)

    # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
    alpha = 0.5
    beta = 1.0 - alpha
    # This function helps to add two image with specific weight parameter to get a third image as
    # summation of two image.
    img_final_bin = cv2.addWeighted(vertical_lines_img, alpha, horizontal_lines_img, beta, 0.0)
    img_final_bin = cv2.erode(~img_final_bin, kernel, iterations=2)
    (thresh, img_final_bin) = cv2.threshold(img_final_bin, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # For Debugging
    # Enable this line to see vertical and horizontal lines in the image which is used to find boxes
    cv2.imwrite("img_final_bin.jpg", img_final_bin)
    final = img-img_final_bin
    cv2.imwrite("final.jpg", final)

    # closing the lines
    vert_close = cv2.morphologyEx(img_final_bin, cv2.MORPH_OPEN, vertical_kernel)
    hori_close = cv2.morphologyEx(vert_close, cv2.MORPH_OPEN, hori_kernel)

    # Find contours for image, which will detect all the boxes
    im2, contours, hierarchy = cv2.findContours(
        hori_close, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Sort all the contours by top to bottom.
    # (contours, boundingBoxes) = sort_contours(contours, method="left-to-right")

    def get_true_contours(pre_contours):
        post_contours = []
        for pre_contour in pre_contours:
            the_x, the_y, the_w, the_h = cv2.boundingRect(pre_contour)
            if 70 < the_w < 120 and 80 < the_h < 140 and the_h > the_w * 1.05:
                post_contours.append(pre_contour)
        return post_contours

    def set_row_y(the_true_contours):
        the_row_y = []
        for contour in the_true_contours:
            the_x, the_y, the_w, the_h = cv2.boundingRect(contour)
            add = True
            for row in the_row_y:
                if the_y - the_h / 3 < row < the_y + the_h / 3:
                    add = False
            if add:
                the_row_y.append(the_y)
        the_row_y.sort(key=lambda value: value)
        return the_row_y

    true_contours = get_true_contours(contours)
    row_y = set_row_y(true_contours)

    # second output was originally img.shape[1]
    true_contours.sort(key=lambda the_contours: get_contour_precedence(the_contours, row_y))

    idx = 0
    for c in range(500):
        # Returns the location and width,height for every contour
        x, y, w, h = cv2.boundingRect(true_contours[c])

        # If the box height is greater then 20, width is >80, then only save it as a box in "cropped/" folder.
        # This was moved up to sorting algorithm
        idx += 1
        new_img = img[y:y + h, x:x + w]
        cv2.imwrite(cropped_dir_path + str(idx) + '.png', new_img)

        # For Debugging
        # Enable this line to see all contours.
        # cv2.drawContours(img, contours, -1, (0, 0, 255), 3)
        # cv2.imwrite("./Temp/img_contour.jpg", img)


box_extraction("C:\\Users\\alexf\\Desktop\\reine\\scoresheet_samples\\1388_pre.png",
               "C:\\Users\\alexf\\Desktop\\reine\\cropped_imgs\\")

end = time.time()
print('Time: ' + str(end - start) + ' s')
