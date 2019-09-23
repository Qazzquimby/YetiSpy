import os
import tempfile

import pytest

import infiltrate


@pytest.fixture
def client():
    db_fd, infiltrate.application.config['DATABASE'] = tempfile.mkstemp()
    infiltrate.application.config['TESTING'] = True
    test_client = infiltrate.application.test_client()

    # with infiltrate.app.app_context():
    #     infiltrate.init_db()

    yield test_client

    os.close(db_fd)
    os.unlink(infiltrate.application.config['DATABASE'])


def test_playset_dict_create(client):
    from infiltrate import card_collections

    sut = card_collections.PlaysetDict()

    key = 1
    default_values = sut[key]

    for i in range(4):
        assert default_values[i] == 0


def test_playset_dict_keys(client):
    from infiltrate import card_collections

    sut = card_collections.PlaysetDict()

    num_cards = 5
    keys = [i for i in range(num_cards)]
    _ = [sut[key] for key in keys]

    assert len(sut.keys()) == num_cards
    for key in keys:
        assert key in sut.keys()
