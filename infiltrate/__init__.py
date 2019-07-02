"""Handles creating the flask app"""
import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(SECRET_KEY='dev')


def _setup_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Q1a1zz22@localhost/infiltrate'
    return SQLAlchemy(app)


def _set_config(app, test_config):
    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_pyfile('config.py', silent=True)


def _make_instance_dir(app):
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


def _register_views(app):
    from infiltrate.views import CardsView
    CardsView.register(app)


def _schedule_updates():
    from infiltrate import scheduling
    return scheduling.schedule_updates


db = _setup_db(app)
Bootstrap(app)
_set_config(app, test_config=None)
_make_instance_dir(app)
_register_views(app)
_schedule_updates()


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
    db.session.remove()
