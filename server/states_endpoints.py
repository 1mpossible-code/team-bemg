"""
Geographic API endpoints for states.
Provides full CRUD operations with Swagger documentation.
"""

from flask import request
from flask_restx import Resource, fields, Namespace, reqparse
from http import HTTPStatus
import data.states as states_data
import data.countries as countries_data
import data.cities as cities_data
from server.cities_endpoints import city_model
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
# Read-only timestamp fields (added to validators as dates)
state_model['created_at'] = fields.DateTime(
    description='Creation timestamp', example='2025-11-12T12:00:00Z'
)
state_model['updated_at'] = fields.DateTime(
    description='Last update timestamp', example='2025-11-12T12:00:00Z'
)

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
    help='Filter states by country code (ISO 3166-1 alpha-2), e.g., US',
    location='args')
list_parser.add_argument(
    'min_population',
    type=int,
    required=False,
    help='Filter states with population >= min_population (e.g., 1000000)',
    location='args')
list_parser.add_argument(
    'max_population',
    type=int,
    required=False,
    help='Filter states with population <= max_population (e.g., 5000000)',
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


@states_ns.route('/<string:state_code>')
@states_ns.param('state_code', 'The state code (e.g., CA, NY)')
class State(Resource):
    """Single state endpoint"""

    @states_ns.doc('get_state')
    @states_ns.marshal_with(state_model)
    @states_ns.response(HTTPStatus.NOT_FOUND, 'State not found', error_model)
    def get(self, state_code: str):
        """
        Retrieve a specific state by its code.
        """
        try:
            state = states_data.get_state_by_code(state_code.upper())
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")

        if state:
            return state, HTTPStatus.OK
        else:
            states_ns.abort(HTTPStatus.NOT_FOUND,
                            f"State with code '{state_code}' not found")

    @states_ns.doc('update_state')
    @states_ns.expect(state_update_model)
    @states_ns.marshal_with(state_model)
    @states_ns.response(HTTPStatus.NOT_FOUND, 'State not found', error_model)
    @states_ns.response(HTTPStatus.BAD_REQUEST, 'Validation err', error_model)
    def put(self, state_code: str):
        """
        Update a state by its code.
        """
        update_data = request.json or {}

        # If country_code provided, ensure it exists
        if 'country_code' in update_data:
            try:
                if not countries_data.get_country_by_code(
                        update_data['country_code'].upper()
                ):
                    states_ns.abort(HTTPStatus.BAD_REQUEST,
                                    ("Provided country_code does not exist: "
                                     f"{update_data['country_code']}"))
            except Exception as e:
                states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                                f"Error validating country: {str(e)}")

        try:
            success = states_data.update_state(state_code.upper(), update_data)
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")

        if success:
            try:
                updated = states_data.get_state_by_code(state_code.upper())
                return updated, HTTPStatus.OK
            except Exception as e:
                states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                                f"Database error: {str(e)}")
        else:
            states_ns.abort(HTTPStatus.NOT_FOUND,
                            f"State with code '{state_code}' not found")

    @states_ns.doc('delete_state')
    @states_ns.response(HTTPStatus.NO_CONTENT, 'State deleted successfully')
    @states_ns.response(HTTPStatus.NOT_FOUND, 'State not found', error_model)
    @states_ns.response(HTTPStatus.CONFLICT,
                        'Cannot delete state with dependent cities',
                        error_model)
    def delete(self, state_code: str):
        """
        Delete a state by its code. Fails with 409 if dependent cities exist.
        """
        try:
            success = states_data.delete_state(state_code.upper())
        except ValueError as e:
            states_ns.abort(HTTPStatus.CONFLICT, str(e))
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")

        if success:
            return "", HTTPStatus.NO_CONTENT
        else:
            states_ns.abort(HTTPStatus.NOT_FOUND,
                            f"State with code '{state_code}' not found")


@states_ns.route('/country/<string:country_code>')
@states_ns.param('country_code', 'The country code (ISO 3166-1), e.g., US')
class StatesByCountry(Resource):
    """List states by country code (convenience endpoint)."""

    @states_ns.doc('get_states_by_country')
    @states_ns.marshal_list_with(state_model)
    def get(self, country_code: str):
        """
        Retrieve all states for a specific country.
        Equivalent to GET /states?country_code=<code>.
        """
        try:
            return (states_data.get_states_by_country(country_code.upper()),
                    HTTPStatus.OK)
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")


@states_ns.route('/<string:state_code>/cities')
@states_ns.param('state_code', 'The state code (e.g., CA, NY)')
class StateCities(Resource):
    """List cities within a state (convenience endpoint)."""

    @states_ns.doc('get_state_cities')
    @states_ns.marshal_list_with(city_model)
    def get(self, state_code: str):
        """
        Retrieve all cities for a specific state.
        Equivalent to GET /cities?state_code=<code>.
        """
        try:
            return (cities_data.get_cities_by_state(state_code.upper()),
                    HTTPStatus.OK)
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")


@states_ns.route('/name/<string:state_name>')
@states_ns.param('state_name', 'The state name (e.g., California, New York)')
class StateByName(Resource):
    """Single state by name endpoint"""

    @states_ns.doc('get_state_by_name')
    @states_ns.marshal_with(state_model)
    @states_ns.response(HTTPStatus.NOT_FOUND, 'State not found', error_model)
    def get(self, state_name: str):
        """
        Retrieve a specific state by its name.
        """
        try:
            state = states_data.get_state_by_name(state_name)
        except Exception as e:
            states_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")

        if state:
            return state, HTTPStatus.OK
        else:
            states_ns.abort(HTTPStatus.NOT_FOUND,
                            f"State with name '{state_name}' not found")
