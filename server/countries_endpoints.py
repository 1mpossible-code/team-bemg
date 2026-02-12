"""
Geographic API endpoints for countries.
Provides full CRUD operations with Swagger documentation.
"""

from flask import request, url_for
from flask_restx import Resource, fields, Namespace, reqparse
from http import HTTPStatus

import data.countries as countries_data
import data.states as states_data
from data.countries import VALID_CONTINENTS
from server.states_endpoints import state_model
from server.helpers import apply_pagination, validate_pagination

# Create namespace for countries endpoints
countries_ns = Namespace("countries", description="Country operations")

# Define models for Swagger documentation and validation

# Request model for creating countries (no timestamps - server-side only)
country_create_model = countries_ns.model(
    "CountryCreate",
    {
        "country_name": fields.String(
            required=True, description="Country name", example="United States"
        ),
        "country_code": fields.String(
            required=True,
            description="ISO 3166-1 alpha-2 country code",
            example="US"
        ),
        "continent": fields.String(
            required=True,
            description="Continent name",
            enum=VALID_CONTINENTS,
            example="North America",
        ),
        "capital": fields.String(
            required=True,
            description="Capital city",
            example="Washington D.C."
        ),
        "population": fields.Integer(
            description="Population count", example=331000000
        ),
        "area_km2": fields.Float(
            description="Area in square kilometers", example=9833517.0
        ),
    },
)

# Response model for countries (includes read-only timestamps)
country_model = countries_ns.model(
    "Country",
    {
        "country_name": fields.String(
            required=True, description="Country name", example="United States"
        ),
        "country_code": fields.String(
            required=True,
            description="ISO 3166-1 alpha-2 country code",
            example="US"
        ),
        "continent": fields.String(
            required=True,
            description="Continent name",
            enum=VALID_CONTINENTS,
            example="North America",
        ),
        "capital": fields.String(
            required=True,
            description="Capital city",
            example="Washington D.C."
        ),
        "population": fields.Integer(
            description="Population count", example=331000000
        ),
        "area_km2": fields.Float(
            description="Area in square kilometers", example=9833517.0
        ),
        "created_at": fields.DateTime(
            description='Creation timestamp (read-only, set by server)',
            example='2025-11-12T12:00:00Z'
        ),
        "updated_at": fields.DateTime(
            description='Last update timestamp (read-only, set by server)',
            example='2025-11-12T12:00:00Z'
        ),
    },
)

country_update_model = countries_ns.model(
    "CountryUpdate",
    {
        "country_name": fields.String(description="Country name"),
        "continent": fields.String(
            description="Continent name", enum=VALID_CONTINENTS
        ),
        "capital": fields.String(description="Capital city"),
        "population": fields.Integer(description="Population count"),
        "area_km2": fields.Float(
            description="Area in square kilometers"
        ),
    },
)

# HATEOAS link model
link_model = countries_ns.model(
    "Link",
    {
        "rel": fields.String(
            required=True,
            description="Relationship type",
            example="self"
        ),
        "href": fields.String(
            required=True,
            description="URL to the related resource",
            example="/api/countries/US"
        ),
        "method": fields.String(
            description="HTTP method to use",
            example="GET"
        ),
    },
)

# Country model with HATEOAS links
country_hateoas_model = countries_ns.model(
    "CountryWithLinks",
    {
        "country_name": fields.String(
            required=True, description="Country name", example="United States"
        ),
        "country_code": fields.String(
            required=True,
            description="ISO 3166-1 alpha-2 country code",
            example="US"
        ),
        "continent": fields.String(
            required=True,
            description="Continent name",
            enum=VALID_CONTINENTS,
            example="North America",
        ),
        "capital": fields.String(
            required=True,
            description="Capital city",
            example="Washington D.C."
        ),
        "population": fields.Integer(
            description="Population count", example=331000000
        ),
        "area_km2": fields.Float(
            description="Area in square kilometers", example=9833517.0
        ),
        "created_at": fields.DateTime(
            description='Creation timestamp (read-only, set by server)',
            example='2025-11-12T12:00:00Z'
        ),
        "updated_at": fields.DateTime(
            description='Last update timestamp (read-only, set by server)',
            example='2025-11-12T12:00:00Z'
        ),
        "_links": fields.List(
            fields.Nested(link_model),
            description="HATEOAS navigational links to related resources"
        ),
    },
)


