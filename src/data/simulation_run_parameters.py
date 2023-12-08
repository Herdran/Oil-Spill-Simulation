from dataclasses import dataclass

import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates, CoordinatesBase


CellSideCount = CoordinatesBase[int]

@dataclass
class SimulationRunParameters:
    area: Range[Coordinates]
    time: Range[pd.Timestamp]
    data_time_step: pd.Timedelta
    cells_side_count: CellSideCount
    path_to_data: str
    
    
