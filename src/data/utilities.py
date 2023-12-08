from enum import Enum
from math import acos, cos, radians, sin
from typing import Callable, Optional

from data.measurment_data import CoordinatesBase, Coordinates, Temperature

import pandas as pd
import numpy as np
import geopy.distance as geo

    
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
    
def project_coordinates(coordinates: Coordinates, width: int, height: int) -> CoordinatesBase[int]:
    LONGITUDE_OFFSET = 180.0
    LATITUDE_OFFSET = 90.0
    LONGITUDE_RANGE = 360.0
    LATITUDE_RANGE = 180.0

    lon = (coordinates.longitude + LONGITUDE_OFFSET) * (width / LONGITUDE_RANGE)
    lat = (-coordinates.latitude + LATITUDE_OFFSET) * (height / LATITUDE_RANGE)
    
    return CoordinatesBase[int](int(lat), int(lon))

def coordinates_distance(first: Coordinates, second: Coordinates) -> float:
    return geo.distance(first.as_tuple(), second.as_tuple()).meters

class Move_direction(Enum):
    North = 0
    East = 90
    South = 180
    West = 270

def move_coordinate(source: Coordinates, distance: float, direcion: Move_direction) -> Coordinates:
    bearing = direcion.value
    point = geo.distance(meters=distance).destination(source.as_tuple(), bearing)
    return Coordinates(latitude=point.latitude, longitude=point.longitude)