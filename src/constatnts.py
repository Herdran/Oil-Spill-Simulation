import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import CellSideCount, SimulationRunParameters


class Constants:
    POINT_SIDE_SIZE = 50  # [m] #TODO: right now that could be different from what we have from coordinates :v - need to be calculated
    POINTS_SIDE_COUNT = 500
    ITER_AS_SEC = 20

    POINT_LAT_SIZE = None
    POINT_LON_SIZE = None

    POINT_LAT_CENTERS = None
    POINT_LON_CENTERS = None

    SIMULATION_INITIAL_PARAMETERS = None
    SIMULATION_TIME = None


def set_simulation_coordinates_parameters(TOP_COORD, DOWN_COORD, LEFT_COORD, RIGHT_COORD, DATA_PATH):
    global POINT_LAT_SIZE, POINT_LON_SIZE, POINT_LAT_CENTERS, POINT_LON_CENTERS, SIMULATION_INITIAL_PARAMETERS

    Constants.SIMULATION_INITIAL_PARAMETERS = SimulationRunParameters(
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
        # we need to think about behavior of our application when sim time ends
        time=Range(
            min=pd.Timestamp("2010-04-01 00:00:00"),
            max=pd.Timestamp("2010-04-02 00:00:00"),
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
        path_to_data=DATA_PATH
    )
    Constants.POINT_LAT_SIZE = (TOP_COORD - DOWN_COORD) / Constants.POINTS_SIDE_COUNT
    Constants.POINT_LON_SIZE = (RIGHT_COORD - LEFT_COORD) / Constants.POINTS_SIDE_COUNT

    Constants.POINT_LAT_CENTERS = [TOP_COORD - Constants.POINT_LAT_SIZE / 2 - (Constants.POINT_LAT_SIZE * i) for i in
                                   range(Constants.POINTS_SIDE_COUNT)]
    Constants.POINT_LON_CENTERS = [LEFT_COORD + Constants.POINT_LON_SIZE / 2 + (Constants.POINT_LON_SIZE * i) for i in
                                   range(Constants.POINTS_SIDE_COUNT)]

    Constants.SIMULATION_TIME = (SIMULATION_INITIAL_PARAMETERS.time.max - SIMULATION_INITIAL_PARAMETERS.time.min).total_seconds()