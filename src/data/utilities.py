from typing import Callable, Optional

import numpy as np
import pandas as pd

from data.measurement_data import Temperature


def minutes(time_delta: pd.Timedelta) -> float:
    SECONDS_IN_MINUTE = 60
    return time_delta.total_seconds() / SECONDS_IN_MINUTE


def dataframe_replace_apply(dataframe: pd.DataFrame, result_columns: list[str], function: Callable, columns: list[str]):
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


KELVIN_CONSTANT = 273.15


def celcius_to_kelvins(celcius: float) -> Temperature:
    return celcius + KELVIN_CONSTANT


def kelvins_to_celsius(kelvins: Temperature) -> float:
    return kelvins - KELVIN_CONSTANT


def round_values(arr: np.array):
    DATA_FLOAT_PRECISION = 5
    return np.round(arr, DATA_FLOAT_PRECISION)
