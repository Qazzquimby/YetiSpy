import abc
import collections


class FieldHashCollection(abc.ABC):
    def __init__(self):
        self.contents = []  # todo make readonly property
        self.dict = collections.defaultdict(lambda: collections.defaultdict(list))
        self.updated = False

    def append(self, input):
        self.contents.append(input)
        self._add_to_dict(input)

    def _add_to_dict(self, input: input):
        raise NotImplementedError
