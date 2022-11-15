import logging
import os

from flask_sqlalchemy import SQLAlchemy


def _set_config(app):
    logging.info("Setting configuration")
    variables = [
        "SECRET_KEY",
        "WARCRY_KEY",
        "UPDATE_KEY",
        "ENV",
        "DATABASE_URL",
    ]
    for var in variables:
        value = os.environ.get(var)
        if value is None:
            raise ValueError(f"{var} missing from environment.")
        app.config[var] = value


def _setup_db(app):
    logging.info("Setting up database")
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["DATABASE_URL"]
    database = SQLAlchemy(
        app, session_options={"expire_on_commit": False}  # Fixes DetachedInstanceError
    )
    return database
