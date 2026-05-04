"""
Tests for the coordinate validation types.
"""

import pytest

from data.coordinates import Coordinate, Coordinates, Latitude, Longitude


class TestCoordinates:
    def test_coordinate_base_is_abstract(self):
        with pytest.raises(TypeError):
            Coordinate(10)

    def test_construct_latitude(self):
        latitude = Latitude(39.78)
        assert isinstance(latitude, Latitude)

    def test_construct_longitude(self):
        longitude = Longitude(-89.64)
        assert isinstance(longitude, Longitude)

    def test_construct_latitude_bad_type(self):
        with pytest.raises(TypeError):
            Latitude("39.78")

    def test_construct_longitude_bad_type(self):
        with pytest.raises(TypeError):
            Longitude("-89.64")

    def test_construct_latitude_too_small(self):
        with pytest.raises(ValueError, match="latitude"):
            Latitude(-91)

    def test_construct_latitude_too_large(self):
        with pytest.raises(ValueError, match="latitude"):
            Latitude(91)

    def test_construct_longitude_too_small(self):
        with pytest.raises(ValueError, match="longitude"):
            Longitude(-181)

    def test_construct_longitude_too_large(self):
        with pytest.raises(ValueError, match="longitude"):
            Longitude(181)

    def test_coordinate_string_conversion(self):
        assert str(Latitude(39.78)) == "39.78"

    def test_coordinate_float_conversion(self):
        assert float(Longitude(-89.64)) == -89.64

    def test_coordinates_from_dict(self):
        coordinates = Coordinates.from_dict(
            {"latitude": 39.78, "longitude": -89.64}
        )
        assert coordinates.to_dict() == {"latitude": 39.78, "longitude": -89.64}

    def test_coordinates_bad_container_type(self):
        with pytest.raises(TypeError):
            Coordinates.from_dict("39.78,-89.64")

    def test_coordinates_missing_latitude(self):
        with pytest.raises(ValueError, match="Missing latitude"):
            Coordinates.from_dict({"longitude": -89.64})

    def test_coordinates_missing_longitude(self):
        with pytest.raises(ValueError, match="Missing longitude"):
            Coordinates.from_dict({"latitude": 39.78})
