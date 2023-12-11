import pandas as pd

from data.generic import Range
from data.measurment_data import Coordinates
from data.simulation_run_parameters import CellSideCount, SimulationRunParameters
from files import get_data_path
from simulation.utilities import Neighbourhood


class InitialValues:
    point_side_size: int = 50
    point_side_count: int = 1000  # TODO to be calculated
    iter_as_sec: int = 20

    point_lat_size: float = None
    point_lon_size: float = None

    point_lat_centers: list[float] = None
    point_lon_centers: list[float] = None

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
        cells_side_count=CellSideCount(
            latitude=10,
            longitude=10
        ),
        path_to_data=get_data_path()
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
    neighbourhood = None


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
                                          point_side_size: int,
                                          iter_as_sec: int,
                                          min_oil_thickness: float,
                                          oil_viscosity: float,
                                          oil_density: float,
                                          neighbourhood: Neighbourhood
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

    InitialValues.point_side_size = point_side_size

    InitialValues.point_lat_size = (top_coord - down_coord) / InitialValues.point_side_count
    InitialValues.point_lon_size = (right_coord - left_coord) / InitialValues.point_side_count

    InitialValues.point_lat_centers = [top_coord - InitialValues.point_lat_size / 2 - (InitialValues.point_lat_size * i) for i in
                                       range(InitialValues.point_side_count)]
    InitialValues.point_lon_centers = [left_coord + InitialValues.point_lon_size / 2 + (InitialValues.point_lon_size * i) for i in
                                       range(InitialValues.point_side_count)]

    InitialValues.simulation_time = (InitialValues.simulation_initial_parameters.time.max - InitialValues.simulation_initial_parameters.time.min).total_seconds()
    InitialValues.iter_as_sec = iter_as_sec

    InitialValues.viscosity_kinematic = oil_viscosity
    InitialValues.oil_density = oil_density
    InitialValues.neighbourhood = neighbourhood
    InitialValues.min_oil_thickness = min_oil_thickness
