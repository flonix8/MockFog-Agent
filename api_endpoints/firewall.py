from flask_restplus import Resource, fields
from api_config import api
from flask import current_app as app
from flask import request

ns = api.namespace('firewall', description="The local firewall configuration.")

firewall = api.model('firewall-parameters', {
    'active': fields.Boolean(description='Blocks all incoming - and outgoing traffic', example='false')
})

@ns.route('/')
class Tc_config(Resource):
    @api.doc(responses={200: 'Firewall configuration retrieved',
                        201: 'Firewall is not running'})
    def get(self):
        """
        Retrieve the current Firewall configuration
        """
        FogAgent = app.config['FogAgent']
        fw = FogAgent.get_property('Firewall')
        res = fw.parameter
        return res, 200

    @api.doc(responses={200: 'Firewall initialized',
                        500: 'Firewall was not started'})
    @ns.expect(firewall)
    def post(self):
        """
        Start Firewall
        """
        config = request.json
        FogAgent = app.config['FogAgent']
        fw = FogAgent.get_property('Firewall')
        FogAgent.start_property(fw, config)
        if FogAgent.property_running(fw):
            res = {
                'msg': "Firewall was successfully started"
            }
            return res, 200
        api.abort(500, "Firewall was not started")

    @api.doc(responses={200: 'Firewall configuration updated',
                        400: 'Update not possible. Please start Firewall first.',
                        500: 'Firewall update was not successfull'})
    @ns.expect(firewall)
    def put(self):
        """
        Update Firewall rule
        """
        config = request.json
        FogAgent = app.config['FogAgent']
        fw = FogAgent.get_property('Firewall')
        if not FogAgent.property_running(fw):
            res = {
                'msg': 'Update not possible. Please start Firewall first.'
            }
            return res, 201
        if FogAgent.update_property(fw, config):
            res = {
                'msg': "Firewall was successfully updated"
            }
            return res, 200
        api.abort(500, "Firewall update failed")

    @api.doc(responses={200: 'Firewall stopped',
                        500: 'Firewall has not been stopped'})
    def delete(self):
        """
        Shutdown Firewall
        """
        FogAgent = app.config['FogAgent']
        fw = FogAgent.get_property('Firewall')
        FogAgent.stop_property(fw)
        if not FogAgent.property_running(fw):
            res = {
                'msg': "TC was successfully stopped"
            }
            return res, 200
        api.abort(500, "TC has not been stopped")






