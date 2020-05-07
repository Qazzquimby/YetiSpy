# from unittest import TestCase
#
# import infiltrate.card as cards
# from infiltrate.base_learner import JsonCompatible
# from parameterized import parameterized
#
#
# class JsonCompatibleStub(JsonCompatible):
#     pass
#
#
# class TestCardCollection(TestCase):
#     def test_get_cards_in_set__when_set_is_0__throws_ValueError(self):
#         sut = cards.CardCollection()
#
#         with self.assertRaises(ValueError):
#             sut.get_cards_in_set(0)
#
#     def test_get_cards_in_set__when_set_is_1__gets_cards_in_0_and_1(self):
#         sut = cards.CardCollection()
#
#         [sut.append(cards.Card(name=f"test_card_{set_num}", card_num=0, set_num=set_num, rarity="common"))
#          for set_num in range(2)]
#
#         result = sut.get_cards_in_set(1)
#
#         self.assertEqual(2, len(result))
#
#     def test_get_cards_in_set__when_set_is_2plus__gets_cards_in_set(self):
#         sut = cards.CardCollection()
#
#         set_num = 3
#         num_cards_in_set = 5
#
#         [sut.append(cards.Card(name=f"test_card_{set_num}", card_num=card_num, set_num=set_num, rarity="common"))
#          for card_num in range(num_cards_in_set)]
#
#         result = sut.get_cards_in_set(set_num)
#
#         self.assertEqual(num_cards_in_set, len(result))
#
#
# class TestCardUtilities(TestCase):
#
#     @parameterized.expand([["bore", "https://eternalwarcry.com/cards/details/1003-1/bore", 1],
#                            ["on the hunt", "https://eternalwarcry.com/cards/details/2-5/on-the-hunt", 5]])
#     def test_get_card_num_from_card_url(self, name, url, expected):
#         result = cards.get_card_num_from_card_url(url)
#
#         self.assertEqual(expected, result)
#
#     @parameterized.expand([["bore", "https://eternalwarcry.com/cards/details/1003-1/bore", 1003],
#                            ["on the hunt", "https://eternalwarcry.com/cards/details/2-5/on-the-hunt", 2]])
#     def test_get_set_num_from_card_url(self, name, url, expected):
#         result = cards.get_set_num_from_card_url(url)
#
#         self.assertEqual(expected, result)
