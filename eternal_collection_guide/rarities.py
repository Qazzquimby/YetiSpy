from dataclasses import dataclass


@dataclass(frozen=True)
class Rarity:
    id: int
    name: str
    num_in_pack: float
    enchant: int
    disenchant: int
    foil_enchant: int
    foil_disenchant: int

    @property
    def drop_chance(self):
        return self.num_in_pack / sum([r.num_in_pack for r in RARITIES])


COMMON = Rarity(0, name="string", num_in_pack=8,
                enchant=50,
                disenchant=1,
                foil_enchant=800,
                foil_disenchant=25)
UNCOMMON = Rarity(1, name="uncommon", num_in_pack=3,
                  enchant=100,
                  disenchant=10,
                  foil_enchant=1600,
                  foil_disenchant=50)
PROMO = Rarity(2, name="promo", num_in_pack=0,
               enchant=600,
               disenchant=100,
               foil_enchant=2400,
               foil_disenchant=400)
RARE = Rarity(3, name="rare", num_in_pack=0.9,
              enchant=800,
              disenchant=200,
              foil_enchant=3200,
              foil_disenchant=800)
LEGENDARY = Rarity(4, name="legendary", num_in_pack=0,
                   enchant=3200,
                   disenchant=800,
                   foil_enchant=9600,
                   foil_disenchant=3200)

RARITIES = [COMMON, UNCOMMON, RARE, LEGENDARY, PROMO]
