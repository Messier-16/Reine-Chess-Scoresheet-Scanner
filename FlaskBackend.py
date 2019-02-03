from flask import Flask, render_template, request
import base64
import numpy as np
from PIL import Image
import io
import Aruco
import cv2 as cv
import CutUp
import PostProcess
import PreProcess

aligned = None
resized = None
processed_images = []
probabilities = []


# from base64 to numpy
def get_numpy(base64_string):
    split = base64_string.split(',', 1)
    byte_file = bytes(split[1], 'utf-8')
    file = base64.decodebytes(byte_file)

    # finding the dimensions
    im = Image.open(io.BytesIO(file))
    arr = np.array(im)[:, :, 0]
    return arr


app = Flask(__name__)


@app.route('/')
def output():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    global aligned
    data = request.get_json(force=True)

    try:
        numpy = get_numpy(data)
        aligned = Aruco.aruco_align(numpy)
        return 'success'
    except IndexError:
        return 'Image file is too small. Please upload at least 1100 x 1700 px.'


@app.route('/align', methods=['GET'])
def align():
    global resized

    try:
        resized = cv.resize(aligned, (1100, 1700))
        return 'success'
    except IndexError:
        return 'We couldn\'t detect the corners of your scoresheet. Make sure the black boxes are clearly ' \
               'visible!.'


@app.route('/preProcess', methods=['GET'])
def pre_process():
    global processed_images

    try:
        cut_images = CutUp.box_extraction(resized)
    except IndexError:
        return 'We couldn\'t detect all of the gridlines'

    for cut_image in cut_images:
        processed_images.append(PreProcess.pre_process(cut_image, b=3, by_mass=False, boundary=8))

    return 'success'


@app.route('/identify', methods=['GET'])
def identify():
    global probabilities

    for x in range(100):
        # for y in range(5):
        # function(5 * x + y + 1)
        break

    # for testing
    probabilities = [
        [  # 1
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # e
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 4
        ],
        [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # e
            [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 5
        ],
        [  # 2
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # N
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # c
            [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 3
        ],
        [
            [0.5, 0, 0, 0, 0, 0.5, 0.5, 0.5, 0, 0, 0, 0.5, 0.5, 0, 0, 0, 0, 0, 0, 0, 0.9, 0, 0, 0],  # N
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # f
            [0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 6
        ],
        [  # 3
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0],  # d
            [0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 4
        ],
        [
            [0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.9, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0],  # d
            [0, 0, 0, 0, 0, 0.9, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 5
        ]
    ]

    return 'success'


@app.route('/postProcess', methods=['GET'])
def post_process():
    message, game_res, moves = PostProcess.post_process(probabilities)
    return message + 'delimiter' + game_res + 'delimiter' + moves


if __name__ == '__main__':
    app.run()
