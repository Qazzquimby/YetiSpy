"""Handles saving and loading objects to SQL"""
import os

DB_FILENAME = os.path.abspath('data.db')


def create_db_if_not_exist():
    with open(DB_FILENAME, "w+") as _:
        pass


connection_string = rf'sqlite:{DB_FILENAME}'
