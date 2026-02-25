from flask import request
from flask_restx import Resource, fields, Namespace, reqparse
from http import HTTPStatus

import data.cities as cities_data
import data.states as states_data
from server.helpers import (
    apply_pagination,
    validate_pagination,
    validate_range_filters,
)

cities_ns = Namespace('cities', description='City operations')

# we avoid importing validators that touch the database on import
LAT_MIN, LAT_MAX = -90, 90
LON_MIN, LON_MAX = -180, 180
coordinate_model = cities_ns.model('Coordinate', {
    'latitude': fields.Float(required=True, description='Latitude',
                             min=LAT_MIN,
                             max=LAT_MAX,
                             example=40.7128),
    'longitude': fields.Float(required=True, description='Longitude',
                              min=LON_MIN,
                              max=LON_MAX,
                              example=-74.0060)
})

list_parser = reqparse.RequestParser()
list_parser.add_argument('name', type=str, required=False,
                         help='Search cities by name (partial match)')
list_parser.add_argument('country_code', type=str, required=False,
                         help='Filter by country code')
list_parser.add_argument('state_code', type=str, required=False,
                         help='Filter by state code')
list_parser.add_argument('min_population', type=int, required=False,
                         help='Filter by minimum population')
list_parser.add_argument('max_population', type=int, required=False,
                         help='Filter by maximum population')
list_parser.add_argument(
    'limit',
    type=int,
    required=False,
    help='Maximum number of cities to return (positive integer)'
)
list_parser.add_argument(
    'offset',
    type=int,
    required=False,
    help='Number of cities to skip from the start (>= 0)'
)

# Request model for creating cities (no timestamps - server-side only)
city_create_model = cities_ns.model(
    'CityCreate',
    {
        'city_name': fields.String(
            required=True,
            description='City name',
            example='New York'),
        'state_code': fields.String(
            required=True,
            description='Parent state code (e.g., NY)',
            example='NY'),
        'country_code': fields.String(
            required=True,
            description='Parent country code (ISO 3166-1 alpha-2)',
            example='US'),
        'population': fields.Integer(
            description='Population count',
            example=8468000),
        'area_km2': fields.Float(
            description='Area in square kilometers',
            example=783.8),
        'coordinates': fields.Nested(
            coordinate_model,
            required=True,
            description='Geographic coordinates')
    }
)

# Response model for cities (includes read-only timestamps)
city_model = cities_ns.model(
    'City',
    {
        'city_name': fields.String(
            required=True,
            description='City name',
            example='New York'),
        'state_code': fields.String(
            required=True,
            description='Parent state code (e.g., NY)',
            example='NY'),
        'country_code': fields.String(
            required=True,
            description='Parent country code (ISO 3166-1 alpha-2)',
            example='US'),
        'population': fields.Integer(
            description='Population count',
            example=8468000),
        'area_km2': fields.Float(
            description='Area in square kilometers',
            example=783.8),
        'coordinates': fields.Nested(
            coordinate_model,
            required=True,
            description='Geographic coordinates'),
        'created_at': fields.DateTime(
            description='Creation timestamp (read-only, set by server)',
            example='2025-11-12T12:00:00Z'),
        'updated_at': fields.DateTime(
            description='Last update timestamp (read-only, set by server)',
            example='2025-11-12T12:00:00Z')
    }
)

# Model for updating (key fields are not updatable)
city_update_model = cities_ns.model('CityUpdate', {
    'population': fields.Integer(description='Population count'),
    'area_km2': fields.Float(description='Area in square kilometers'),
    'coordinates': fields.Nested(coordinate_model,
                                 description='Geographic coordinates')
})

error_model = cities_ns.model('Error', {
    'error': fields.String(description='Error message'),
    'code': fields.Integer(description='HTTP status code')
})


