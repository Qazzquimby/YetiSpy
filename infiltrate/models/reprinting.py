"""Models for cards being reprinted in new sets."""
import collections
import logging
import typing as t

import infiltrate.browsers as browsers
import infiltrate.caches as caches
import infiltrate.dwd_news as dwd_news
import infiltrate.models.card as card

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    String,
    Table,
    text,
    Text as TextType,
    VARCHAR,
    Integer,
    DateTime,
    Numeric,
    JSON,
)

from infiltrate.db_access import db


class Reprinting(db.Model):
    """A table matching card ids and the set numbers they are reprinted in"""

    card_id = db.Column(ForeignKey("card.id"), primary_key=True)
    set_num = db.Column(ForeignKey("set.id"), primary_key=True)
