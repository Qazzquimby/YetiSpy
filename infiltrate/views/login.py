"""This is where the routes are defined."""
import typing as t
import flask
import flask_login
from flask_classy import FlaskView
from werkzeug.security import generate_password_hash, check_password_hash
from infiltrate import db

import infiltrate.browsers as browsers
from infiltrate.models.user import User


class AuthenticationException(Exception):
    """The user isn't logged in."""

    pass


def ew_key_is_authentic(key: str) -> bool:
    name = get_username_from_key(key)
    return name is not None


class RegisterView(FlaskView):
    def index(self):
        return flask.render_template("register.html")

    def post(self):
        email = flask.request.form.get("email")
        ew_key = flask.request.form.get("ew_key")
        password = flask.request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            flask.flash("An account with that email address already exists.")
            return flask.redirect(flask.url_for("RegisterView:index"))

        name = get_username_from_key(ew_key)
        if name is None:
            flask.flash("Bad Eternal Warcry API key.")
            return flask.redirect(flask.url_for("RegisterView:index"))

        new_user = User(
            email=email,
            ew_key=ew_key,
            name=name,
            password=generate_password_hash(password, method="sha256"),
        )

        db.session.add(new_user)
        db.session.commit()

        redirect = flask.redirect("/login")
        return redirect


def get_username_from_key(key: str) -> t.Optional[str]:
    url = "https://api.eternalwarcry.com/v1/useraccounts/profile" + f"?key={key}"
    try:
        response = browsers.get_json_from_url(url)
        return response["username"]
    except (ConnectionError, KeyError):
        return None


# noinspection PyMethodMayBeStatic
class LoginView(FlaskView):
    """View for the list of card values"""

    def index(self):
        return flask.render_template("login.html")

    def post(self):
        email = flask.request.form.get("email")
        password = flask.request.form.get("password")
        remember = True if flask.request.form.get("remember") else False

        user = User.query.filter(User.email == email).first()

        if not user or not check_password_hash(user.password, password):
            flask.flash("Your username or password is incorrect.")
            return flask.redirect(flask.url_for("LoginView:index"))

        # if the above check passes, then we know the user has the right credentials
        flask_login.login_user(user, remember=remember)
        return flask.redirect("/")
