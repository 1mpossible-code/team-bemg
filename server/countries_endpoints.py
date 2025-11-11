"""
Geographic API endpoints for countries.
Provides full CRUD operations with Swagger documentation.
"""

from flask import request
from flask_restx import Resource, fields, Namespace, reqparse
from http import HTTPStatus
import data.countries as countries_data
import data.states as states_data
from data.countries import VALID_CONTINENTS

# Create namespace for countries endpoints
countries_ns = Namespace("countries", description="Country operations")

# Define models for Swagger documentation and validation
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

error_model = countries_ns.model(
    "Error",
    {
        "error": fields.String(description="Error message"),
        "code": fields.Integer(description="HTTP status code"),
    },
)


@countries_ns.route("")
class CountriesList(Resource):
    """Countries collection endpoint"""

    @countries_ns.doc("list_countries")
    @countries_ns.marshal_list_with(country_model)
    def get(self):
        """
        Retrieve all countries
        Returns a list of all countries in the database.
        """
        try:
            return countries_data.get_countries(), HTTPStatus.OK
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )

    @countries_ns.doc("create_country")
    @countries_ns.expect(country_model)
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


@countries_ns.route("/<string:country_code>")
@countries_ns.param("country_code", "The country code (ISO 3166-1 alpha-2)")
class Country(Resource):
    """Single country endpoint"""

    @countries_ns.doc("get_country")
    @countries_ns.marshal_with(country_model)
    @countries_ns.response(
        HTTPStatus.NOT_FOUND, "Country not found", error_model
    )
    def get(self, country_code):
        """
        Retrieve a specific country
        Returns country details for the given country code.
        """
        try:
            country = countries_data.get_country_by_code(country_code.upper())
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )

        if country:
            return country, HTTPStatus.OK
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

    @countries_ns.doc("get_states_in_country")
    @countries_ns.marshal_with(country_model)
    @countries_ns.response(
        HTTPStatus.NOT_FOUND, "Couldn't find states in country", error_model
    )
    def get_states_in_country(self, country_code):
        """
        Retrieve a specific country
        Returns states in the given country.
        """
        try:
            country = countries_data.get_country_by_code(country_code.upper())
        except Exception as e:
            countries_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}"
            )
        if country:
            return states_data.get_states_by_country(country_code.upper()), HTTPStatus.OK
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
