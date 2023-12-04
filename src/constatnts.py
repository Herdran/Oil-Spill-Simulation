import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import CellSideCount, SimulationRunParameters


class Constants:
    point_side_size: int = None
    point_side_count: int = 1000  # TODO to be calculated
    iter_as_sec: int = 20

    point_lat_size: float = None
    point_lon_size: float = None

    point_lat_centers: list[float] = None
    point_lon_centers: list[float] = None

    simulation_initial_parameters: SimulationRunParameters = None
    simulation_time: float = None


def set_simulation_coordinates_parameters(top_coord: float,
                                          down_coord: float,
                                          left_coord: float,
                                          right_coord: float,
                                          time_range_start: str,
                                          time_range_end: str,
                                          data_time_step: int,
                                          cells_side_count_latitude: int,
                                          cells_side_count_longitude: int,
                                          data_path: str,
                                          point_side_size: int
                                          ):

    Constants.simulation_initial_parameters = SimulationRunParameters(
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

    Constants.point_side_size = point_side_size

    Constants.point_lat_size = (top_coord - down_coord) / Constants.point_side_count
    Constants.point_lon_size = (right_coord - left_coord) / Constants.point_side_count

    Constants.point_lat_centers = [top_coord - Constants.point_lat_size / 2 - (Constants.point_lat_size * i) for i in
                                   range(Constants.point_side_count)]
    Constants.point_lon_centers = [left_coord + Constants.point_lon_size / 2 + (Constants.point_lon_size * i) for i in
                                   range(Constants.point_side_count)]

    Constants.simulation_time = (Constants.simulation_initial_parameters.time.max - Constants.simulation_initial_parameters.time.min).total_seconds()