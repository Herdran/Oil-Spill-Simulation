from enum import Enum
from math import atan2, degrees, sqrt
from typing import Callable, Optional

from data.measurment_data import CoordinatesBase, Coordinates, Temperature

import pandas as pd
import numpy as np
import geopy.distance as geo
import pyproj as proj

    
def minutes(time_delta: pd.Timedelta) -> float:
    SECONDS_IN_MINUTE = 60
    return time_delta.total_seconds() / SECONDS_IN_MINUTE

def dataframe_replace_applay(dataframe: pd.DataFrame, result_columns: list[str], function: Callable, columns: list[str]):
    def is_any_nan(row: pd.Series) -> bool:
        return any([pd.isna(row[column]) for column in columns])

    def apply_function(row: pd.Series) -> object:
        return pd.NA if is_any_nan(row) else function(*[row[column] for column in columns])


    result = dataframe.apply(
        lambda row: apply_function(row),
        axis=1
    )
    
    SINGLE_RESULT_COLUMNS_COUNT = 1
    if len(result_columns) == SINGLE_RESULT_COLUMNS_COUNT:
        dataframe[result_columns[0]] = result
    else:
        for i in range(len(result_columns)):
            dataframe[result_columns[i]] = result.apply(lambda x: x[i] if not pd.isna(x) else pd.NA)

    dataframe.drop(
        columns=columns,
        inplace=True
    )

def or_default(value: Optional[object], default: object) -> object:
    if value is None:
        return default
    return value

KELVIN_CONSTATNT = 273.15

def celcius_to_kelvins(celcius: float) -> Temperature:
    return celcius + KELVIN_CONSTATNT

def kelvins_to_celsius(kelvins: Temperature) -> float:
    return kelvins - KELVIN_CONSTATNT

def round_values(arr: np.array):
    DATA_FLOAT_PRECISSION = 5
    return np.round(arr, DATA_FLOAT_PRECISSION)
  
LONGITUDE_OFFSET = 180.0
LATITUDE_OFFSET = 90.0
LONGITUDE_RANGE = 360.0
LATITUDE_RANGE = 180.0
    
def project_coordinates(coordinates: Coordinates, width: int, height: int) -> CoordinatesBase[int]:
    lon = (coordinates.longitude + LONGITUDE_OFFSET) * (width / LONGITUDE_RANGE)
    lat = (-coordinates.latitude + LATITUDE_OFFSET) * (height / LATITUDE_RANGE)
    return CoordinatesBase[int](int(lat), int(lon))

def project_coordinates_raw(lat: float, lon: float, width: int, height: int) -> (int, int):
    x = (lon + LONGITUDE_OFFSET) * (width / LONGITUDE_RANGE)
    y = (-lat + LATITUDE_OFFSET) * (height / LATITUDE_RANGE)
    return (int(x), int(y))

def project_to_coordinates_raw(x: int, y: int, width: int, height: int) -> (float, float):
    lon = x / (width / LONGITUDE_RANGE) - LONGITUDE_OFFSET
    lat = -(y / (height / LATITUDE_RANGE) - LATITUDE_OFFSET)
    return (lon, lat)

def project_to_coordinates(x: int, y: int, width: int, height: int) -> Coordinates:
    lon, lat = project_to_coordinates_raw(x, y, width, height)
    return Coordinates(latitude=lat, longitude=lon)

def coordinates_distance(first: Coordinates, second: Coordinates) -> float:
    return geo.distance(first.as_tuple(), second.as_tuple()).meters

class Move_direction(Enum):
    North = 0
    East = 90
    South = 180
    West = 270

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

geodesic = proj.Geod(ellps='WGS84')
def calculate_compass_bearing_and_dist(start: Coordinates, end: Coordinates) -> (float, float):
    forward_azimuth, _, dist = geodesic.inv(start.longitude, start.latitude, end.longitude, end.latitude)
    bearing = forward_azimuth + 360 if forward_azimuth < 0 else forward_azimuth
    return (bearing, dist)
