#!flask/bin/python

from flask import Flask, render_template, request
import base64

# save wherever you want
img_location = 'C:\\Users\\alexf\\desktop\\reine\\base64_test.png'


# go from base64 encoding to choice location
def string_to_saved_image(base64_string):
    split = base64_string.split(',', 1)
    byte_string = bytes(split[1], 'utf-8')
    with open(img_location, 'wb') as fh:
        fh.write(base64.decodebytes(byte_string))


app = Flask(__name__)


@app.route('/')
def output():
    # serve index template
    return render_template('index.html')


@app.route('/receiver', methods=['POST'])
def worker():
    # read json + reply
    data = request.get_json(force=True)
    string_to_saved_image(data)
    return data


if __name__ == '__main__':
    # run!
    app.run()
