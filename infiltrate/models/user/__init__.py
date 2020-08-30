"""User account objects"""

import sqlalchemy_utils
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
import infiltrate.models.user.collection as collection
from infiltrate import application, db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """Model representing a user."""

    __tablename__ = "users"
    id = db.Column("id", db.Integer(), primary_key=True, autoincrement=True)
    email = db.Column("email", db.String(), unique=True)
    name = db.Column("name", db.String(length=40))
    ew_key = db.Column(
        "ew_key",
        sqlalchemy_utils.EncryptedType(
            db.String(50), application.config["SECRET_KEY"], FernetEngine
        ),
    )
    password = db.Column("password", db.String())


def get_by_id(user_id: int):
    user = User.query.filter_by(id=str(user_id)).first()
    return user
