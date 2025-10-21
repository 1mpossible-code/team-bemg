from flask import request
from flask_restx import Resource, fields, Namespace
from http import HTTPStatus
import data.cities as cities_data
import data.states as states_data
from data.models import cities_validator

cities_ns = Namespace('cities', description='City operations')

coord_props = cities_validator["$jsonSchema"]["properties"]["coordinates"]["properties"]
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

city_model = cities_ns.model('City', {
    'city_name': fields.String(required=True, description='City name',
                              example='New York'),
    'state_code': fields.String(required=True,
                               description='Parent state code (e.g., NY)',
                               example='NY'),
    'country_code': fields.String(required=True,
                                 description='Parent country code (ISO 3166-1 alpha-2)',
                                 example='US'),
    'population': fields.Integer(description='Population count',
                                 example=8468000),
    'area_km2': fields.Float(description='Area in square kilometers',
                             example=783.8),
    'coordinates': fields.Nested(coordinate_model, required=True,
                                 description='Geographic coordinates')
})

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

    