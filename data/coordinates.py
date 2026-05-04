"""
Validated coordinate field types for city data.
"""

from abc import ABC, abstractmethod

LATITUDE = "latitude"
LONGITUDE = "longitude"

MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180


class Coordinate(ABC):
    def __init__(self, value: int | float):
        numeric_value = self._validate_type(value)
        lower_bound, upper_bound = self.bounds()
        if numeric_value < lower_bound or numeric_value > upper_bound:
            raise ValueError(
                f"Bad value for {self.field_name()}: {numeric_value}. "
                f"Expected between {lower_bound} and {upper_bound}"
            )
        self.value = numeric_value

    @classmethod
    @abstractmethod
    def bounds(cls) -> tuple[float, float]:
        """Return the inclusive coordinate bounds."""

    @classmethod
    def field_name(cls) -> str:
        return cls.__name__.lower()

    def _validate_type(self, value: int | float) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Bad type for value: {type(value)}")
        return float(value)

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return str(self.value)


class Latitude(Coordinate):
    @classmethod
    def bounds(cls) -> tuple[float, float]:
        return MIN_LATITUDE, MAX_LATITUDE


class Longitude(Coordinate):
    @classmethod
    def bounds(cls) -> tuple[float, float]:
        return MIN_LONGITUDE, MAX_LONGITUDE


class Coordinates:
    def __init__(
        self,
        latitude: int | float | Latitude,
        longitude: int | float | Longitude,
    ):
        self.latitude = latitude if isinstance(latitude, Latitude) else Latitude(latitude)
        self.longitude = (
            longitude if isinstance(longitude, Longitude) else Longitude(longitude)
        )

    @classmethod
    def from_dict(cls, coordinates: dict) -> "Coordinates":
        if not isinstance(coordinates, dict):
            raise TypeError(f"Bad type for coordinates: {type(coordinates)}")
        if LATITUDE not in coordinates:
            raise ValueError("Missing latitude in coordinates")
        if LONGITUDE not in coordinates:
            raise ValueError("Missing longitude in coordinates")
        return cls(coordinates[LATITUDE], coordinates[LONGITUDE])

    def to_dict(self) -> dict:
        return {
            LATITUDE: float(self.latitude),
            LONGITUDE: float(self.longitude),
        }
