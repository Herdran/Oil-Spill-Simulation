import pandas as pd

from data.generic import Range
from data.measurement_data import Coordinates
from data.simulation_run_parameters import Interpolation_grid_size, SimulationRunParameters
from simulation.utilities import Neighbourhood
from files import get_main_path


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
    top_left_binary_offset = None

    min_lon = None
    max_lon = None
    min_lat = None
    max_lat = None

    simulation_initial_parameters: SimulationRunParameters = SimulationRunParameters(
        area=Range(
            min=Coordinates(
                latitude=26.36,
                longitude=-91.31
            ),
            max=Coordinates(
                latitude=30.6,
                longitude=-85.23
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
        )
    )

    simulation_time: float = None
    
    data_preprocessor_initial_timestamp: pd.Timestamp = None

    min_oil_thickness = 5e-6  # [m]

    data_dir_path = get_main_path().joinpath("data/test_data")

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
    neighbourhood: Neighbourhood = None
    checkpoint_frequency: int = 0
    total_simulation_time: int = 0
    curr_iter: int = 0
