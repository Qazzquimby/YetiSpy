"""Handles creating the flask app"""
import functools

import boltons.fileutils
import flask
import flask_login
import flask_talisman
from flask import Flask
from flask_bootstrap import Bootstrap

from infiltrate.flask_jsglue import JSGlue
import logging

from infiltrate.setup import _set_config, _setup_db

# noinspection PyArgumentList
logging.basicConfig(handlers=[logging.StreamHandler()], level=logging.INFO)

application = Flask(__name__)
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
_set_config(application)
db = _setup_db(application)


@application.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


def one_time_setup():
    logging.info("Running one time setup")
    setup_application(application)
    updates()


def setup_application(app):
    flask_talisman.Talisman(app, content_security_policy=None)

    Bootstrap(app)
    JSGlue(app)
    boltons.fileutils.mkdir_p(app.instance_path)
    _register_views(app)
    _setup_login_manager(app)

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
        logging.info(f"Sitemap: {links}")
        return "See backend console log."

    @app.route("/logout")
    @flask_login.login_required
    def logout():
        flask_login.logout_user()
        return flask.redirect("/")


def _register_views(app):
    logging.info("Registering views")
    from infiltrate.views.card_values.cards_view import CardsView
    from infiltrate.views.update_api import UpdateAPI
    from infiltrate.views.login import LoginView, RegisterView
    from infiltrate.views.purchases_view import PurchasesView
    from infiltrate.views.update_collection import UpdateCollectionView
    from infiltrate.views.update_key import UpdateKeyView
    from infiltrate.views.faq import FaqView
    from infiltrate.views.raw_data import RawDataView

    CardsView.register(app)
    PurchasesView.register(app)
    LoginView.register(app)
    RegisterView.register(app)
    UpdateAPI.register(app)
    UpdateCollectionView.register(app)
    UpdateKeyView.register(app)
    FaqView.register(app)
    RawDataView.register(app)


def _setup_login_manager(app):
    logging.info("Setting up login manager")
    login_manager = flask_login.LoginManager()
    login_manager.login_view = "LoginView:index"
    login_manager.init_app(app)

    @login_manager.user_loader
    @functools.lru_cache(20)
    def load_user(user_id):
        logging.info(f"Loading user {user_id}")
        from infiltrate.models.user import User

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


one_time_setup()

if __name__ == "__main__":
    application.run()
