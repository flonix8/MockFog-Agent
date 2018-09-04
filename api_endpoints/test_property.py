from flask_restplus import Resource
from api_config import api
from flask import current_app as app

ns = api.namespace('testproperty', description="Start/Stop the Test Property")


@ns.route('/testproperty')
class TestProperty(Resource):

    @api.doc(responses={200: 'Propertiy is running',
                        201: 'Property is not running'})
    def get(self):
        """
        Returns status of TestProperty
        """
        FogAgent = app.config['FogAgent']
        prop = FogAgent.get_property('TestProperty')
        if FogAgent.property_running(prop):
            res = {
                'status': 'TestProperty is running'
            }
            return res, 200
        else:
            res = {
                'status': 'TestProperty is not running'
            }
            return res, 201


    @api.doc(responses={200: 'Property was successfully started',
                        500: 'Property was not started'})
    def post(self):
        """
        Start Testproperty
        """
        FogAgent = app.config['FogAgent']
        prop = FogAgent.get_property('TestProperty')
        FogAgent.start_property(prop, "testparams")
        if FogAgent.property_running(prop):
            res = {
                'msg': "TestProperty was successfully started"
            }
            return res, 200
        api.abort(500, "TestProperty was not started")


    @api.doc(responses={200: 'Property was successfully stopped',
                        500: 'Property has not been stopped'})
    def delete(self):
        """
        Stop Testproperty
        """
        FogAgent = app.config['FogAgent']
        prop = FogAgent.get_property('TestProperty')
        FogAgent.stop_property(prop)
        if not FogAgent.property_running(prop):
            res = {
                'msg': "TestProperty was successfully stopped"
            }
            return res, 200
        api.abort(500, "TestProperty has not been stopped")






