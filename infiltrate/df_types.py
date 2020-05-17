"""Handles creation of specific dataframe types for type hinting."""
import functools
import typing

import pandas as pd


# todo use dataenforce to handle this.

# noinspection PyUnresolvedReferences,PyProtectedMember
def get_columns_for_model(model) -> typing.List[str]:
    """Creates a dataframe type with columns matching the model's columns."""
    columns = model._sa_class_manager._all_key_set
    return columns


def get_columns_from_dataframe_type(df_type: functools.partial
                                    ) -> typing.List[str]:
    """Gets the column names from the df type."""
    columns = df_type.keywords['columns']
    return columns


def make_dataframe_type(columns: typing.List[str]) -> functools.partial:
    """Makes a dataframe type with the given columns."""
    df_type = functools.partial(pd.DataFrame, columns=columns)
    return df_type
