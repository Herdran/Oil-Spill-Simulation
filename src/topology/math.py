from enum import Enum
from math import atan2, cos, sin, degrees, radians, sqrt

from data.measurment_data import Coordinates

import geopy.distance as geo
import pyproj as proj

from initial_values import InitialValues


class Move_direction(Enum):
    North = 0
    East = 90
    South = 180
    West = 270

def coordinates_distance(first: Coordinates, second: Coordinates) -> float:
    return geo.distance(first.as_tuple(), second.as_tuple()).meters

def move_coordinate_bearing(source: Coordinates, distance: float, bearing: float) -> Coordinates:
    point = geo.distance(meters=distance).destination(source.as_tuple(), bearing)
    return Coordinates(latitude=point.latitude, longitude=point.longitude)

def move_coordinate(source: Coordinates, distance: float, direction: Move_direction) -> Coordinates:
    return move_coordinate_bearing(source, distance, direction.value)

def move_coordinate_raw(lat: float, lon: float, distance: float, direction: Move_direction) -> (float, float):
    bearing = direction.value
    point = geo.distance(meters=distance).destination((lat, lon), bearing)
    return (point.latitude, point.longitude)

def get_coordinate_from_xy(top_left: Coordinates, cell_size: int, x: int, y: int) -> Coordinates:
    degree_bearing = (180.0 + degrees(atan2(-x, y))) % 360 if x != 0 or y != 0 else 0
    x_distance = abs(x) * cell_size
    y_distance = abs(y) * cell_size
    full_distance = sqrt((x_distance ** 2) + (y_distance ** 2))
    return move_coordinate_bearing(top_left, full_distance, degree_bearing)

BEARING_OFFSET = 90.0
def get_xy_from_coord_raw(lon: float, lat: float) -> (int, int):
    bearing, distance = calculate_compass_bearing_and_dist(InitialValues.top_left_coord,
                                                            Coordinates(latitude=lat, longitude=lon))
    rad = radians(bearing - BEARING_OFFSET)
    x = int(distance * cos(rad)) // InitialValues.point_side_size
    y = int(distance * sin(rad)) // InitialValues.point_side_size
    return min(x, InitialValues.point_side_lon_count), min(y, InitialValues.point_side_lat_count)

_geodesic = proj.Geod(ellps='WGS84')
def calculate_compass_bearing_and_dist(start: Coordinates, end: Coordinates) -> (float, float):
    forward_azimuth, _, dist = _geodesic.inv(start.longitude, start.latitude, end.longitude, end.latitude)
    bearing = forward_azimuth + 360 if forward_azimuth < 0 else forward_azimuth
    return (bearing, dist)
