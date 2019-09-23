"""Handles creating the flask app"""
import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
# sys.path.append(".")

application = Flask(__name__, instance_relative_config=True)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def _setup_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE']
    database = SQLAlchemy(app, session_options={
        'expire_on_commit': False  # Fixes DetachedInstanceError
    })
    return database


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
    from infiltrate.views.card_values import CardsView
    from infiltrate.views.update_api import UpdateAPI
    from infiltrate.views.login import LoginView
    from infiltrate.views.update_collection import UpdateCollectionView
    CardsView.register(app)
    LoginView.register(app)
    UpdateAPI.register(app)
    UpdateCollectionView.register(app)


def _schedule_updates():
    from infiltrate import scheduling
    return scheduling.schedule_updates()


def _update():
    from infiltrate import models
    models.update()


_set_config(application, test_config=None)
db = _setup_db(application)
Bootstrap(application)
_make_instance_dir(application)
_register_views(application)
_schedule_updates()


# _update()


@application.teardown_request
def teardown_request(exception):
    """Prevents bad db states by rolling back when the app closes."""
    if exception:
        db.session.rollback()
    db.session.remove()
