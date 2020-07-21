import typing as t

import pandas as pd

import models.card
from infiltrate import db

if t.TYPE_CHECKING:
    import models.user


class UserOwnsCard(db.Model):
    """Table representing card playset ownership."""

    user_id = db.Column(
        "user_id", db.Integer(), db.ForeignKey("users.id"), primary_key=True
    )
    set_num = db.Column("set_num", db.Integer, primary_key=True)
    card_num = db.Column("card_num", db.Integer, primary_key=True)
    count = db.Column("count", db.Integer, nullable=False)
    __table_args__ = (
        db.ForeignKeyConstraint(
            (set_num, card_num), [models.card.Card.set_num, models.card.Card.card_num]
        ),
        {},
    )

    @classmethod
    def dataframe_for_user(cls, user: "models.user.User"):
        session = db.engine.raw_connection()
        query = f"""\
                SELECT *
                FROM user_owns_card
                WHERE user_id = {user.id}"""
        return pd.read_sql_query(query, session)


def create_is_owned_series(
    card_details: pd.DataFrame, ownership: pd.DataFrame
) -> pd.Series:
    """Makes a series matching the card copies in card_details for if that many copies
    are owned."""
    full_ownership = pd.concat(
        [ownership.assign(count_in_deck=i) for i in range(1, 5)], axis=0
    ).set_index(["set_num", "card_num", "count_in_deck"])

    details_with_total_owned = card_details.join(full_ownership)

    ownership_frame = details_with_total_owned[["set_num", "card_num", "count_in_deck"]]

    # noinspection PyTypeChecker
    is_owned = (
        details_with_total_owned["count_in_deck"] <= details_with_total_owned["count"]
    )
    ownership_frame.loc[:, "is_owned"] = is_owned
    return ownership_frame
