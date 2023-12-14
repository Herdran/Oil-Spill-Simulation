from logging import getLogger
from math import ceil

import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import Interpolation_grid_size, SimulationRunParameters
from data.utilities import coordinates_distance
from simulation.utilities import Neighbourhood

logger = getLogger("constants")


class InitialValues:
    SEA_COLOR = (15, 10, 222)
    LAND_COLOR = (38, 166, 91)
    OIL_COLOR = (0, 0, 0)
    LAND_WITH_OIL_COLOR = (0, 100, 0)

    BINARY_MAP_WIDTH = 86400
    BINARY_MAP_HEIGHT = 43200

    PREVIEW_MAP_SCALE = 6

    point_side_size: int = 50
    iter_as_sec: int = 20

    point_side_lat_count: int = None
    point_side_lon_count: int = None

    top_left_coord: Coordinates = None
    bottom_right_coord: Coordinates = None

    simulation_initial_parameters: SimulationRunParameters = SimulationRunParameters(
        area=Range(
            min=Coordinates(
                latitude=30.19767,
                longitude=-88.77964
            ),
            max=Coordinates(
                latitude=30.24268,
                longitude=-88.72648
            )
        ),
        time=Range(
            min=pd.Timestamp("2010-04-01 00:00:00"),
            max=pd.Timestamp("2010-04-02 00:00:00"),
        ),
        data_time_step=pd.Timedelta(minutes=30),
        interpolation_grid_size=Interpolation_grid_size(
            latitude=10,
            longitude=10
        ),
        path_to_data="data/processed_data"
    )

    simulation_time: float = None

    min_oil_thickness = 5e-5

    water_density = 997  # [kg/m^3]
    oil_density = 846  # [kg/m^3]
    emulsion_max_content_water = 0.7  # max content of water in the emulsion
    molar_mass = 348.23  # [g/mol] mean
    boiling_point = 609  # [K] mean
    interfacial_tension = 30  # [dyna/cm]
    propagation_factor = 2.5
    c = 10  # parameter dependant of oil type, used in viscosity change
    viscosity_kinematic = 5.3e-6  # [m^2/s]
    viscosity_dynamic = viscosity_kinematic * oil_density
    emulsification_rate = 0
    neighbourhood: Neighbourhood = None
    checkpoint_frequency: int = 0
    total_simulation_time: int = 0
    curr_iter: int = 0


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
