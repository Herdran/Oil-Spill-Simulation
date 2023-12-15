from data.generic import Range
from data.measurement_data import Coordinates
from data.simulation_run_parameters import Interpolation_grid_size, SimulationRunParameters
from simulation.utilities import Neighbourhood

import pandas as pd


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
    
    top_left_binary_offset = None
    bottom_right_binary_offset = None

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
