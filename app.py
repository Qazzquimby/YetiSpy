"""
This is invoked to start a production server.
"""
import sys

sys.path.append("/opt/python/current/app/infiltrate")
from infiltrate import application, setup_application

if __name__ == "__main__":
    setup_application(application)
    application.run()
