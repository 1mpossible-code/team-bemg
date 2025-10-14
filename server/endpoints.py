"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""

from flask_restx import Resource, Namespace

# Create namespace for general endpoints
general_ns = Namespace('general', description='General API operations')

# Constants for endpoints and responses
HELLO_EP = '/hello'
HELLO_RESP = 'hello'


@general_ns.route('/hello')
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    @general_ns.doc('hello_world')
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {'hello': 'world'}


@general_ns.route('/endpoints')
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    @general_ns.doc('list_endpoints')
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        from flask import current_app
        endpoints = sorted(rule.rule for rule in
                           current_app.url_map.iter_rules())
        return {"Available endpoints": endpoints}
