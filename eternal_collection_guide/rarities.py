from dataclasses import dataclass

COMMON = "common"
UNCOMMON = "uncommon"
RARE = "rare"
LEGENDARY = "legendary"
PROMO = "promo"
RARITIES = [COMMON, UNCOMMON, RARE, LEGENDARY, PROMO]
rarity_string_to_id = {COMMON: 2,
                       UNCOMMON: 3,
                       RARE: 4,
                       LEGENDARY: 5,
                       PROMO: 6}


@dataclass(frozen=True)
class Rarity:
    id: str
    name: str
