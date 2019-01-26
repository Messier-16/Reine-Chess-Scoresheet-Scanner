from flask import Flask, render_template, request
import base64
import numpy as np
from PIL import Image
import io


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
    numpy_img = get_numpy(data)
    message, game_res, moves = 'It worked', '*', data  # to be updated
    return message + 'delimiter' + game_res + 'delimiter' + moves


if __name__ == '__main__':
    # run!
    app.run()
