from logging import getLogger
from math import ceil

import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import Interpolation_grid_size , SimulationRunParameters
from data.utilities import Move_direction, coordinates_distance, move_coordinate


logger = getLogger("constants")


class Constants:
    point_side_size: int = None
    iter_as_sec: int = 20

    point_lat_centers: list[float] = None
    point_lon_centers: list[float] = None

    top_left_coord: Coordinates = None
    bottom_right_coord: Coordinates = None

    simulation_initial_parameters: SimulationRunParameters = None
    simulation_time: float = None


def set_simulation_coordinates_parameters(top_coord: float,
                                          down_coord: float,
                                          left_coord: float,
                                          right_coord: float,
                                          time_range_start: str,
                                          time_range_end: str,
                                          data_time_step: int,
                                          interpolation_grid_size_latitude: int,
                                          interpolation_grid_size_longitude: int,
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
        time=Range(
            min=pd.Timestamp(time_range_start),
            max=pd.Timestamp(time_range_end),
        ),
        data_time_step=pd.Timedelta(minutes=data_time_step),
        interpolation_grid_size=Interpolation_grid_size ( 
            latitude=interpolation_grid_size_latitude,
            longitude=interpolation_grid_size_longitude
        ),
        path_to_data=data_path
    )

    Constants.point_side_size = point_side_size

    middle_lat = (top_coord + down_coord) / 2
    middle_lon = (left_coord + right_coord) / 2
    middle_coord_lat = lambda lat: Coordinates(latitude=lat, longitude=middle_lon)
    middle_coord_lon = lambda lon: Coordinates(latitude=middle_lat, longitude=lon)
    height = coordinates_distance(middle_coord_lat(top_coord), middle_coord_lat(down_coord))
    width = coordinates_distance(middle_coord_lon(left_coord), middle_coord_lon(right_coord))
    
    get_points_count = lambda size: int(ceil(size / Constants.point_side_size))
    
    Constants.point_side_lat_count = get_points_count(height)
    Constants.point_side_lon_count = get_points_count(width)
    
    logger.debug(f"Points count: {Constants.point_side_lat_count} x {Constants.point_side_lon_count}")
    
    Constants.top_left_coord = Coordinates(latitude=top_coord, longitude=left_coord)
    Constants.bottom_right_coord = Coordinates(latitude=down_coord, longitude=right_coord)

    Constants.simulation_time = (Constants.simulation_initial_parameters.time.max - Constants.simulation_initial_parameters.time.min).total_seconds()
    
    logger.debug(f"Simulation time: {Constants.simulation_time}s")
 