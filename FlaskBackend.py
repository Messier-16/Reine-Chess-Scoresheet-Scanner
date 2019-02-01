from flask import Flask, render_template, request
import base64
import numpy as np
from PIL import Image
import io
import Aruco
import cv2 as cv
import CutUp
import PostProcess
import modelrun

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
    # serve index template
    return render_template('index.html')


@app.route('/receiver', methods=['POST'])
def worker():
    # read json + reply
    data = request.get_json(force=True)

    def get_result(the_data):
        try:
            numpy = get_numpy(the_data)
        except IndexError:
            return 'Image file is too small. Please upload at least 1100 x 1700 px.', 'error', ''

        try:
            align = Aruco.aruco_align(numpy)
        except IndexError:  # occurs when the corners are not found
            return 'We couldn\'t detect the corners of your scoresheet. Make sure the black boxes are clearly ' \
                   'visible!.', 'error', ''
        try:
            final = cv.resize(align, (1100, 1700))
            # parameters and outputs of box_extraction still need to be changed   
            CutUp.box_extraction(final)
            return PostProcess.post_process(the_moves, the_confs)
        except IndexError and TypeError:  # occurs when not enough contours are found, TypeError is just for testing
            return 'We couldn\'t read your handwriting! Make sure the grid-lines are clearly visible.', 'error', ''

    # Return result
    message, game_res, moves = get_result(data)
    # message, game_res, moves = 'It worked', '*', data  # to be updated
    return message + 'delimiter' + game_res + 'delimiter' + moves


if __name__ == '__main__':
    # run!
    app.run()
