"""This is where the routes are defined."""
from __future__ import annotations

import json
import typing

import flask
import requests
from flask_classy import FlaskView
from werkzeug.exceptions import BadRequestKeyError

from infiltrate import models, db, cookies


# TODO change key field to password type so that it can be queried by

class BadKeyException(Exception):
    """The given key is not recognized by Eternal Warcry"""
    pass


class AuthenticationException(Exception):
    """The user isn't logged in."""
    pass


def get_sign_up():
    try:
        return flask.request.form['signup'] == 'on'
    except BadRequestKeyError:
        return False


def get_remember_me():
    try:
        return flask.request.form['remember'] == 'on'
    except BadRequestKeyError:
        return False


def get_username(key: str):
    try:
        username = get_username_from_key(key)
        return username
    except BadKeyException as e:
        raise e


def get_username_from_key(key: str):
    url = "https://api.eternalwarcry.com/v1/useraccounts/profile" + \
          f"?key={key}"
    response = requests.get(url)
    if response.status_code == 500:
        raise BadKeyException
    response_json = json.loads(response.text)
    username = response_json["username"]
    return username


def get_user_id(username: str, key: str) -> int:
    user = get_user_id_if_exists(username, key)
    if not user:
        user = make_new_user(username, key)
    user_id = user.id
    return user_id


def get_user_id_if_exists(username: str, key: str) -> typing.Optional[models.user.User]:
    existing_users_with_username = models.user.User.query.filter_by(name=username).all()
    matching_users = [user for user in existing_users_with_username if user.key == key]
    assert len(matching_users) in (0, 1)
    if matching_users:
        return matching_users[0]
    else:
        return None


def make_new_user(user_name: str, key: str):
    new_user = models.user.User(name=user_name, key=key)
    db.session.merge(new_user)
    db.session.commit()
    return get_user_id_if_exists(user_name, key)


def login(response, user_id: int, username: str, remember_me: bool):
    # import datetime
    # response.set_cookie(name, value, expires=)

    if remember_me:
        max_age = 60 * 60 * 24 * 365
    else:
        max_age = None

    response.set_cookie(cookies.ID, str(user_id), max_age=max_age)
    response.set_cookie(cookies.USERNAME, username, max_age=max_age)


# noinspection PyMethodMayBeStatic
class LoginView(FlaskView):
    """View for the list of card values"""

    def index(self):
        # import datetime
        # response.set_cookie(name, value, expires=datetime.datetime.now() + datetime.timedelta(days=30))

        return flask.render_template('login.html')

    def post(self):
        key = flask.request.form['key']
        # given_username = flask.request.form['username']
        sign_up = get_sign_up()
        remember_me = get_remember_me()

        username = get_username(key)
        # if username_for_key != given_username:
        #     print("bad")

        user_id = get_user_id(username, key)

        response = flask.redirect('/')
        login(response, user_id=user_id, username=username, remember_me=remember_me)

        return response


"""
set_cookie(key, value='', max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False, samesite=None)
Sets a cookie. The parameters are the same as in the cookie Morsel object in the Python standard library but it accepts unicode data, too.

A warning is raised if the size of the cookie header exceeds max_cookie_size, but the header will still be set.

Parameters
key – the key (name) of the cookie to be set.

value – the value of the cookie.

max_age – should be a number of seconds, or None (default) if the cookie should last only as long as the client’s browser session.

expires – should be a datetime object or UNIX timestamp.

path – limits the cookie to a given path, per default it will span the whole domain.

domain – if you want to set a cross-domain cookie. For example, domain=".example.com" will set a cookie that is readable by the domain www.example.com, foo.example.com etc. Otherwise, a cookie will only be readable by the domain that set it.

secure – If True, the cookie will only be available via HTTPS

httponly – disallow JavaScript to access the cookie. This is an extension to the cookie standard and probably not supported by all browsers.

samesite – Limits the scope of the cookie such that it will only be attached to requests if those requests are “same-site”.
"""
