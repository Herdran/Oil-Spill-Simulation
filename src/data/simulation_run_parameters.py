from dataclasses import dataclass
from generic import Range
from measurment_data import Coordinates, CoordinatesBase
import pandas as pd

CellSideCount = CoordinatesBase[int]

@dataclass
class SimulationRunParameters:
    area: Range[Coordinates]
    time: Range[pd.Timestamp]
    data_time_step: pd.Timedelta
    cells_side_count: CellSideCount
    
    
