from flask_restplus import Resource
from api_config import api
from flask import current_app as app

ns = api.namespace('properties', description="Properties on the host")


@ns.route('/')
class Properties(Resource):

    def get(self):
        """
        Returns all started properties
        """
        FogAgent = app.config['FogAgent']
        res = []
        for prop in FogAgent.running_properties():
            tmp = {
                'name': prop.name,
                'parameter': prop.parameter
            }
            res.append(tmp)

        return res, 200