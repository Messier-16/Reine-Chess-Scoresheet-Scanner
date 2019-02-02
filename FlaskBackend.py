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
import Test


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
            cut_images = CutUp.box_extraction(final)
        except IndexError:
            return 'We couldn\'t detect all of the gridlines', 'error', ''

        processed_images = []
        for cut_image in cut_images:
            processed_images.append(Test.pre_process(cut_image, b=3, by_mass=False))

        for x in range(100):
            # for y in range(5):
                # function(5 * x + y + 1)
            break

        # for testing
        probabilities = [
            [  # 1
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # e
                [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # 4
            ],
            [
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # e
                [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # 5
            ],
            [  # 2
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # N
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # c
                [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # 3
            ],
            [
                [0.5, 0, 0, 0, 0, 0.5, 0.5, 0.5, 0, 0, 0, 0.5, 0.5, 0, 0, 0, 0, 0, 0, 0, 0.9, 0, 0, 0],  # N
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # f
                [0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # 6
            ],
            [  # 3
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0],  # d
                [0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # 4
            ],
            [
                [0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.9, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0],  # d
                [0, 0, 0, 0, 0, 0.9, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # 5
            ]
        ]

        return PostProcess.post_process(probabilities)

    # Return result
    message, game_res, moves = get_result(data)
    # message, game_res, moves = 'It worked', '*', data  # to be updated
    return message + 'delimiter' + game_res + 'delimiter' + moves


if __name__ == '__main__':
    # run!
    app.run()
