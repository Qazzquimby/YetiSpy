"""This is where the routes are defined."""
import flask
from flask_classy import FlaskView


class FaqView(FlaskView):
    def index(self):
        return flask.render_template("faq.html")