@cities_ns.route('')
class CitiesList(Resource):

    @cities_ns.doc('list_cities')
    @cities_ns.expect(list_parser)
    @cities_ns.marshal_list_with(city_model)
    def get(self):
        args = list_parser.parse_args()
        name_query = args.get('name')
        country_code = args.get('country_code')
        state_code = args.get('state_code')
        min_pop = args.get('min_population')
        max_pop = args.get('max_population')
        limit = args.get('limit')
        offset = args.get('offset')

        validate_pagination(limit, offset, cities_ns.abort)
        validate_range_filters(
            min_pop,
            max_pop,
            'min_population',
            'max_population',
            cities_ns.abort,
        )

        try:
            # Replaces the if/elif block
            data = cities_data.get_cities_filtered(
                name=name_query,
                state_code=state_code,
                country_code=country_code,
                min_pop=min_pop,
                max_pop=max_pop
            )

            data = apply_pagination(data, limit, offset)
            return data, HTTPStatus.OK
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            message=f"Database error: {str(e)}")

    @cities_ns.doc('create_city')
    @cities_ns.expect(city_create_model)
    @cities_ns.marshal_with(city_model, code=HTTPStatus.CREATED)
    @cities_ns.response(HTTPStatus.BAD_REQUEST, 'Validation error',
                        error_model)
    @cities_ns.response(HTTPStatus.CONFLICT, 'City already exists',
                        error_model)
    def post(self):
        """
        Create a new city
        Creates a new city with the provided data.
        Timestamps are automatically set by the server.
        """
        city_data = request.json

        state_code = city_data.get('state_code')
        country_code = city_data.get('country_code')

        if not state_code or not country_code:
            cities_ns.abort(HTTPStatus.BAD_REQUEST,
                            "state_code and country_code are required")

        # Only wrap the DB access, not the abort calls
        try:
            parent_state = states_data.get_state_by_code(state_code.upper())
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Error validating parent state: {str(e)}")

        if not parent_state:
            cities_ns.abort(HTTPStatus.BAD_REQUEST,
                            (f"Parent state with code '{state_code}' "
                             f"does not exist"))

        if parent_state.get('country_code') != country_code.upper():
            cities_ns.abort(HTTPStatus.BAD_REQUEST,
                            (f"State '{state_code}' does not belong to "
                             f"country '{country_code}'"))

        try:
            success = cities_data.add_city(city_data)
            if success:
                return city_data, HTTPStatus.CREATED
            else:
                cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                                "Failed to create city")

        except ValueError as e:
            cities_ns.abort(HTTPStatus.BAD_REQUEST, str(e))
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")


@cities_ns.route('/country/<string:country_code>')
@cities_ns.param('country_code', 'The country code')
class CitiesByCountry(Resource):
    """Cities filtered by country"""

    @cities_ns.doc('get_cities_by_country')
    @cities_ns.marshal_list_with(city_model)
    def get(self, country_code):
        """
        Get cities by country code.
        """
        try:
            cities = cities_data.get_cities_by_country(country_code.upper())
            return cities, HTTPStatus.OK
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            message=f"Database error: {str(e)}")


@cities_ns.route('/state/<string:state_code>')
@cities_ns.param('state_code', 'The state code (2 letters)')
class CitiesByState(Resource):
    """Cities filtered by state"""

    @cities_ns.doc('get_cities_by_state')
    @cities_ns.marshal_list_with(city_model)
    def get(self, state_code):
        """
        Get cities by state code.
        """
        try:
            cities = cities_data.get_cities_by_state(state_code.upper())
            return cities, HTTPStatus.OK
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            message=f"Database error: {str(e)}")


@cities_ns.route('/<string:state_code>/<string:city_name>')
@cities_ns.param('state_code', 'The 2-letter state code')
@cities_ns.param('city_name', 'The name of the city')
class City(Resource):
    """Single city endpoint"""

    @cities_ns.doc('get_city')
    @cities_ns.marshal_with(city_model)
    @cities_ns.response(HTTPStatus.NOT_FOUND, 'City not found',
                        error_model)
    def get(self, state_code, city_name):
        """
        Retrieve a specific city
        Returns city details for the given state code and city name.
        """
        try:
            city = cities_data.get_city_by_name_and_state(
                city_name, state_code.upper()
            )
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            message=f"Database error: {str(e)}")

        if city:
            return city, HTTPStatus.OK
        else:
            cities_ns.abort(HTTPStatus.NOT_FOUND,
                            message=(f"City '{city_name}' in state "
                                     f"'{state_code}' not found"))

    @cities_ns.doc('update_city')
    @cities_ns.expect(city_update_model)
    @cities_ns.marshal_with(city_model)
    @cities_ns.response(HTTPStatus.NOT_FOUND, 'City not found',
                        error_model)
    @cities_ns.response(HTTPStatus.BAD_REQUEST, 'Validation error',
                        error_model)
    def put(self, state_code, city_name):
        """
        Update a city
        Updates the city with the provided data.
        The updated_at timestamp is automatically set by the server.
        """
        update_data = request.json

        try:
            success = cities_data.update_city(
                city_name, state_code.upper(), update_data
            )
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            message=f"Database error: {str(e)}")

        if success:
            try:
                updated_city = cities_data.get_city_by_name_and_state(
                    city_name, state_code.upper()
                )
                return updated_city, HTTPStatus.OK
            except Exception as e:
                cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                                message=f"Database error: {str(e)}")
        else:
            cities_ns.abort(HTTPStatus.NOT_FOUND,
                            message=(f"City '{city_name}' in state "
                                     f"'{state_code}' not found"))

    @cities_ns.doc('delete_city')
    @cities_ns.response(HTTPStatus.NO_CONTENT,
                        'City deleted successfully')
    @cities_ns.response(HTTPStatus.NOT_FOUND, 'City not found',
                        error_model)
    def delete(self, state_code, city_name):
        """
        Delete a city
        Removes the city from the database.
        """
        try:
            success = cities_data.delete_city(
                city_name, state_code.upper()
            )
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            message=f"Database error: {str(e)}")

        if success:
            return '', HTTPStatus.NO_CONTENT
        else:
            cities_ns.abort(HTTPStatus.NOT_FOUND,
                            message=(f"City '{city_name}' in state "
                                     f"'{state_code}' not found"))
