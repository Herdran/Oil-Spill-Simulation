from logging import getLogger
from math import ceil

from initial_values import InitialValues
from simulation.utilities import Neighbourhood
from data.generic import Range
from data.measurement_data import Coordinates
from data.simulation_run_parameters import Interpolation_grid_size, SimulationRunParameters
from topology.binary_map_math import project_binary_map_coordinates
from topology.math import coordinates_distance

import pandas as pd


logger = getLogger("constants")


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
                                          curr_iter: int
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
        ),
        path_to_data=data_path
    )

    InitialValues.point_side_size = point_side_size

    middle_lat = (top_coord + down_coord) / 2
    middle_lon = (left_coord + right_coord) / 2
    middle_coord_lat = lambda lat: Coordinates(latitude=lat, longitude=middle_lon)
    middle_coord_lon = lambda lon: Coordinates(latitude=middle_lat, longitude=lon)
    height = coordinates_distance(middle_coord_lat(top_coord), middle_coord_lat(down_coord))
    width = coordinates_distance(middle_coord_lon(left_coord), middle_coord_lon(right_coord))

    get_points_count = lambda size: int(ceil(size / InitialValues.point_side_size))

    InitialValues.point_side_lat_count = get_points_count(height)
    InitialValues.point_side_lon_count = get_points_count(width)

    logger.debug(f"Points count: {InitialValues.point_side_lat_count} x {InitialValues.point_side_lon_count}")

    InitialValues.top_left_coord = Coordinates(latitude=top_coord, longitude=left_coord)
    InitialValues.bottom_right_coord = Coordinates(latitude=down_coord, longitude=right_coord)
    InitialValues.top_left_binary_offset = project_binary_map_coordinates(InitialValues.top_left_coord)
    InitialValues.bottom_right_binary_offset = project_binary_map_coordinates(InitialValues.bottom_right_coord)

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