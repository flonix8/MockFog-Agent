from flask_restplus import Resource, fields
from api_config import api
from flask import current_app as app
from flask import request

ns = api.namespace('tc-config', description="The local TC configuration.")

tc_rule_fields = api.model('rule', {
    'dst_net': fields.String(description='Destination subnet or IP', example='1.1.1.1/24'),
    'out_rate': fields.String(description='Bandwidth to destination', example='10mbps'),
    'delay': fields.String(description='Additional latency to dst_net', example='10ms'),
    'dispersion': fields.String(description='Additional latency dispersion to dst_net', example='10ms', required=False),
    'loss': fields.String(description='Additional packet loss to dst_net', example='0.1'),
    'corrupt': fields.String(description='Additional packet corruption to dst_net', example='0.1'),
    'duplicate': fields.String(description='Additional packet duplication to dst_net', example='0.1'),
    'reorder': fields.String(description='Additional packet reordering to dst_net', example='0.1')
})
tc_config = api.model('tc-parameters', {
    'out_rate': fields.String(description='Output bandwidth', example='100mbps'),
    'in_rate': fields.String(description='Input bandwidth', example='100mbps'),
    'rules': fields.List(fields.Nested(tc_rule_fields))
})

@ns.route('/')
class Tc_config(Resource):
    @api.doc(responses={200: 'TC configuration retrieved',
                        201: 'TC is not running'})
    def get(self):
        """
        Retrieve the current TC configuration
        """
        FogAgent = app.config['FogAgent']
        tc = FogAgent.get_property('TC')
        res = tc.parameter
        return res, 200

    @api.doc(responses={200: 'TC initialized',
                        500: 'TC was not started'})
    @ns.expect(tc_config)
    def post(self):
        """
        Start TC
        """
        config = request.json
        FogAgent = app.config['FogAgent']
        tc = FogAgent.get_property('TC')
        if FogAgent.start_property(tc, config):
            res = {
                'msg': "TC was successfully started"
            }
            return res, 200
        api.abort(500, "TC was not started")

    @api.doc(responses={200: 'TC configuration updated',
                        400: 'Update not possible. Please start TC first.',
                        500: 'TC update was not successfull'})
    #@ns.param('config', 'Specifies the TC configuration', _in='body')
    @ns.expect(tc_config)
    def put(self):
        """
        Update the TC configuration
        """
        config = request.json
        FogAgent = app.config['FogAgent']
        tc = FogAgent.get_property('TC')
#        if not FogAgent.property_running(tc):
#            res = {
#                'msg': 'Update not possible. Please start TC first.'
#            }
#            return res, 201
        if FogAgent.update_property(tc, config):
            res = {
                'msg': "TC was successfully updated"
            }
            return res, 200
        api.abort(500, "TC update failed")

    @api.doc(responses={200: 'TC stopped',
                        500: 'TC has not been stopped'})
    def delete(self):
        """
        TC shut down
        """
        FogAgent = app.config['FogAgent']
        tc = FogAgent.get_property('TC')
        FogAgent.stop_property(tc)
        if not FogAgent.property_running(tc):
            res = {
                'msg': "TC was successfully stopped"
            }
            return res, 200
        api.abort(500, "TC has not been stopped")