def add_country_links(country: dict) -> dict:
    """Add HATEOAS links to a country resource.

    Adds navigational links including:
    - self: Link to this country
    - states: Link to states in this country
    - continent: Link to all countries in same continent
    - update: Link to update this country
    - delete: Link to delete this country
    """
    country_code = country.get('country_code', '')
    continent = country.get('continent', '')

    links = [
        {
            "rel": "self",
            "href": url_for(
                'countries_country',
                country_code=country_code,
                _external=False
            ),
            "method": "GET"
        },
        {
            "rel": "states",
            "href": url_for(
                'countries_states_in_country',
                country_code=country_code,
                _external=False
            ),
            "method": "GET"
        },
        {
            "rel": "continent",
            "href": url_for(
                'countries_countries_by_continent',
                continent_name=continent,
                _external=False
            ),
            "method": "GET"
        },
        {
            "rel": "update",
            "href": url_for(
                'countries_country',
                country_code=country_code,
                _external=False
            ),
            "method": "PUT"
        },
        {
            "rel": "delete",
            "href": url_for(
                'countries_country',
                country_code=country_code,
                _external=False
            ),
            "method": "DELETE"
        },
        {
            "rel": "all_countries",
            "href": url_for('countries_countries_list', _external=False),
            "method": "GET"
        },
    ]

    # Create a copy to avoid mutating the original
    enhanced_country = country.copy()
    enhanced_country['_links'] = links
    return enhanced_country


error_model = countries_ns.model(
    "Error",
    {
        "error": fields.String(description="Error message"),
        "code": fields.Integer(description="HTTP status code"),
    },
)

list_parser = reqparse.RequestParser()
list_parser.add_argument(
    "limit",
    type=int,
    required=False,
    help="Maximum number of countries to return (positive integer)",
    location="args",
)
list_parser.add_argument(
    "offset",
    type=int,
    required=False,
    help="Number of countries to skip from the start (>= 0)",
    location="args",
)


@countries_ns.route("")
class CountriesList(Resource):
    """Countries collection endpoint"""

    @countries_ns.doc("list_countries")
    @countries_ns.expect(list_parser)
    @countries_ns.marshal_list_with(country_model)
    def get(self):
        """
        Retrieve all countries with optional pagination.
        """
        args = list_parser.parse_args()
        limit = args.get("limit")
        offset = args.get("offset")
        validate_pagination(limit, offset, countries_ns.abort)

        try:
            data = countries_data.get_countries()
            data = apply_pagination(data, limit, offset)
            return data, HTTPStatus.OK
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )

    @countries_ns.doc("create_country")
    @countries_ns.expect(country_create_model)
    @countries_ns.marshal_with(country_model, code=HTTPStatus.CREATED)
    @countries_ns.response(
        HTTPStatus.BAD_REQUEST, "Validation error", error_model
    )
    @countries_ns.response(
        HTTPStatus.CONFLICT, "Country already exists", error_model
    )
    def post(self):
        """
        Create a new country
        Creates a new country with the provided data.
        Timestamps are automatically set by the server.
        """
        country_data = request.json

        # Validate continent
        if country_data.get("continent") not in VALID_CONTINENTS:
            countries_ns.abort(
                HTTPStatus.BAD_REQUEST,
                f"Invalid continent. Must be one of: " f"{VALID_CONTINENTS}",
            )

        try:
            success = countries_data.add_country(country_data)
            if success:
                return country_data, HTTPStatus.CREATED
            else:
                countries_ns.abort(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    "Failed to create country"
                )

        except ValueError as e:
            countries_ns.abort(HTTPStatus.BAD_REQUEST, str(e))
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )


@countries_ns.route("/<string:country_code>/states")
@countries_ns.param("country_code", "The country code (ISO 3166-1 alpha-2)")
class StatesInCountry(Resource):
    """States within a country endpoint"""

    @countries_ns.doc("get_states_in_country")
    @countries_ns.marshal_list_with(state_model)
    @countries_ns.response(
        HTTPStatus.NOT_FOUND, "Couldn't find states in country", error_model
    )
    def get(self, country_code):
        """
        Retrieve states in a country
        Returns states in the given country.
        """
        try:
            country = countries_data.get_country_by_code(country_code.upper())
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )
        if country:
            country_code = country_code.upper()
            country_states = states_data.get_states_by_country(country_code)
            return country_states, HTTPStatus.OK
        else:
            countries_ns.abort(
                HTTPStatus.NOT_FOUND,
                f"Country with code '{country_code}' " f"not found",
            )


