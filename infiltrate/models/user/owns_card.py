import typing as t

import pandas as pd

import models.card
import profiling
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
    def to_dataframe(cls, user: "models.user.User"):
        session = db.engine.raw_connection()
        query = f"""\
                SELECT *
                FROM user_owns_card
                WHERE user_id = {user.id}"""
        return pd.read_sql_query(query, session)


def create_is_owned_column(
    card_details: pd.DataFrame, user: "models.user.User"
) -> pd.DataFrame:
    raw_ownership = UserOwnsCard.to_dataframe(user)

    details_with_total_owned = (
        card_details.set_index(["set_num", "card_num"])
        .join(raw_ownership.set_index(["set_num", "card_num"]))
        .reset_index()
    )

    details_with_total_owned["is_owned"] = (
        details_with_total_owned["count_in_deck"] <= details_with_total_owned["count"]
    )
    del details_with_total_owned["count"]
    new_df = details_with_total_owned
    return new_df
