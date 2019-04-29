from unittest import TestCase

from eternal_collection_guide.base_learner import CollectionContent
from eternal_collection_guide.card import CardCollection, Card


class CollectionContentStub(CollectionContent):
    pass


class TestCardCollection(TestCase):
    def test_get_cards_in_set__when_set_is_0__throws_ValueError(self):
        sut = CardCollection()

        with self.assertRaises(ValueError):
            sut.get_cards_in_set(0)

    def test_get_cards_in_set__when_set_is_1__gets_cards_in_0_and_1(self):
        sut = CardCollection()

        [sut.append(Card(name=f"test_card_{set_num}", card_num=0, set_num=set_num, rarity="common"))
         for set_num in range(2)]

        result = sut.get_cards_in_set(1)

        self.assertEqual(2, len(result))

    def test_get_cards_in_set__when_set_is_2plus__gets_cards_in_set(self):
        sut = CardCollection()

        set_num = 3
        num_cards_in_set = 5

        [sut.append(Card(name=f"test_card_{set_num}", card_num=card_num, set_num=set_num, rarity="common"))
         for card_num in range(num_cards_in_set)]

        result = sut.get_cards_in_set(set_num)

        self.assertEqual(num_cards_in_set, len(result))
