from enum import Enum
from typing import Tuple

import numpy as np
import pandas as pd
from numpy import exp, log, sqrt

from data.measurement_data import Coordinates
from initial_values import InitialValues
from simulation.utilities import get_neighbour_coordinates, Neighbourhood, sign
from topology.math import get_coordinate_from_xy_cached

DEFAULT_WAVE_VELOCITY = np.array([0.0, 0.0])  # [m/s]
DEFAULT_WIND_VELOCITY = np.array([0.0, 0.0])  # [m/s]
DEFAULT_TEMPERATURE = 302.15  # [K]

Coord_t = Tuple[int, int]


class TopographyState(Enum):
    LAND = 0
    SEA = 1


def is_coord_in_simulation_area(coord: Coord_t) -> bool:
    return 0 <= coord[0] < InitialValues.point_side_lon_count and 0 <= coord[1] < InitialValues.point_side_lat_count





class Point:
    world = dict()

    def __init__(self, coord: Coord_t, engine):
        self._topography = engine.get_topography(coord)
        self._engine = engine
        self._coord = coord  # world coordinates
        self.weather_station_coordinates = engine.data_processor.weather_station_coordinates(get_coordinate_from_xy_cached(coord))
        self._wind_velocity = DEFAULT_WIND_VELOCITY
        self._wave_velocity = DEFAULT_WAVE_VELOCITY
        self._temperature = DEFAULT_TEMPERATURE
        self._last_weather_update_time = None
        self._oil_mass = 0  # [kg]
        self._emulsification_rate = InitialValues.emulsification_rate
        self._data_processor = engine.data_processor
        self._viscosity_dynamic = InitialValues.viscosity_dynamic  # [Pa*s]
        self.oil_buffer = []  # contains tuples (mass, viscosity, emulsification_rate)
        self._evaporation_rate = 0

    def contain_oil(self) -> bool:
        return self.slick_thickness() / 100 > InitialValues.min_oil_thickness

    def add_oil(self, mass: float) -> None:
        # maybe initial emulsification rate will be changed
        self._emulsification_rate = (self._oil_mass * self._emulsification_rate +
                                     mass * InitialValues.emulsification_rate) / (self._oil_mass + mass)
        self._viscosity_dynamic = (
                (self._oil_mass * self._viscosity_dynamic + mass * InitialValues.viscosity_dynamic) / (
                self._oil_mass + mass))
        self._oil_mass += mass

    def _should_update_weather_data(self, time_delta: pd.Timedelta) -> bool:
        return (self._last_weather_update_time is None
                or self._data_processor.should_update_data(time_delta - self._last_weather_update_time))

    def _update_weather_data(self) -> None:
        time_delta = pd.Timedelta(seconds=int(self._engine.total_time))
        if not self._should_update_weather_data(time_delta):
            return
        time_stamp = InitialValues.simulation_initial_parameters.time.min + time_delta
        measurement = self._data_processor.get_measurement(get_coordinate_from_xy_cached(self.coord), self.weather_station_coordinates,
                                                           time_stamp)
        self._wave_velocity = measurement.current.to_numpy()
        self._wind_velocity = measurement.wind.to_numpy()
        self._temperature = measurement.temperature
        self._last_weather_update_time = time_delta

    def update(self) -> None:
        self._update_weather_data()
        if self._topography == TopographyState.LAND:
            self._process_seashore_interaction()
            return
        delta_y = self._process_emulsification()
        delta_f = self._process_evaporation()
        self._process_natural_dispersion()
        self._viscosity_change(delta_f, delta_y)

        # that needs to be done as the last step
        self._process_advection()

    def _process_emulsification(self) -> float:
        K = 5.0e-7
        old_emulsification_rate = self._emulsification_rate
        self._emulsification_rate += InitialValues.iter_as_sec * K * (
                ((np.linalg.norm(self._wind_velocity) + 1) ** 2) * (
                1 - self._emulsification_rate / InitialValues.emulsion_max_content_water))
        if self._emulsification_rate > InitialValues.emulsion_max_content_water:
            self._emulsification_rate = InitialValues.emulsion_max_content_water
        return self._emulsification_rate - old_emulsification_rate

    def _process_evaporation(self) -> float:
        K = 1.25e-3
        P = 1000 * exp(-(4.4 + log(InitialValues.boiling_point)) * (
                1.803 * (InitialValues.boiling_point / self._temperature - 1) - 0.803 * log(
            InitialValues.boiling_point / self._temperature)))  # [Pa]
        R = 8.314  # [J/(mol*K)]

        self._evaporation_rate = (K * (InitialValues.molar_mass / 1000) * P) / (R * self._temperature)
        delta_mass = -1 * min(
            InitialValues.iter_as_sec * InitialValues.point_side_size * InitialValues.point_side_size * self._evaporation_rate,
            self._oil_mass)
        delta_f = -delta_mass / self._oil_mass
        self._oil_mass += delta_mass
        return delta_f

    def _process_seashore_interaction(self) -> None:
        half_time = 3600 * 24  # 24h for sand beach / sand and gravel beach
        delta_mass = log(2) * self._oil_mass * InitialValues.iter_as_sec / half_time
        self._oil_mass -= delta_mass
        to_share = []
        (x, y) = self._coord

        neighbours = get_neighbour_coordinates(x, y, InitialValues.neighbourhood)
        for cords in neighbours:
            if not is_coord_in_simulation_area(cords):
                continue
            if self._engine.get_topography(cords) == TopographyState.LAND:
                continue
            if cords not in self.world:
                self.world[cords] = Point(cords, self._engine)
            to_share.append(self.world[cords])
        if len(to_share) == 0:  # in case of bug
            return
        delta_mass /= len(to_share)
        for neighbor in to_share:
            neighbor.oil_mass += delta_mass

    def _advection_land_collision(self, advection_vector: Tuple[float, float]) -> Tuple[int, int, Tuple[float, float]]:
        x, y = self._coord
        next_x = x + int(advection_vector[0])
        next_y = y + int(advection_vector[1])
        for i in range(1, int(max(map(abs, advection_vector)))):
            advection_x, advection_y = advection_vector
            if abs(advection_x) > abs(advection_y):
                crossing_point = (x + i * sign(advection_x), y + round(i * advection_y / abs(advection_x)))
            else:
                crossing_point = (round(x + i * advection_x / abs(advection_y)), y + i * sign(advection_y))
            if self._engine.get_topography(crossing_point) == TopographyState.LAND:
                next_x, next_y = map(int, crossing_point)
                advection_vector = (0, 0)  # so it's not going through land in the next step
                break
        return next_x, next_y, advection_vector

    def _process_advection(self) -> None:
        ALPHA = 1.1
        BETA = 0.03

        delta_r = (ALPHA * self._wave_velocity + BETA * self._wind_velocity) * InitialValues.iter_as_sec
        delta_r /= InitialValues.point_side_size
        advection_vector = (delta_r[1], -delta_r[0])

        # check if there is a land between current and next point
        next_x, next_y, advection_vector = self._advection_land_collision(advection_vector)

        fractional_part_x = (abs(advection_vector[0]) % 1) * sign(advection_vector[0])
        fractional_part_y = (abs(advection_vector[1]) % 1) * sign(advection_vector[1])
        x_shift = sign(fractional_part_x)
        y_shift = sign(fractional_part_y)
        neighbours = [(next_x, next_y + y_shift), (next_x + x_shift, next_y), (next_x + x_shift, next_y + y_shift)]
        areas = [abs(fractional_part_y) * (1 - abs(fractional_part_x)),
                 abs(fractional_part_x) * (1 - abs(fractional_part_y)),
                 abs(fractional_part_x * fractional_part_y)]
        if InitialValues.neighbourhood == Neighbourhood.VON_NEUMANN:
            neighbours.pop()
            area_to_split = areas.pop()
            if sum(areas) > 0:
                areas[0] += area_to_split * areas[0] / sum(areas)
                areas[1] += area_to_split * areas[1] / sum(areas)
        oil_mass = self._oil_mass
        for neighbour, area in zip(neighbours, areas):
            self.move_oil_to_other(neighbour, oil_mass * area)

        if (next_x, next_y) != self._coord:
            self.move_oil_to_other((next_x, next_y), self._oil_mass)

    def _process_natural_dispersion(self) -> None:
        Da = 0.11 * (np.linalg.norm(self._wind_velocity) + 1) ** 2
        interfacial_tension = InitialValues.interfacial_tension * (1 + self._evaporation_rate)
        # multiply viscosity by 100 to convert from Pa*s to cPa*s
        Db = 1 / (1 + 50 * sqrt(self._viscosity_dynamic * 100) * self.slick_thickness() * interfacial_tension)
        self._oil_mass -= self._oil_mass * Da * Db / (3600 * InitialValues.iter_as_sec)

    def slick_thickness(self) -> float:
        thickness = (self._oil_mass / InitialValues.oil_density) / (InitialValues.point_side_size ** 2)  # [m]
        return thickness * 100  # [cm]

    def _viscosity_change(self, delta_F: float, delta_Y: float) -> None:
        delta_viscosity = InitialValues.c * self._viscosity_dynamic * delta_F + (
                2.5 * self._viscosity_dynamic * delta_Y) / (
                                  (1 - InitialValues.emulsion_max_content_water * self._emulsification_rate) ** 2)
        self._viscosity_dynamic += delta_viscosity
        if self._oil_mass < 1:
            self._viscosity_dynamic = InitialValues.viscosity_dynamic

    def pour_from_buffer(self):
        oil_mass = sum([tup[0] for tup in self.oil_buffer]) + self._oil_mass
        if oil_mass < 1:
            return
        self._viscosity_dynamic = (sum([tup[0] * tup[1] for tup in
                                        self.oil_buffer]) + self._oil_mass * self._viscosity_dynamic) / oil_mass
        self._emulsification_rate = (sum([tup[0] * tup[2] for tup in
                                          self.oil_buffer]) + self._oil_mass * self._emulsification_rate) / oil_mass
        self.oil_buffer = []
        self._oil_mass = oil_mass

    def move_oil_to_other(self, coord: Coord_t, mass: float) -> None:
        self._oil_mass -= mass
        if not is_coord_in_simulation_area(coord):
            return
        if coord not in self.world:
            self.world[coord] = Point(coord, self._engine)
        self.world[coord].oil_buffer.append((mass, self._viscosity_dynamic, self._emulsification_rate))

    @property
    def oil_mass(self) -> float:
        return self._oil_mass

    @oil_mass.setter
    def oil_mass(self, value: float) -> None:
        if value < 0:
            self._oil_mass = 0
            return
        self._oil_mass = value

    @property
    def viscosity_dynamic(self) -> float:
        return self._viscosity_dynamic

    @viscosity_dynamic.setter
    def viscosity_dynamic(self, value: float) -> None:
        if not 0 < value < 10:
            raise ValueError("Viscosity value is strange")
        self._viscosity_dynamic = value

    @property
    def coord(self) -> Coord_t:
        return self._coord

    @property
    def emulsification_rate(self) -> float:
        return self._emulsification_rate

    @emulsification_rate.setter
    def emulsification_rate(self, value: float) -> None:
        if not 0 <= value <= 1:
            raise ValueError("Emulsification rate should be between 0 and 1")
        self._emulsification_rate = value

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def wave_velocity(self) -> np.ndarray:
        return self._wave_velocity

    @property
    def wind_velocity(self) -> np.ndarray:
        return self._wind_velocity

    @property
    def evaporation_rate(self) -> float:
        return self._evaporation_rate

    @evaporation_rate.setter
    def evaporation_rate(self, value: float) -> None:
        if not 0 <= value <= 1:
            raise ValueError("Evaporation rate should be between 0 and 1")
        self._evaporation_rate = value

    @property
    def topography(self) -> TopographyState:
        return self._topography
