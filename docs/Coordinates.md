# Design Project Assignment : Small Component:

The data layer now includes a small `data.coordinates` component for validating city coordinates before writes reach MongoDB.

## What was added

### `feat: create small component for data.coordinates`

`data/coordinates.py` provides:

- `Coordinate` — abstract base class for validated numeric coordinate values
- `Latitude` — validates values in the range `-90..90`
- `Longitude` — validates values in the range `-180..180`
- `Coordinates` — wrapper for paired latitude/longitude values with:
  - `from_dict()`
  - `to_dict()`

Example:

```python
from data.coordinates import Coordinates

coords = Coordinates.from_dict({
    "latitude": 39.78,
    "longitude": -89.64,
})

payload = coords.to_dict()
```

## Where it is used

`data/cities.py` now validates coordinate payloads in:

- `add_city()`
- `update_city()`
- `update_city_by_name_and_country()`

The stored data shape is unchanged:

```python
{
    "coordinates": {
        "latitude": 39.78,
        "longitude": -89.64,
    }
}
```

## Validation behavior

The component rejects:

- non-dict coordinate payloads
- missing `latitude`
- missing `longitude`
- non-numeric values
- boolean values
- latitude outside `-90..90`
- longitude outside `-180..180`

## Tests

### `test: add testing to coordinates component`

Coverage was added in:

- `data/tests/test_coordinates.py`
- `data/tests/test_cities.py`

Run the relevant tests with:

```bash
python -m pytest data/tests/test_coordinates.py data/tests/test_cities.py -q
```
