from dataclasses import dataclass

import pandas as pd

from data.generic import Range
from data.measurement_data import Coordinates, CoordinatesBase

Interpolation_grid_size = CoordinatesBase[int]


@dataclass
class SimulationRunParameters:
    area: Range[Coordinates]
    time: Range[pd.Timestamp]
    data_time_step: pd.Timedelta
    interpolation_grid_size: Interpolation_grid_size
