from data.measurement_data import Coordinates, CoordinatesBase
from initial_values import InitialValues


LONGITUDE_OFFSET = 180.0
LATITUDE_OFFSET = 90.0
LONGITUDE_RANGE = 360.0
LATITUDE_RANGE = 180.0

def _project_longitude_to_x(lon: float, width: int) -> int:
    return int((lon + LONGITUDE_OFFSET) * (width / LONGITUDE_RANGE))

def _project_latitude_to_y(lat: float, height: int) -> int:
    return int((-lat + LATITUDE_OFFSET) * (height / LATITUDE_RANGE))    

def _project_coordinates(lat: float, lon: float, width: int, height: int) -> (int, int):
    x = _project_longitude_to_x(lon, width)
    y = _project_latitude_to_y(-lat, height)
    return (x, y)

def _project_to_coordinates_raw(x: int, y: int, width: int, height: int) -> (float, float):
    lon = x / (width / LONGITUDE_RANGE) - LONGITUDE_OFFSET
    lat = -(y / (height / LATITUDE_RANGE) - LATITUDE_OFFSET)
    return (lon, lat)

def _project_to_coordinates(x: int, y: int, width: int, height: int) -> Coordinates:
    lon, lat = _project_to_coordinates_raw(x, y, width, height)
    return Coordinates(latitude=lat, longitude=lon)

def project_binary_map_coordinates(coord: Coordinates) -> CoordinatesBase[int]:
    x, y = _project_coordinates(coord.latitude, coord.longitude, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)
    return CoordinatesBase(latitude=y, longitude=x)

def project_binary_map_coordinates_raw(lat: float, lon: float) -> (float, float):
    return _project_coordinates(lat, lon, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)

def project_binary_map_xy_to_coordinates(x: int, y: int) -> Coordinates:
    return _project_to_coordinates(x, y, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)

def project_binary_map_xy_to_coordinates_raw(x: int, y: int) -> (float, float):
    return _project_to_coordinates_raw(x, y, InitialValues.BINARY_MAP_WIDTH, InitialValues.BINARY_MAP_HEIGHT)

def project_longitude_to_x(lon: float) -> int:
    return _project_longitude_to_x(lon, InitialValues.BINARY_MAP_WIDTH)

def project_latitude_to_y(lat: float) -> int:
    return _project_latitude_to_y(lat, InitialValues.BINARY_MAP_HEIGHT)