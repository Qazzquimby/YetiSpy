"""This is where the routes are defined."""
from __future__ import annotations

import flask
from flask_classy import FlaskView


# noinspection PyMethodMayBeStatic
class LoginView(FlaskView):
    """View for the list of card values"""

    def index(self):
        # import datetime
        # response.set_cookie(name, value, expires=datetime.datetime.now() + datetime.timedelta(days=30))

        return flask.render_template('login.html')

    def post(self):
        key = flask.request.form['key']


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
