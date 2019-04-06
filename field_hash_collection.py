import abc
import collections


class FieldHashCollection(abc.ABC):
    def __init__(self):
        self._contents = []  # todo make readonly property
        self.dict = collections.defaultdict(lambda: collections.defaultdict(list))

    def append(self, input):
        self._contents.append(input)
        self._add_to_dict(input)

    def _add_to_dict(self, input: input):
        raise NotImplementedError