@countries_ns.route("/<string:country_code>")
@countries_ns.param("country_code", "The country code (ISO 3166-1 alpha-2)")
class Country(Resource):
    """Single country endpoint"""

    @countries_ns.doc("get_country")
    @countries_ns.marshal_with(country_hateoas_model)
    @countries_ns.response(
        HTTPStatus.NOT_FOUND, "Country not found", error_model
    )
    def get(self, country_code):
        """
        Retrieve a specific country with HATEOAS links
        Returns country details with navigational links to related resources.
        Includes links to states, continent, and CRUD operations.
        """
        try:
            country = countries_data.get_country_by_code(country_code.upper())
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )

        if country:
            # Add HATEOAS links to the response
            country_with_links = add_country_links(country)
            return country_with_links, HTTPStatus.OK
        else:
            countries_ns.abort(
                HTTPStatus.NOT_FOUND,
                f"Country with code '{country_code}' " f"not found",
            )

    @countries_ns.doc("update_country")
    @countries_ns.expect(country_update_model)
    @countries_ns.marshal_with(country_model)
    @countries_ns.response(
        HTTPStatus.NOT_FOUND, "Country not found", error_model
    )
    @countries_ns.response(
        HTTPStatus.BAD_REQUEST, "Validation error", error_model
    )
    def put(self, country_code):
        """
        Update a country
        Updates the country with the provided data.
        The updated_at timestamp is automatically set by the server.
        """
        update_data = request.json

        # Validate continent if provided
        if (
            "continent" in update_data
            and update_data["continent"] not in VALID_CONTINENTS
        ):
            countries_ns.abort(
                HTTPStatus.BAD_REQUEST,
                f"Invalid continent. Must be one of: " f"{VALID_CONTINENTS}",
            )

        try:
            success = countries_data.update_country(
                country_code.upper(), update_data
            )
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )

        if success:
            try:
                updated_country = countries_data.get_country_by_code(
                    country_code.upper()
                )
                return updated_country, HTTPStatus.OK
            except Exception as e:
                countries_ns.abort(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    f"Database error: {str(e)}"
                )
        else:
            countries_ns.abort(
                HTTPStatus.NOT_FOUND,
                f"Country with code '{country_code}' " f"not found",
            )

    @countries_ns.doc("delete_country")
    @countries_ns.response(
        HTTPStatus.NO_CONTENT, "Country deleted successfully"
    )
    @countries_ns.response(
        HTTPStatus.NOT_FOUND, "Country not found", error_model
    )
    @countries_ns.response(
        HTTPStatus.CONFLICT,
        "Cannot delete country with dependent states",
        error_model
    )
    def delete(self, country_code):
        """
        Delete a country
        Removes the country from the database if no dependent states exist.
        """
        try:
            success = countries_data.delete_country(country_code.upper())
        except ValueError as e:
            countries_ns.abort(HTTPStatus.CONFLICT, str(e))
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )

        if success:
            return "", HTTPStatus.NO_CONTENT
        else:
            countries_ns.abort(
                HTTPStatus.NOT_FOUND,
                f"Country with code '{country_code}' " f"not found",
            )


@countries_ns.route("/continent/<string:continent_name>")
@countries_ns.param("continent_name", "The continent name")
class CountriesByContinent(Resource):
    """Countries filtered by continent"""

    @countries_ns.doc("get_countries_by_continent")
    @countries_ns.marshal_list_with(country_model)
    @countries_ns.response(
        HTTPStatus.BAD_REQUEST, "Invalid continent", error_model
    )
    def get(self, continent_name):
        """
        Get countries by continent
        Returns all countries in the specified continent.
        """
        # Validate continent
        if continent_name not in VALID_CONTINENTS:
            countries_ns.abort(
                HTTPStatus.BAD_REQUEST,
                f"Invalid continent. Must be one of: " f"{VALID_CONTINENTS}",
            )

        try:
            filtered_countries = countries_data.get_countries_by_continent(
                continent_name
            )
            return filtered_countries, HTTPStatus.OK
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )


# Parser for search query parameters
search_parser = reqparse.RequestParser()
search_parser.add_argument(
    "name",
    type=str,
    required=True,
    help="Country name to search for (partial matching supported)",
    location="args",
)


@countries_ns.route("/search")
class CountriesSearch(Resource):
    """Search countries by name"""

    @countries_ns.doc("search_countries")
    @countries_ns.expect(search_parser)
    @countries_ns.marshal_list_with(country_model)
    @countries_ns.response(
        HTTPStatus.BAD_REQUEST, "Invalid search query", error_model
    )
    def get(self):
        """
        Search countries by name
        Returns countries whose names contain the search query
        (case-insensitive).
        Supports partial matching - e.g., searching for 'united' will
        find 'United States'.
        """
        args = search_parser.parse_args()
        name_query = args.get("name")

        if not name_query or not name_query.strip():
            countries_ns.abort(
                HTTPStatus.BAD_REQUEST,
                "Search query 'name' parameter is required and cannot be "
                "empty",
            )

        try:
            search_results = countries_data.search_countries_by_name(
                name_query
            )
            return search_results, HTTPStatus.OK
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )
