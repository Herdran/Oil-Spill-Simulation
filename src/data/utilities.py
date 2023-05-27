from math import acos, cos, radians, sin
from typing import Callable
from measurment_data import Coordinates
import pandas as pd


def great_circle_distance(first: Coordinates, second: Coordinates) -> float:
    lon1, lat1, lon2, lat2 = map(
        radians, [first.longitude, first.latitude, second.longitude, second.latitude])

    RADIUS = 6371
    return RADIUS * (
        acos(sin(lat1) * sin(lat2) + cos(lat1)
             * cos(lat2) * cos(lon1 - lon2))
    )


def dataframe_replace_applay(dataframe: pd.DataFrame, result_column: str, function: Callable, columns: list[str]):
    def is_any_nan(row: pd.Series) -> bool:
        return any([pd.isna(row[column]) for column in columns])

    def apply_function(row: pd.Series) -> object:
        if (is_any_nan(row)):
            return pd.NA
        return function(*[row[column] for column in columns])

    dataframe[result_column] = dataframe.apply(
        lambda row: apply_function(row),
        axis=1
    )

    dataframe.drop(
        columns=columns,
        inplace=True
    )