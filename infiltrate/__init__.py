"""Handles creating the flask app"""
import flask
import flask_login
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

import boltons.fileutils

application = Flask(__name__, instance_relative_config=True)
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def _set_config(app, test_config):
    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_pyfile("config.py", silent=True)


_set_config(application, test_config=None)


def _setup_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["DATABASE"]
    database = SQLAlchemy(
        app, session_options={"expire_on_commit": False}  # Fixes DetachedInstanceError
    )
    return database


db = _setup_db(application)


def setup_application(app):
    Bootstrap(app)
    boltons.fileutils.mkdir_p(app.instance_path)
    updates()
    _register_views(app)
    _setup_login_manager(app)


def _register_views(app):
    from infiltrate.views.card_values.cards_view import CardsView
    from infiltrate.views.update_api import UpdateAPI
    from infiltrate.views.login import LoginView, RegisterView
    from infiltrate.views.purchases_view import PurchasesView
    from infiltrate.views.update_collection import UpdateCollectionView
    from infiltrate.views.faq import FaqView

    CardsView.register(app)
    PurchasesView.register(app)
    LoginView.register(app)
    RegisterView.register(app)
    UpdateAPI.register(app)
    UpdateCollectionView.register(app)
    FaqView.register(app)

    # Temporary dev page to see all routes
    @app.route("/site_map")
    def site_map():
        def has_no_empty_params(rule):
            defaults = rule.defaults if rule.defaults is not None else ()
            arguments = rule.arguments if rule.arguments is not None else ()
            return len(defaults) >= len(arguments)

        links = []
        for rule in app.url_map.iter_rules():
            # Filter out rules we can't navigate to in a browser
            # and rules that require parameters
            if "GET" in rule.methods and has_no_empty_params(rule):
                url = flask.url_for(rule.endpoint, **(rule.defaults or {}))
                links.append((url, rule.endpoint))
        print(links)
        return "See backend console log."

    @app.route("/logout")
    @flask_login.login_required
    def logout():
        flask_login.logout_user()
        return flask.redirect("/")


def _setup_login_manager(app):
    login_manager = flask_login.LoginManager()
    login_manager.login_view = "LoginView:index"
    login_manager.init_app(app)

    from infiltrate.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.filter(User.id == user_id).first()


def updates():
    import infiltrate.scheduling as scheduling

    scheduling.initial_update()
    scheduling.schedule_updates()


@application.teardown_request
def teardown_request(exception):
    """Prevents bad db states by rolling back when the app closes."""
    if exception:
        db.session.rollback()
    db.session.remove()
