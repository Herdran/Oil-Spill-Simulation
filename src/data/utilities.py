from math import acos, cos, radians, sin
from typing import Callable, Optional
from data.measurment_data import Coordinates, Temperature
import pandas as pd
import numpy as np

from data.measurment_data import Coordinates
    
def minutes(time_delta: pd.Timedelta) -> float:
    SECONDS_IN_MINUTE = 60
    return time_delta.total_seconds() / SECONDS_IN_MINUTE

def great_circle_distance(first: Coordinates, second: Coordinates) -> float:
    lon1, lat1, lon2, lat2 = map(
        radians, [first.longitude, first.latitude, second.longitude, second.latitude])

    RADIUS = 6371
    return RADIUS * (
        acos(sin(lat1) * sin(lat2) + cos(lat1)
             * cos(lat2) * cos(lon1 - lon2))
    )
    
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
    
    
