"""
This file contains configuration variables that shouldn’t be in version control.

This includes things like API keys and database URIs containing passwords.
This also contains variables that are specific to this particular instance of your application.
For example, you might have DEBUG = False in config.py, but set DEBUG = True in instance/config.py on your local
machine for development.
Since this file will be read in after config.py, it will override it and set DEBUG = True."""
ENV = 'development'
SECRET_KEY = 'dev'

WARCRY_KEY = 'e6b3bf05-2fb7-4979-baf8-92328818e3f5'

UPDATE_KEY = 'teH9sWmTv0mqs4tmeAHRKfB9Pme9Z0nl'

DATABASE = 'mysql+pymysql://root:Q1a1zz22@localhost/infiltrate'

