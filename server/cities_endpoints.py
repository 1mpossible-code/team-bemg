from flask import request
from flask_restx import Resource, fields, Namespace
from http import HTTPStatus
import data.cities as cities_data
import data.states as states_data
from data.models import cities_validator

cities_ns = Namespace('cities', description='City operations')

coord_props = (
    cities_validator["$jsonSchema"]["properties"]["coordinates"]["properties"]
)
coordinate_model = cities_ns.model('Coordinate', {
    'latitude': fields.Float(required=True, description='Latitude',
                             min=coord_props["latitude"]["minimum"],
                             max=coord_props["latitude"]["maximum"],
                             example=40.7128),
    'longitude': fields.Float(required=True, description='Longitude',
                              min=coord_props["longitude"]["minimum"],
                              max=coord_props["longitude"]["maximum"],
                              example=-74.0060)
})

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
            description='Geographic coordinates')
    }
)

error_model = cities_ns.model('Error', {
    'error': fields.String(description='Error message'),
    'code': fields.Integer(description='HTTP status code')
})


@cities_ns.route('')
class CitiesList(Resource):

    @cities_ns.doc('list_cities')
    @cities_ns.marshal_list_with(city_model)
    def get(self):
        try:
            return cities_data.get_cities(), HTTPStatus.OK
        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Database error: {str(e)}")

    @cities_ns.doc('create_city')
    @cities_ns.expect(city_model)
    @cities_ns.marshal_with(city_model, code=HTTPStatus.CREATED)
    @cities_ns.response(HTTPStatus.BAD_REQUEST, 'Validation error',
                        error_model)
    @cities_ns.response(HTTPStatus.CONFLICT, 'City already exists',
                        error_model)
    def post(self):
        city_data = request.json

        state_code = city_data.get('state_code')
        country_code = city_data.get('country_code')

        if not state_code or not country_code:
            cities_ns.abort(HTTPStatus.BAD_REQUEST,
                            "state_code and country_code are required")

        try:
            parent_state = states_data.get_state_by_code(state_code.upper())
            if not parent_state:
                cities_ns.abort(HTTPStatus.BAD_REQUEST,
                                (f"Parent state with code '{state_code}' "
                                 f"does not exist"))

            if parent_state['country_code'] != country_code.upper():
                cities_ns.abort(HTTPStatus.BAD_REQUEST,
                                (f"State '{state_code}' does not belong to "
                                 f"country '{country_code}'"))

        except Exception as e:
            cities_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                            f"Error validating parent state: {str(e)}")

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
