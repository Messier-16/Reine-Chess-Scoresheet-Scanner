import tensorflow as tf
import numpy as np
import cv2

# create an array where we can store our 4 pictures
images = np.zeros((4,784))
# and the correct values
correct_vals = np.zeros((4,10))

# we want to test our images which you saw at the top of this page
i = 0

def process(path):
    # read the image
    gray = cv2.imread(path, cv2.CV_LOAD_IMAGE_GRAYSCALE)

    # resize the images and invert it (black background)
    gray = cv2.resize(255-gray, (28, 28))

    # save the processed images
    cv2.imwrite("pic.png", gray)
    flatten = gray.flatten() / 255.0
    images[i] = flatten
    correct_val = np.zeros((10))
    correct_val[no] = 1
    correct_vals[i] = correct_val
    i += 1

