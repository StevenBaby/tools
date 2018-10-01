#!/usr/bin/python

import os
import glob
import traceback
import datetime
import dandan

from flask import Flask
from flask import abort
from flask import send_file
from flask import send_from_directory
from flask import render_template
from werkzeug.routing import BaseConverter

import config

__VERSION__ = "0.0.1.1"


dirname = os.path.dirname(os.path.abspath(__file__))
favicon = os.path.join(dirname, "static/images/favicon.ico")

class RegexConverter(BaseConverter):
    def __init__(self, map, *args):
        self.map = map
        self.regex = args[0]


server = Flask(__name__)
server.url_map.converters['regex'] = RegexConverter


def get_data():
    data = dandan.value.AttrDict()
    data.info.name = "Files"
    data.info.current_time = datetime.datetime.now()
    return data

def get_info(filepath):
    
    info = dandan.value.AttrDict()
    info.filepath = filepath
    info.basename = os.path.basename(filepath)
    info.size = os.path.getsize(filepath)
    info.mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
    if os.path.isfile(filepath):
        info.type = "file"
    elif os.path.isdir(filepath):
        info.type = 'dir'
    return info

def get_response(filename=""):
    basket = os.path.join(dirname, "basket")
    if not os.path.exists(basket):
        return "basket not exists."
        # abort(404)
    
    filepath = os.path.join(basket, filename)
    if not os.path.exists(filepath):
        return "file not exists {}".format(filepath)
        # abort(404)

    if os.path.isfile(filepath):
        return send_file(filepath)

    children = os.listdir(filepath)

    data = get_data()
    data.filename = filename
    if filename:
        data.title = '/{}/'.format(filename)
    else:
        data.title = "/"
    data.items = [get_info(os.path.join(filepath, child)) for child in children]
    return render_template("index.html", **data)


@server.route('/')
@server.route("/<regex('.+'):filename>")
def index(filename=""):
    if filename == "favicon.ico" and os.path.exists(favicon):
        return send_file(favicon)
    else:
        return get_response(filename)


def main():
    try:
        print("run server {}:{}".format(config.host, config.port))
        server.run(host=config.host, port=config.port, debug=config.debug, threaded=True)
    except Exception:
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
