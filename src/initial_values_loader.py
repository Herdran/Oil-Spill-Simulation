from logging import getLogger
from math import ceil

import pandas as pd

from data.generic import Range
from data.measurement_data import Coordinates
from data.simulation_run_parameters import Interpolation_grid_size, SimulationRunParameters
from initial_values import InitialValues
from simulation.utilities import Neighbourhood
from topology.binary_map_math import project_binary_map_coordinates
from topology.math import MoveDirection, get_coordinate_from_xy, get_xy_dist_from_coord, move_coordinate

logger = getLogger("initial_values")


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
                                          point_side_size: int,
                                          iter_as_sec: int,
                                          min_oil_thickness: float,
                                          oil_viscosity: float,
                                          oil_density: float,
                                          neighbourhood: Neighbourhood,
                                          checkpoint_frequency: int,
                                          total_simulation_time: int,
                                          curr_iter: int,
                                          minimal_oil_to_show: int
                                          ):
    InitialValues.simulation_initial_parameters = SimulationRunParameters(
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
        interpolation_grid_size=Interpolation_grid_size(
            latitude=interpolation_grid_size_latitude,
            longitude=interpolation_grid_size_longitude
        )
    )

    InitialValues.data_dir_path = data_path

    InitialValues.point_side_size = point_side_size

    top_left = Coordinates(latitude=top_coord, longitude=left_coord)
    bottom_right = Coordinates(latitude=down_coord, longitude=right_coord)
    
    InitialValues.top_left_coord = top_left
    
    width, height = get_xy_dist_from_coord(top_left, bottom_right)

    get_points_count = lambda size: int(ceil(size / InitialValues.point_side_size))

    InitialValues.point_side_lat_count = get_points_count(height)
    InitialValues.point_side_lon_count = get_points_count(width)

    logger.debug(f"Points count: {InitialValues.point_side_lat_count} x {InitialValues.point_side_lon_count}")
    
    top_right = get_coordinate_from_xy(InitialValues.point_side_lon_count, 0)
    bottom_left = get_coordinate_from_xy(0, InitialValues.point_side_lat_count)
    bottom_right = get_coordinate_from_xy(InitialValues.point_side_lon_count, InitialValues.point_side_lat_count)
   
    max_lat = max(top_left.latitude, top_right.latitude)
    min_lat = min(bottom_right.latitude, bottom_left.latitude)
    max_lon = max(bottom_right.longitude, top_right.longitude)
    min_lon = min(top_left.longitude, bottom_left.longitude)

    if top_coord > 0.0 and down_coord < 0.0:
        equator_coord = Coordinates(latitude=0.0, longitude=0.0)
        _, height = get_xy_dist_from_coord(top_left, equator_coord)
        equator_left = move_coordinate(top_left, height, MoveDirection.South)
        equator_right = move_coordinate(bottom_right, height, MoveDirection.North)
        max_lon = max(max_lon, equator_left.longitude, equator_right.longitude)
        min_lon = min(min_lon, equator_left.longitude, equator_right.longitude)

    InitialValues.max_lon = max_lon
    InitialValues.min_lon = min_lon
    InitialValues.max_lat = max_lat
    InitialValues.min_lat = min_lat
    
    InitialValues.top_left_binary_offset = project_binary_map_coordinates(InitialValues.top_left_coord)

    InitialValues.simulation_time = (
            InitialValues.simulation_initial_parameters.time.max - InitialValues.simulation_initial_parameters.time.min).total_seconds()
    InitialValues.iter_as_sec = iter_as_sec

    logger.debug(f"Simulation time: {InitialValues.simulation_time}s")

    InitialValues.viscosity_kinematic = oil_viscosity
    InitialValues.oil_density = oil_density
    InitialValues.neighbourhood = neighbourhood
    InitialValues.min_oil_thickness = min_oil_thickness
    InitialValues.checkpoint_frequency = checkpoint_frequency
    InitialValues.total_simulation_time = total_simulation_time
    InitialValues.curr_iter = curr_iter
    InitialValues.minimal_oil_to_show = minimal_oil_to_show
