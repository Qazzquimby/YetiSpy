import csv
import typing
from dataclasses import dataclass


@dataclass
class DeckSearch:
    name: str
    weight: float
    url: str


def get_deck_searches() -> typing.List[DeckSearch]:
    deck_searches = []
    search_urls_file_name = "search_urls.csv"

    with open(search_urls_file_name, "r") as file:
        reader = csv.reader(file)
        for line in reader:
            deck_search = _get_deck_search_from_line(line)
            deck_searches.append(deck_search)

    return deck_searches


def _get_deck_search_from_line(line: str) -> DeckSearch:
    name = line[0]
    weight = float(line[1])
    url = line[2]
    deck_search = DeckSearch(name, weight, url)
    return deck_search
