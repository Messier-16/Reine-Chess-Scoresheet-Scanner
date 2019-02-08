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
import Identify

numpy = None
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
    global numpy
    data = request.get_json(force=True)

    try:
        numpy = get_numpy(data)

        return 'success'
    except IndexError:
        return 'Couldn\'t read image file. Please upload a PNG or JPG of at least 550 x 850 px.'


@app.route('/align', methods=['GET'])
def align():
    global numpy, resized

    try:
        aligned = Aruco.aruco_align(numpy)
        numpy = None
        resized = cv.resize(aligned, (1100, 1700))
        return 'success'
    except IndexError:
        return 'Couldn\'t detect corners. Make sure the black boxes are clearly visible!'


@app.route('/preProcess', methods=['GET'])
def pre_process():
    global resized, processed_images

    try:
        cut_images = CutUp.box_extraction(resized)
        resized = None
    except IndexError:
        resized = None
        return 'We couldn\'t detect all of the gridlines.'

    for cut_image in cut_images:
        processed_images.append(PreProcess.pre_process(cut_image, b=7, by_mass=False, boundary=8))

    return 'success'


@app.route('/identify', methods=['GET'])
def identify():
    global processed_images, probabilities
    probabilities = Identify.process(processed_images)
    processed_images = []

    return probabilities


@app.route('/postProcess', methods=['GET'])
def post_process():
    global probabilities
    message, game_res, moves = PostProcess.post_process(probabilities)
    probabilities = []
    return message + 'delimiter' + game_res + 'delimiter' + moves


if __name__ == '__main__':
    app.run()
