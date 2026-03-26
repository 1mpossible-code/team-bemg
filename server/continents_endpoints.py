"""
Geographic API endpoints for continents.
Provides full CRUD operations with Swagger documentation.
"""

from flask import request
from flask_restx import Resource, fields, Namespace, reqparse
from http import HTTPStatus

import data.continents as continents_data
from data.countries import VALID_CONTINENTS
from server.helpers import apply_pagination, validate_pagination

continents_ns = Namespace("continents", description="Continent operations")

continent_create_model = continents_ns.model(
    "ContinentCreate",
    {
        "continent_name": fields.String(
            required=True,
            description="Continent name",
            enum=VALID_CONTINENTS,
            example="Asia",
        ),
    },
)

continent_model = continents_ns.model(
    "Continent",
    {
        "continent_name": fields.String(
            required=True,
            description="Continent name",
            enum=VALID_CONTINENTS,
            example="Asia",
        ),
        "created_at": fields.DateTime(
            description="Creation timestamp (read-only, set by server)",
            example="2025-11-12T12:00:00Z",
        ),
        "updated_at": fields.DateTime(
            description="Last update timestamp (read-only, set by server)",
            example="2025-11-12T12:00:00Z",
        ),
    },
)

error_model = continents_ns.model(
    "ContinentError",
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
    help="Maximum number of continents to return (positive integer)",
    location="args",
)
list_parser.add_argument(
    "offset",
    type=int,
    required=False,
    help="Number of continents to skip from the start (>= 0)",
    location="args",
)


@continents_ns.route("")
class ContinentsList(Resource):
    """Continents collection endpoint"""

    @continents_ns.doc("list_continents")
    @continents_ns.expect(list_parser)
    @continents_ns.marshal_list_with(continent_model)
    def get(self):
        """Retrieve all continents with optional pagination."""
        args = list_parser.parse_args()
        limit = args.get("limit")
        offset = args.get("offset")

        validate_pagination(limit, offset, continents_ns.abort)

        try:
            data = continents_data.get_continents()
            data = apply_pagination(data, limit, offset)
            return data, HTTPStatus.OK
        except Exception as e:
            continents_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}")

    @continents_ns.doc("create_continent")
    @continents_ns.expect(continent_create_model)
    @continents_ns.marshal_with(continent_model, code=HTTPStatus.CREATED)
    @continents_ns.response(HTTPStatus.BAD_REQUEST, "Validation error", error_model)
    @continents_ns.response(HTTPStatus.CONFLICT, "Continent already exists", error_model)
    def post(self):
        """Create a new continent."""
        continent_data = request.json

        if continent_data.get("continent_name") not in VALID_CONTINENTS:
            continents_ns.abort(
                HTTPStatus.BAD_REQUEST,
                f"Invalid continent. Must be one of: {VALID_CONTINENTS}",
            )

        try:
            success = continents_data.add_continent(continent_data)
            if success:
                return continent_data, HTTPStatus.CREATED
            continents_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to create continent")
        except ValueError as e:
            continents_ns.abort(HTTPStatus.CONFLICT, str(e))
        except Exception as e:
            continents_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}")


@continents_ns.route("/<string:continent_name>")
@continents_ns.param("continent_name", "The continent name")
class Continent(Resource):
    """Single continent endpoint"""

    @continents_ns.doc("get_continent")
    @continents_ns.marshal_with(continent_model)
    @continents_ns.response(HTTPStatus.NOT_FOUND, "Continent not found", error_model)
    def get(self, continent_name):
        """Retrieve a specific continent."""
        try:
            continent = continents_data.get_continent_by_name(continent_name)
        except Exception as e:
            continents_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}")

        if continent:
            return continent, HTTPStatus.OK
        continents_ns.abort(HTTPStatus.NOT_FOUND, f"Continent '{continent_name}' not found")

    @continents_ns.doc("update_continent")
    @continents_ns.response(HTTPStatus.NO_CONTENT, "Continent updated successfully")
    @continents_ns.response(HTTPStatus.NOT_FOUND, "Continent not found", error_model)
    def put(self, continent_name):
        """
        Update a continent (touch updated_at).
        continent_name is the identifier and cannot be changed.
        """
        try:
            success = continents_data.update_continent(continent_name, {})
        except Exception as e:
            continents_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}")

        if success:
            return "", HTTPStatus.NO_CONTENT
        continents_ns.abort(HTTPStatus.NOT_FOUND, f"Continent '{continent_name}' not found")

    @continents_ns.doc("delete_continent")
    @continents_ns.response(HTTPStatus.NO_CONTENT, "Continent deleted successfully")
    @continents_ns.response(HTTPStatus.NOT_FOUND, "Continent not found", error_model)
    @continents_ns.response(HTTPStatus.CONFLICT, "Cannot delete: countries reference this continent", error_model)
    def delete(self, continent_name):
        """
        Delete a continent.
        Fails if any countries are assigned to this continent.
        """
        try:
            success = continents_data.delete_continent(continent_name)
        except ValueError as e:
            continents_ns.abort(HTTPStatus.CONFLICT, str(e))
        except Exception as e:
            continents_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Database error: {str(e)}")

        if success:
            return "", HTTPStatus.NO_CONTENT
        continents_ns.abort(HTTPStatus.NOT_FOUND, f"Continent '{continent_name}' not found")
