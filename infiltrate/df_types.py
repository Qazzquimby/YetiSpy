"""Handles creation of specific dataframe types for type hinting."""
import functools
import typing as t

import pandas as pd
import sqlalchemy.orm


def _sqlalchemy_class_to_column_names(sqlalchemy_class):
    sqlalchemy.orm.class_mapper(sqlalchemy_class)
    column_names = [
        prop.key
        for prop in sqlalchemy.orm.class_mapper(sqlalchemy_class).iterate_properties
        if isinstance(prop, sqlalchemy.orm.ColumnProperty)
    ]
    return column_names


def _sqlalchemy_object_to_dict(sqlalchemy_object):
    column_names = _sqlalchemy_class_to_column_names(sqlalchemy_object.__class__)
    column_dict = {
        column_name: sqlalchemy_object.__getattribute__(column_name)
        for column_name in column_names
    }
    return column_dict


def sqlalchemy_objects_to_df(sqlalchemy_objects: t.Iterable):
    rows = [_sqlalchemy_object_to_dict(obj) for obj in sqlalchemy_objects]
    df = pd.DataFrame(rows)
    return df


# noinspection PyUnresolvedReferences,PyProtectedMember
def get_columns_for_model(model) -> t.List[str]:
    """Creates a dataframe type with columns matching the model's columns."""
    columns = model._sa_class_manager._all_key_set
    return columns


def get_columns_from_dataframe_type(df_type: functools.partial) -> t.List[str]:
    """Gets the column names from the df type."""
    columns = df_type.keywords["columns"]
    return columns


def make_dataframe_type(columns: t.List[str]) -> functools.partial:
    """Makes a dataframe type with the given columns."""
    df_type = functools.partial(pd.DataFrame, columns=columns)
    return df_type
