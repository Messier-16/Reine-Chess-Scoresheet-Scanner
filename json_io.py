#!flask/bin/python

import sys

from flask import Flask, render_template, request, redirect, Response
import random
import json

app = Flask(__name__)


@app.route('/')
def output():
    # serve index template
    return render_template('index.html')


@app.route('/receiver', methods=['POST'])
def worker():
    # read json + reply
    data = request.get_json(force=True)

    return data


if __name__ == '__main__':
    # run!
    app.run()

'''
WITH OPENCV:

 import base64
 imgdata = base64.b64decode(imgstring) #I use imgdata as this variable itself in references below
 filename = 'some_image.jpg'
 with open(filename, 'wb') as f:
    f.write(imgdata)
'''