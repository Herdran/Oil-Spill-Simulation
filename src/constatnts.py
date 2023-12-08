import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import Interpolation_grid_size , SimulationRunParameters
from data.utilities import Move_direction, coordinates_distance, move_coordinate


class Constants:
    point_side_size: int = None
    point_side_count: int = None
    iter_as_sec: int = 20

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
    
    print(height, width)
    
    
    Constants.point_side_count = int(max(height, width) / Constants.point_side_size)

    def get_center(first, direction, index) -> float:
        center_offset = 0.5 + index
        return move_coordinate(first, Constants.point_side_size * center_offset, direction)

    get_lat_centers = lambda i: get_center(middle_coord_lat(top_coord), Move_direction.South, i).latitude 
    get_lon_centers = lambda i: get_center(middle_coord_lon(left_coord), Move_direction.East, i).longitude

    print(Constants.point_side_count)

    Constants.point_lat_centers = list(map(get_lat_centers, range(Constants.point_side_count)))
    Constants.point_lon_centers = list(map(get_lon_centers, range(Constants.point_side_count)))

    Constants.simulation_time = (Constants.simulation_initial_parameters.time.max - Constants.simulation_initial_parameters.time.min).total_seconds()
    
    print(move_coordinate(middle_coord_lat(top_coord), height, Move_direction.South).latitude)
    print(down_coord, Constants.point_lat_centers[-1], move_coordinate(middle_coord_lat(down_coord), point_side_size / 2, Move_direction.North).latitude)

    
    # assert(down_coord <= Constants.point_lat_centers[-1])
    # assert(right_coord <= Constants.point_lon_centers[-1])
    
    
    