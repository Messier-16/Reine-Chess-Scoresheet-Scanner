import cv2 as cv
import numpy as np
import time
import PreProcess

start = time.time()


def get_contour_precedence(contour, row_y):
    # dependent on the fact that the contouring (besides sorting) is perfect
    x, y, w, h = cv.boundingRect(contour)
    row_num = None
    for row in row_y:
        if row - h / 3 < y < row + h / 3:
            row_num = row_y.index(row)
    return 10000 * row_num + x


def box_extraction(uncropped, cropped_dir_path):
    # cropping image
    h, w = uncropped.shape[:2]
    img = uncropped[int(0 + h / 40): int(h - h / 40), int(0 + w / 50): int(w - w / 50)]

    # Thresholding the image
    img_bin = cv.adaptiveThreshold(img, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, 2)
    img_bin = 255 - img_bin  # Invert the image

    cv.imwrite("Image_bin.jpg", img_bin)

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
    # cv.imwrite("vertical_lines.jpg", vertical_lines_img)

    # Morphological operation to detect horizontal lines from an image
    img_temp2 = cv.erode(img_bin, hori_kernel, iterations=3)
    horizontal_lines_img = cv.dilate(img_temp2, hori_kernel, iterations=3)
    # cv.imwrite("horizontal_lines.jpg", horizontal_lines_img)

    # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
    alpha = 0.5
    beta = 1.0 - alpha
    # This function helps to add two image with specific weight parameter to get a third image as
    # summation of two image.
    img_final_bin = cv.addWeighted(vertical_lines_img, alpha, horizontal_lines_img, beta, 0.0)
    img_final_bin = cv.erode(~img_final_bin, kernel, iterations=2)
    (thresh, img_final_bin) = cv.threshold(img_final_bin, 128, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)

    # For Debugging
    # Enable this line to see vertical and horizontal lines in the image which is used to find boxes
    cv.imwrite("img_final_bin.jpg", img_final_bin)
    final = img-img_final_bin
    cv.imwrite("final.jpg", final)

    # closing the lines
    vert_close = cv.morphologyEx(img_final_bin, cv.MORPH_OPEN, vertical_kernel)
    hori_close = cv.morphologyEx(vert_close, cv.MORPH_OPEN, hori_kernel)

    # Find contours for image, which will detect all the boxes
    im2, contours, hierarchy = cv.findContours(
        hori_close, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    def get_true_contours(pre_contours):
        post_contours = []
        for pre_contour in pre_contours:
            the_x, the_y, the_w, the_h = cv.boundingRect(pre_contour)
            if int(w / 36.6) < the_w < int(w / 15.7) and int(h / 34) < the_h < int(h / 18.9) and the_w * 1.05 < \
                    the_h < the_w * 2:
                post_contours.append(pre_contour)
        return post_contours

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
        the_row_y.sort(key=lambda value: value)
        return the_row_y
    true_contours = get_true_contours(contours)
    row_y = set_row_y(true_contours)

    # second output was originally img.shape[1]
    true_contours.sort(key=lambda the_contours: get_contour_precedence(the_contours, row_y))

    idx = 0
    for c in range(500):
        # which move num
        move = int(idx / 20) + 1
        if idx % 20 >= 10:
            move += 25

        # which player
        player = 1
        if idx % 10 >= 5:
            player = 2

        # which char in the move
        move_idx = idx % 5 + 1

        key = str(move) + '.' + str(player) + '.' + str(move_idx)

        # Returns the location and width,height for every contour
        x, y, w, h = cv.boundingRect(true_contours[c])

        new_img = img[y:y + h, x:x + w]
        cv.imwrite(cropped_dir_path + key + '.png', PreProcess.pre_process(new_img))

        idx += 1

        # For Debugging
        # Enable this line to see all contours.
        # cv.drawContours(img, contours, -1, (0, 0, 255), 3)
        # cv.imwrite("./Temp/img_contour.jpg", img)


# for testing
# parameter is gray-scale img
file = 'C:\\Users\\alexf\\Desktop\\reine\\scoresheet_samples\\1388.png'
numpy = cv.imread(file, 0)
box_extraction(numpy, 'C:\\Users\\alexf\\Desktop\\reine\\cropped_imgs\\')

end = time.time()
print('Time: ' + str(end - start) + ' s')
