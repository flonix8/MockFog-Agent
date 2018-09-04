import threading

from flask_restplus import Resource, fields
from api_config import api
from flask import current_app as app
from flask import request
import logging

ns = api.namespace('ping', description="Run ping tests")


host = api.model('host', {
    'hostname': fields.String(description='Hostname', example='edge_node1'),
    'ip': fields.String(description='IP of Host', example='10.0.0.1')
})

host_list = api.model('hosts', {
    'threads_num': fields.Integer(description='Number of threads to run ping with', example=1, default=1),
    'seconds': fields.String(description='seconds to run each ping for', example='4'),
    'hosts': fields.List(fields.Nested(host))
})

@ns.route('')
class PingList(Resource):

    @api.doc(responses={200: 'Everything ok',
                        201: 'No known hosts'})
    def get(self):
        """
        Returns dict of latencies to known hosts
        """
        FogAgent = app.config['FogAgent']
        dict = FogAgent.rtt_dict

        if len(dict) == 0:
            return dict, 201
        return dict, 200

    @api.doc(responses={200: 'Ping started',
                        423: 'Another ping is still running'})
    @ns.expect(host_list)
    def post(self):
        FogAgent = app.config['FogAgent']
        host_list = request.json['hosts']
        num_of_threads = request.json['threads_num']
        seconds = request.json['seconds']

        if FogAgent.ping_running:
            logging.info("There is already a ping running")
            api.abort(423, "There is already a ping running")

        main_ping_thread = threading.Thread(target=FogAgent.ping_hosts, args=(num_of_threads, host_list, seconds))
        main_ping_thread.start()
        return { 'msg': 'Ping started. Please wait at least %s seconds' % (seconds)}, 200


@ns.route('/<string:hostname>/')
@api.doc(params={'hostname' : 'Hostname'})
class Ping(Resource):

    @api.doc(responses={200: 'Statistics of Host returned',
                        404: 'Host not found'})
    def get(self, hostname):
        FogAgent = app.config['FogAgent']
        stats = FogAgent.get_rtt_host(hostname)
        if stats == None:
            res = {'message' : 'Host not found'}
            return res, 404
        else:
            res = {
                hostname: stats
            }
            return res, 200


