"""
This is invoked to start a production server.
"""
import sys

sys.path.append("/opt/python/current/app/infiltrate")
from infiltrate import application, setup_application


# from flask import Flask, render_template, request
#
# app = Flask(__name__)
#
#
# @app.route("/")
# def index():
#     return "Hello world..."
#
#
# if __name__ == "__main__":
#     app.run()
