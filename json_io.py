#!flask/bin/python

from flask import Flask, render_template, request
import cv2 as cv
import base64
import numpy as np
from PIL import Image
import io

# save wherever you want
img_location = 'C:\\Users\\alexf\\desktop\\reine\\base64_test.png'


# go from base64 encoding to choice location
def string_to_saved_image_old(base64_string):
    split = base64_string.split(',', 1)
    byte_string = bytes(split[1], 'utf-8')
    with open(img_location, 'wb') as fh:
        fh.write(base64.decodebytes(byte_string))


def get_numpy(base64_string):
    split = base64_string.split(',', 1)
    byte_file = bytes(split[1], 'utf-8')
    file = base64.decodebytes(byte_file)

    # finding the dimensions
    im = Image.open(io.BytesIO(file))
    arr = np.array(im)[:, :, 0]
    w = 550
    h = 850
    return cv.resize(arr, (w, h))


app = Flask(__name__)


@app.route('/')
def output():
    # serve index template
    return render_template('index.html')


@app.route('/receiver', methods=['POST'])
def worker():
    # read json + reply
    data = request.get_json(force=True)
    numpy_img = get_numpy(data)
    return data


if __name__ == '__main__':
    # run!
    app.run()
