"""Card Rarities"""
import typing as t

from infiltrate import db


# todo this doesnt need to be a table im pretty sure


class Rarity(db.Model):
    """A table representing rarities in Eternal.

    Drop rates and crafting costs correspond to rarity."""

    __tablename__ = "rarities"
    name = db.Column("Name", db.String(length=9), primary_key=True)
    num_in_pack = db.Column("NumInPack", db.Float, nullable=False)
    enchant = db.Column("Enchant", db.Integer, nullable=False)
    disenchant = db.Column("Disenchant", db.Integer, nullable=False)
    foil_enchant = db.Column("FoilEnchant", db.Integer, nullable=False)
    foil_disenchant = db.Column("FoilDisenchant", db.Integer, nullable=False)

    @property
    def drop_chance(self):
        """The number of cards of a given rarity that will drop in a pack.

        Integers are assured numbers. A float is a chance that the drop will appear.
        All numbers are correct for long term average."""
        return self.num_in_pack / sum([r.num_in_pack for r in RARITIES])

    def __repr__(self):
        return f"<Rarity {self.name}>"


COMMON = Rarity(
    name="Common",
    num_in_pack=8,
    enchant=50,
    disenchant=1,
    foil_enchant=800,
    foil_disenchant=25,
)
UNCOMMON = Rarity(
    name="Uncommon",
    num_in_pack=3,
    enchant=100,
    disenchant=10,
    foil_enchant=1600,
    foil_disenchant=50,
)
PROMO = Rarity(
    name="Promo",
    num_in_pack=0,
    enchant=600,
    disenchant=100,
    foil_enchant=2400,
    foil_disenchant=400,
)
RARE = Rarity(
    name="Rare",
    num_in_pack=0.9,
    enchant=800,
    disenchant=200,
    foil_enchant=3200,
    foil_disenchant=800,
)
LEGENDARY = Rarity(
    name="Legendary",
    num_in_pack=0.1,
    enchant=3200,
    disenchant=800,
    foil_enchant=9600,
    foil_disenchant=3200,
)
RARITIES: t.List[Rarity] = [COMMON, UNCOMMON, RARE, LEGENDARY, PROMO]

rarity_from_name = {r.name: r for r in RARITIES}


def create_rarities():
    for rarity in RARITIES:
        db.session.merge(rarity)
    db.session.commit()


create_rarities()
