from unittest import TestCase

from infiltrate.base_learner import JsonInterface
from infiltrate.field_hash_collection import JsonLoadedCollection


class ContentStub:
    pass


class JsonLoadedCollectionStub(JsonLoadedCollection):

    def _add_to_dict(self, entry: any):
        pass

    @classmethod
    def json_entry_to_content(cls, json_entry: dict):
        return json_entry


class _JsonLoaderStub:
    fake_json_entries = [
                            {"data1": 1,
                             "data2": 2}
                        ] * 3

    def load_json_entries(self):
        return self.fake_json_entries


class TestJsonInterface(TestCase):
    def test_load_empty_loads_empty_collection(self):
        sut = JsonInterface("test_prefix", "test_name", JsonLoadedCollectionStub)

        result = sut.load_empty()
        self.assertEqual(JsonLoadedCollectionStub, type(result))
        self.assertEqual(0, len(result.contents))

    def test_load(self):
        sut = JsonInterface("test_prefix", "test_name", JsonLoadedCollectionStub)

        fake_json_entries = [
                                {"data1": 1,
                                 "data2": 2}
                            ] * 3
        json_loader_stub = _JsonLoaderStub()
        json_loader_stub.fake_json_entries = fake_json_entries
        sut._loader = json_loader_stub

        result = sut.load()

        self.assertEqual(JsonLoadedCollectionStub, type(result))
        self.assertEqual(fake_json_entries, result.contents)
