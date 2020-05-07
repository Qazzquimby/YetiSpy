"""
This file contains configuration variables that shouldn’t be in version control.

This includes things like API keys and database URIs containing passwords.
This also contains variables that are specific to this particular instance of your application.
For example, you might have DEBUG = False in config.py, but set DEBUG = True in instance/config.py on your local
machine for development.
Since this file will be read in after config.py, it will override it and set DEBUG = True."""
import os

SECRET_KEY = '2vA4DQVQskiOpRM7qB20mKrDdlt868H5'
WARCRY_KEY = 'e6b3bf05-2fb7-4979-baf8-92328818e3f5'
UPDATE_KEY = 'teH9sWmTv0mqs4tmeAHRKfB9Pme9Z0nl'

if 'RDS_HOSTNAME' in os.environ:
    ENV = 'production'

    DB_USER = os.environ['RDS_USERNAME']
    DB_PASSWORD = os.environ['RDS_PASSWORD']
    DB_HOST_PORT = f"{os.environ['RDS_HOSTNAME']}:{os.environ['RDS_PORT']}"
    DB_NAME = os.environ['RDS_DB_NAME']

else:
    ENV = 'development'

    DB_USER = 'root'
    DB_PASSWORD = 'Q1a1zz22'
    DB_HOST_PORT = 'localhost'
    DB_NAME = 'infiltrate'

    # DATABASE = 'mysql+pymysql://root:PASSWORD@localhost/infiltrate'
DATABASE = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST_PORT}/{DB_NAME}'
print(f"Database connection string: {DATABASE}")
# IF DATABASE CHANGES, ALSO UPDATE ALEMBIC.INI
