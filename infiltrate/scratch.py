import pandas as pd

from infiltrate import db
import pandas_profiling
import numpy as np

session = db.engine.raw_connection()
query = f"""\
        SELECT *
        FROM decks
"""
df = pd.read_sql_query(query, session)

df["rating"] = np.maximum(0, df["rating"])

df["log_views"] = np.log(df["views"])
df["log_rating"] = np.log(df["rating"])
df["rating_per_view"] = df["rating"] / df["views"]

df["score"] = df["rating"] * 300 + df["views"] + df["rating_per_view"] * 300 * 300

profile = pandas_profiling.ProfileReport(df)
profile.to_file("deck_profiling.html")

print("debug")
