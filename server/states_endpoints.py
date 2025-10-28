"""
Geographic API endpoints for states.
Provides full CRUD operations with Swagger documentation.
"""

from flask import request
from flask_restx import Resource, fields, Namespace, reqparse
from http import HTTPStatus
import data.states as states_data
import data.countries as countries_data
from data.models import states_validator

# Create namespace for states endpoints
states_ns = Namespace('states', description='State operations')

# Define models for Swagger documentation and validation
state_props = states_validator["$jsonSchema"]["properties"]

state_model = states_ns.model(
    'State',
    {
        'state_name': fields.String(
            required=True,
            description='State name',
            example='California'),
        'state_code': fields.String(
            required=True,
            description='State code (e.g., CA)',
            example='CA',
            pattern=state_props["state_code"]["pattern"]),
        'country_code': fields.String(
            required=True,
            description='Parent country code (ISO 3166-1 alpha-2)',
            example='US',
            pattern=state_props["country_code"]["pattern"]),
        'capital': fields.String(
            required=True,
            description='Capital city',
            example='Sacramento'),
        'population': fields.Integer(
            required=True,
            description='Population count',
            example=39538223),
        'area_km2': fields.Float(
            required=True,
            description='Area in square kilometers',
            example=423970.0)})

state_update_model = states_ns.model('StateUpdate', {
    'state_name': fields.String(description='State name'),
    'capital': fields.String(description='Capital city'),
    'population': fields.Integer(description='Population count'),
    'area_km2': fields.Float(description='Area in square kilometers')
})

error_model = states_ns.model('Error', {
    'error': fields.String(description='Error message'),
    'code': fields.Integer(description='HTTP status code')
})

# Parser for query parameters on the GET /states endpoint
list_parser = reqparse.RequestParser()
list_parser.add_argument(
    'country_code',
    type=str,
    required=False,
    help='Filter states by country code (ISO 3166-1 alpha-2)',
    location='args')
list_parser.add_argument(
    'min_population',
    type=int,
    required=False,
    help='Filter states with population >= min_population',
    location='args')
list_parser.add_argument(
    'max_population',
    type=int,
    required=False,
    help='Filter states with population <= max_population',
    location='args')


@states_ns.route('')
class StatesList(Resource):
    """States collection endpoint"""

    @states_ns.doc('list_states')
    @states_ns.expect(list_parser)
    @states_ns.marshal_list_with(state_model)
    def get(self):
        """
        Retrieve all states, with optional filters
        Returns a list of all states, optionally filtered by country_code
        or population range.
        """
        args = list_parser.parse_args()
        country_code = args.get('country_code')
        min_pop = args.get('min_population')
        max_pop = args.get('max_population')

        try:
            # Check which filter to apply
            if country_code:
                states = states_data.get_states_by_country(
                    country_code.upper())
            elif min_pop is not None or max_pop is not None:
                states = states_data.get_states_by_population_range(
                    min_pop, max_pop)
            else:
                # No filters, get all states
                states = states_data.get_states()

            return states, HTTPStatus.OK

        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")

    @states_ns.doc('create_state')
    @states_ns.expect(state_model)
    @states_ns.marshal_with(state_model, code=HTTPStatus.CREATED)
    @states_ns.response(HTTPStatus.BAD_REQUEST, 'Validation error',
                        error_model)
    @states_ns.response(HTTPStatus.CONFLICT, 'State already exists',
                        error_model)
    def post(self):
        """
        Create a new state
        Creates a new state with the provided data.
        """
        state_data = request.json

        # Validate parent country exists
        country_code = state_data.get('country_code')
        if not country_code:
            states_ns.abort(HTTPStatus.BAD_REQUEST, "country_code is required")

        try:
            if not countries_data.get_country_by_code(country_code.upper()):
                states_ns.abort(HTTPStatus.BAD_REQUEST,
                                f"Parent country with code '{country_code}' "
                                f"does not exist")
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Error validating country: {str(e)}")

        try:
            success = states_data.add_state(state_data)
            if success:
                return state_data, HTTPStatus.CREATED
            else:
                states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                                "Failed to create state")
        except ValueError as e:
            states_ns.abort(HTTPStatus.BAD_REQUEST, str(e))
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")
