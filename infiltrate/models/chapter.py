import logging

from infiltrate import db, browsers
from infiltrate.models.card import get_card_ids_from_names, Card


class Chapter(db.Model):
    """Table representing a monthly set of promo cards."""

    __tablename = "chapters"
    chapter_number = db.Column("chapter_number", db.Integer, primary_key=True)
    name = db.Column("name", db.String(length=80))


class ChapterHasCard(db.Model):
    __tablename__ = "chapter_has_cards"
    chapter_number = db.Column(
        "chapter_number", db.Integer, db.ForeignKey(Chapter.chapter_number)
    )
    set_num = db.Column("set_num", db.Integer, primary_key=True)
    card_num = db.Column("card_num", db.Integer, primary_key=True)
    __table_args__ = (
        db.ForeignKeyConstraint(
            [set_num, card_num], [Card.set_num, Card.card_num], ondelete="CASCADE"
        ),
        {},
    )


def update():
    logging.info("Updating chapters")

    root_url = "https://eternalcardgame.fandom.com/wiki/Chapters"
    selector = "#mw-content-text > div > table > tbody > tr"
    chapter_rows = browsers.get_elements_from_url_and_selector(root_url, selector)
    row_dicts = []
    for row in chapter_rows:
        children = list(row.children)
        chapter_number_parts = children[1].text.split("Chapter ")
        if len(chapter_number_parts) < 2:
            continue
        chapter_number = int(chapter_number_parts[1])
        if chapter_number < 64:
            continue  # These chapters don't have purchases

        card_names = children[7].text.strip().split("\n")

        row_dict = {
            "chapter_number": chapter_number,
            "name": children[3].text,
            "card_names": card_names,
        }
        row_dicts.append(row_dict)

    for row_dict in row_dicts:
        cards = get_card_ids_from_names(names=row_dict["card_names"])
        chapter = Chapter(
            chapter_number=row_dict["chapter_number"], name=row_dict["name"]
        )
        db.session.merge(chapter)
        for card in cards:
            chapter_has_card = ChapterHasCard(
                chapter_number=chapter.chapter_number,
                set_num=card.set_num,
                card_num=card.card_num,
            )
            db.session.merge(chapter_has_card)
        db.session.commit()


def get_chapters():
    return Chapter.query.all()
