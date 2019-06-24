"""This is where the routes are defined."""
from flask_classy import FlaskView


class CardsView(FlaskView):
    route_base = '/'

    def index(self):
        return "Under construction."
