import models.card
from infiltrate import db


class UserOwnsCard(db.Model):
    """Table representing card playset ownership."""
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('users.id'), primary_key=True)
    set_num = db.Column('set_num', db.Integer, primary_key=True)
    card_num = db.Column('card_num', db.Integer, primary_key=True)
    count = db.Column('count', db.Integer, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint((set_num, card_num), [models.card.Card.set_num,
                                                                    models.card.Card.card_num]), {})
