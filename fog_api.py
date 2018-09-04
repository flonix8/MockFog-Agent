from flask import Flask, Blueprint
from api_endpoints.properties import ns as properties_ns
from api_endpoints.tc_config import ns as tc_ns
from api_endpoints.ping import ns as ping_ns
from api_endpoints.firewall import ns as fw_ns
#from api_endpoints.test_property import ns as test_ns
from api_config import api


def initialize(app):
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)
    api.add_namespace(properties_ns)
    api.add_namespace(tc_ns)
    api.add_namespace(ping_ns)
    api.add_namespace(fw_ns)
    #api.add_namespace(test_ns)
    app.register_blueprint(blueprint)


def create_app(FogAgent):
    app = Flask(__name__)
    app.config['FogAgent'] = FogAgent
    initialize(app)
    return app


if __name__== "__main__":
    create_app()