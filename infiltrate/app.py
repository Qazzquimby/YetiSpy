"""Handles creating the flask app"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


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


def create_app(test_config=None):
    """Creates and configures the flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )
    # noinspection PyTypeChecker
    db = _setup_db(app)
    _set_config(app, test_config)
    _make_instance_dir(app)
    _register_views(app)

    return app, db
