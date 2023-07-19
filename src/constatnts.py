import pandas as pd
from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import CellSideCount, SimulationRunParameters

POINT_SIDE_SIZE = 50  # [m]
CELL_SIDE_SIZE = 10  # points per cell side size
GRID_SIDE_SIZE = 10  # cells per grid side size
WORLD_SIDE_SIZE = CELL_SIDE_SIZE * GRID_SIDE_SIZE
ITER_AS_SEC = 20

TOP_COORD = 30.24268
LEFT_COORD = -88.77964
DOWN_COORD = 30.19767
RIGHT_COORD = -88.72648

CELL_LAT_SIZE = (TOP_COORD - DOWN_COORD)/GRID_SIDE_SIZE
CELL_LON_SIZE = (RIGHT_COORD - LEFT_COORD)/GRID_SIDE_SIZE

##############################################
CELL_LAT = [DOWN_COORD + CELL_LON_SIZE/2 + (CELL_LAT_SIZE * i) for i in range(GRID_SIDE_SIZE)]
CELL_LON = [LEFT_COORD + CELL_LON_SIZE/2 + (CELL_LON_SIZE * i) for i in range(GRID_SIDE_SIZE)]
##############################################

# need to be seted from GUI initial window
SIMULATION_INITIAL_PARAMETERS = SimulationRunParameters(
    area=Range(
        min=Coordinates(
            latitude=DOWN_COORD,
            longitude=LEFT_COORD
        ),
        max=Coordinates(
            latitude=TOP_COORD,
            longitude=RIGHT_COORD
        )
    ),
    # we need to think aboud behavior of our application when sim time ends
    time=Range(
        min=pd.Timestamp("2010-04-01 00:00:00"),
        max=pd.Timestamp("2010-04-01 06:00:00"),
    ),
    data_time_step=pd.Timedelta(minutes=30),
    # how many point we want is how good the interpolation will be
    # but I guess we don't need many of them as that is the only initial iterpolation
    # and making that initial interpolation is costly at app start
    # -----
    # and that cells count is not the same as cells count in simulation!
    cells_side_count=CellSideCount(
        latitude=10,
        longitude=10
    ),
    path_to_data="data/processed_data"
)