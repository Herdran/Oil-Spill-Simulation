import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import CellSideCount, SimulationRunParameters
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
        time=Range(
            min=pd.Timestamp(time_range_start),
            max=pd.Timestamp(time_range_end),
        ),
        data_time_step=pd.Timedelta(minutes=data_time_step),
        cells_side_count=CellSideCount( 
            latitude=cells_side_count_latitude,
            longitude=cells_side_count_longitude
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
    
    Constants.point_side_count = int(max(height, width) / Constants.point_side_size)

    point_lat_size = (top_coord - down_coord) / Constants.point_side_count
    point_lon_size = (right_coord - left_coord) / Constants.point_side_count

    def get_center(first, direction, point_size, index) -> float:
        center_offset = 0.5 + index
        return move_coordinate(first, point_size * center_offset, direction)

    get_lat_centers = lambda i: get_center(middle_coord_lat(top_coord), Move_direction.South, point_lat_size, i)    
    get_lon_centers = lambda i: get_center(middle_coord_lon(left_coord), Move_direction.East, point_lon_size, i) 

    Constants.point_lat_centers = list(map(get_lat_centers, range(Constants.point_side_count)))
    Constants.point_lon_centers = list(map(get_lon_centers, range(Constants.point_side_count)))

    Constants.simulation_time = (Constants.simulation_initial_parameters.time.max - Constants.simulation_initial_parameters.time.min).total_seconds()