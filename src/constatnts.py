import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import CellSideCount, SimulationRunParameters


class Constants:
    POINT_SIDE_SIZE = None
    POINTS_SIDE_COUNT = 500  # TODO to be calculated
    ITER_AS_SEC = 20

    POINT_LAT_SIZE = None
    POINT_LON_SIZE = None

    POINT_LAT_CENTERS = None
    POINT_LON_CENTERS = None

    SIMULATION_INITIAL_PARAMETERS = None
    SIMULATION_TIME = None


def set_simulation_coordinates_parameters(top_coord,
                                          down_coord,
                                          left_coord,
                                          right_coord,
                                          time_range_start,
                                          time_range_end,
                                          data_time_step,
                                          cells_side_count_latitude,
                                          cells_side_count_longitude,
                                          data_path,
                                          point_side_size
                                          ):

    Constants.SIMULATION_INITIAL_PARAMETERS = SimulationRunParameters(
        area=Range(
            min=Coordinates(
                latitude=down_coord,
                longitude=left_coord
            ),
            max=Coordinates(
                latitude=top_coord,
                longitude=right_coord
            )
        ),
        # we need to think about behavior of our application when sim time ends
        time=Range(
            min=pd.Timestamp(time_range_start),
            max=pd.Timestamp(time_range_end),
        ),
        data_time_step=pd.Timedelta(minutes=data_time_step),
        # how many point we want is how good the interpolation will be
        # but I guess we don't need many of them as that is the only initial interpolation
        # and making that initial interpolation is costly at app start
        # -----
        # and that cells count is not the same as cells count in simulation!
        cells_side_count=CellSideCount(
            latitude=cells_side_count_latitude,
            longitude=cells_side_count_longitude
        ),
        path_to_data=data_path
    )

    Constants.POINT_SIDE_SIZE = point_side_size

    Constants.POINT_LAT_SIZE = (top_coord - down_coord) / Constants.POINTS_SIDE_COUNT
    Constants.POINT_LON_SIZE = (right_coord - left_coord) / Constants.POINTS_SIDE_COUNT

    Constants.POINT_LAT_CENTERS = [top_coord - Constants.POINT_LAT_SIZE / 2 - (Constants.POINT_LAT_SIZE * i) for i in
                                   range(Constants.POINTS_SIDE_COUNT)]
    Constants.POINT_LON_CENTERS = [left_coord + Constants.POINT_LON_SIZE / 2 + (Constants.POINT_LON_SIZE * i) for i in
                                   range(Constants.POINTS_SIDE_COUNT)]

    Constants.SIMULATION_TIME = (Constants.SIMULATION_INITIAL_PARAMETERS.time.max - Constants.SIMULATION_INITIAL_PARAMETERS.time.min).total_seconds()