"""
This is the file that is invoked to start up a development server.

It gets a copy of the app from your package and runs it.
This won’t be used in production, but it will see a lot of mileage in development.
"""
import sys
import threading
import webbrowser

sys.path.append("/opt/python/current/app/infiltrate")
from infiltrate import application, setup_application


def open_in_browser():
    url = "http://127.0.0.1:5000/"
    threading.Timer(1.25, lambda: webbrowser.open(url)).start()


def enable_profiling(application):
    from werkzeug.middleware.profiler import ProfilerMiddleware

    application.config["PROFILE"] = True
    application.wsgi_app = ProfilerMiddleware(
        application.wsgi_app, sort_by=("cumulative", "name"), restrictions=[60]
    )


if __name__ == "__main__":
    enable_profiling(application)

    setup_application(application)
    open_in_browser()
    application.run(debug=True, use_debugger=False, use_reloader=False)
